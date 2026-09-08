"""
TDD tests for v11 migration correctness.

Tests are written FIRST to define the correct contract:
  1. folder_path is used as category (NOT the LLM classification label)
  2. primary_tenant is used for tenant assignment (NOT tenant/tenant_name which are None)
  3. Batch PDF is optional at migration time — migration succeeds without a raw scan PDF,
     and when no raw scan exists the batch record is created but no garbage placeholder is written.

Run against a CLEAN migration of House 500 only:
  python src/main.py migrate "/Volumes/arshad-pc/areas_20260908_v11test/Safra D/500 - فواز خليل الطارش"

Then run:
  pytest tests/test_migration_v11_tdd.py -v
"""
import sqlite3
import json
from pathlib import Path
import pytest

# ── Paths ──────────────────────────────────────────────────────────────────────
SOURCE_STATE_JSON = Path(
    "/Volumes/arshad-pc/Areas/Safra D/500 - فواز خليل الطارش/.source_files/500_state.json"
)
TEST_AREA_DIR = Path("/Volumes/arshad-pc/areas_20260908_v11test/Safra D")
# The folder rename may fail on SMB volumes; check both the renamed and original name.
_renamed = TEST_AREA_DIR / "500"
_original = TEST_AREA_DIR / "500 - فواز خليل الطارش"
MIGRATED_HOUSE_DIR = _renamed if _renamed.exists() else _original
_db_root = TEST_AREA_DIR.parent / "organizer.db"
_db_local = TEST_AREA_DIR / "organizer.db"
DB_PATH = _db_root if _db_root.exists() else _db_local


# ── Fixtures ───────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def state():
    """Load House 500 state.json from the ORIGINAL (unmigrated) source."""
    assert SOURCE_STATE_JSON.exists(), (
        f"Source state.json not found at {SOURCE_STATE_JSON}\n"
        "Ensure the original /Volumes/arshad-pc/Areas/ drive is mounted."
    )
    with SOURCE_STATE_JSON.open() as f:
        return json.load(f)


@pytest.fixture(scope="module")
def conn():
    """Open a read-only connection to the migrated DB."""
    assert DB_PATH.exists(), (
        f"Migrated DB not found at {DB_PATH}\n"
        "Run: python src/main.py migrate '<house_dir>' first."
    )
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    yield c
    c.close()


# ── Helper ─────────────────────────────────────────────────────────────────────
def get_routed_docs_from_state(state):
    return state.get("routed_documents") or []


# ══════════════════════════════════════════════════════════════════════════════
# BUG 1: Category must come from folder_path, NOT from 'category' field
# ══════════════════════════════════════════════════════════════════════════════

class TestCategoryMapping:
    """
    In routed_documents:
      - 'category' = LLM classification label  (e.g. "letters", "10-صيانة", "others")
      - 'folder_path' = routed Arabic folder name (e.g. "صيانة", "عقود", "بيانات أساسية")

    The documents.category column in the DB MUST store folder_path values,
    NOT the LLM classification labels.
    """

    def test_folder_path_values_exist_in_source(self, state):
        """Sanity: source data has folder_path fields that differ from category."""
        docs = get_routed_docs_from_state(state)
        assert len(docs) > 0, "routed_documents must not be empty"

        has_diff = any(
            d.get("folder_path") != d.get("category")
            for d in docs
            if d.get("folder_path") and d.get("category")
        )
        assert has_diff, (
            "Expected folder_path to differ from category in at least one document, "
            "but they are always the same — check source data."
        )

    def test_no_english_lm_labels_in_db_categories(self, conn):
        """DB documents.category must not contain raw LLM classification strings."""
        english_lm_labels = {"letters", "forms", "id_cards", "contract", "others",
                              "utilities", "maintenance", "notices", "allocation"}
        rows = conn.execute(
            "SELECT DISTINCT category FROM documents WHERE house_id = '500'"
        ).fetchall()
        db_categories = {row["category"] for row in rows if row["category"]}

        bad = db_categories & english_lm_labels
        assert not bad, (
            f"DB documents.category still contains LLM classification labels: {bad}\n"
            "Fix: extract category from routed_documents['folder_path'] not ['category']."
        )

    def test_db_categories_match_source_folder_paths(self, state, conn):
        """Every DB category for house 500 must be a folder_path value from state.json."""
        docs = get_routed_docs_from_state(state)
        expected_folders = {d["folder_path"] for d in docs if d.get("folder_path")}

        rows = conn.execute(
            "SELECT DISTINCT category FROM documents WHERE house_id = '500'"
        ).fetchall()
        db_categories = {row["category"] for row in rows if row["category"]}

        unexpected = db_categories - expected_folders
        assert not unexpected, (
            f"DB categories not found in source folder_paths: {unexpected}\n"
            f"Source folder_paths: {expected_folders}"
        )

    def test_specific_known_folder_paths_present_in_db(self, conn):
        """Known Arabic folder names must appear in DB for house 500."""
        expected = {"صيانة", "عقود", "بيانات أساسية", "بيانات شخصية"}
        rows = conn.execute(
            "SELECT DISTINCT category FROM documents WHERE house_id = '500'"
        ).fetchall()
        db_categories = {row["category"] for row in rows if row["category"]}

        missing = expected - db_categories
        assert not missing, (
            f"Expected folder names missing from DB categories: {missing}\n"
            f"Got: {db_categories}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG 2: Tenant assignment must use primary_tenant, NOT tenant/tenant_name
# ══════════════════════════════════════════════════════════════════════════════

class TestTenantAssignment:
    """
    In routed_documents each document has a 'primary_tenant' field.
    The migration must use primary_tenant to resolve tenant_id.
    Using 'tenant' or 'tenant_name' (both None in House 500) assigns all
    documents to the default_tenant (the first one), causing Bug 2.
    """

    def test_all_three_tenants_have_documents_in_db(self, conn):
        """All 3 historical tenants of house 500 must have at least 1 document."""
        rows = conn.execute("""
            SELECT t.name, COUNT(d.vault_id) as doc_count
            FROM tenants t
            LEFT JOIN documents d ON d.tenant_id = t.id
            WHERE t.house_id = '500'
            GROUP BY t.id, t.name
        """).fetchall()

        assert rows, "No tenants found for house 500"
        tenant_doc_counts = {row["name"]: row["doc_count"] for row in rows}

        for tenant_name, count in tenant_doc_counts.items():
            assert count > 0, (
                f"Tenant '{tenant_name}' has 0 documents — expected > 0.\n"
                "Fix: use routed_documents['primary_tenant'] for tenant resolution."
            )

    def test_fawaz_has_approximately_29_documents(self, conn):
        """فواز خليل الطارش has 29 docs in source — must be close in DB."""
        row = conn.execute("""
            SELECT COUNT(d.vault_id) as doc_count
            FROM tenants t
            JOIN documents d ON d.tenant_id = t.id
            WHERE t.house_id = '500' AND t.name = 'فواز خليل الطارش'
        """).fetchone()
        assert row is not None, "Tenant فواز خليل الطارش not found"
        assert row["doc_count"] >= 25, (
            f"Expected ~29 docs for فواز, got {row['doc_count']}.\n"
            "Some tolerance allowed but not 0."
        )

    def test_abdulla_has_approximately_30_documents(self, conn):
        """عبد الله حميدة رضا فرج has 30 docs in source — must be close in DB."""
        row = conn.execute("""
            SELECT COUNT(d.vault_id) as doc_count
            FROM tenants t
            JOIN documents d ON d.tenant_id = t.id
            WHERE t.house_id = '500' AND t.name = 'عبد الله حميدة رضا فرج'
        """).fetchone()
        assert row is not None, "Tenant عبد الله حميدة رضا فرج not found"
        assert row["doc_count"] >= 25, (
            f"Expected ~30 docs for عبد الله, got {row['doc_count']}."
        )

    def test_adel_has_approximately_6_documents(self, conn):
        """عادل عبد الرحيم جاسم has 6 docs in source — must be close in DB."""
        row = conn.execute("""
            SELECT COUNT(d.vault_id) as doc_count
            FROM tenants t
            JOIN documents d ON d.tenant_id = t.id
            WHERE t.house_id = '500' AND t.name = 'عادل عبد الرحيم جاسم'
        """).fetchone()
        assert row is not None, "Tenant عادل عبد الرحيم جاسم not found"
        assert row["doc_count"] >= 4, (
            f"Expected ~6 docs for عادل, got {row['doc_count']}."
        )

    def test_not_all_documents_assigned_to_one_tenant(self, conn):
        """Documents must NOT all be assigned to the same tenant (default fallback bug)."""
        rows = conn.execute("""
            SELECT t.name, COUNT(d.vault_id) as doc_count
            FROM tenants t
            JOIN documents d ON d.tenant_id = t.id
            WHERE t.house_id = '500'
            GROUP BY t.id
        """).fetchall()

        counts = [row["doc_count"] for row in rows]
        total = sum(counts)
        assert total > 0, "No documents in DB for house 500"

        max_share = max(counts) / total
        assert max_share < 0.80, (
            f"One tenant holds {max_share:.0%} of all documents — likely a default fallback bug.\n"
            f"Distribution: {[(r['name'], r['doc_count']) for r in rows]}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG 3: No raw scan PDF needed — batch record is DB-only, no garbage placeholder
# ══════════════════════════════════════════════════════════════════════════════

class TestBatchHandling:
    """
    Migration does NOT require a raw scan PDF to exist.
    If no raw scan is found, the batch DB record is still created (for tracking),
    but NO blank/garbage placeholder PDF should be written to disk.
    The vault PDFs are the source of truth; a merged batch PDF is a UX feature,
    not a migration requirement.
    """

    def test_batch_record_exists_in_db(self, conn):
        """Batch DB record must exist for house 500 even without a raw scan PDF."""
        row = conn.execute(
            "SELECT * FROM batches WHERE house_id = '500'"
        ).fetchone()
        assert row is not None, "No batch record found for house 500 in DB"
        assert row["page_count"] > 0, "Batch page_count must be > 0"

    def test_batch_record_has_correct_page_count(self, conn):
        """Batch page count should equal number of pages from state.json (~131)."""
        row = conn.execute(
            "SELECT page_count FROM batches WHERE house_id = '500'"
        ).fetchone()
        assert row is not None
        # 131 pages in raw_dump.json, tolerate small variance
        assert row["page_count"] >= 60, (
            f"Batch page_count is {row['page_count']}, expected >= 60 based on source data."
        )

    def test_no_blank_placeholder_pdf_in_batches(self):
        """If a batch PDF exists on disk, it must NOT be a blank/tiny placeholder.
        A blank fitz-generated placeholder is typically < 30KB even for 100+ pages.
        If it exists it should be a proper merged PDF (> 1MB for 65+ real docs).
        If it doesn't exist yet, that's fine — batch PDF is optional.
        """
        batches_dir = MIGRATED_HOUSE_DIR / "batches"
        if not batches_dir.exists():
            pytest.skip("Batches directory not created yet — batch PDF is optional")

        pdf_files = list(batches_dir.glob("*.pdf"))
        if not pdf_files:
            # No batch PDF on disk is acceptable
            return

        for pdf in pdf_files:
            size_kb = pdf.stat().st_size / 1024
            assert size_kb > 100, (
                f"Batch PDF '{pdf.name}' is only {size_kb:.1f}KB — looks like a blank "
                f"placeholder generated by fitz. Migration must NOT create blank placeholders.\n"
                "Either merge the vault PDFs or leave the batch PDF absent."
            )

    def test_vault_pdfs_are_real(self):
        """Vault PDFs must exist and be non-trivial (> 5KB each)."""
        vault_dir = MIGRATED_HOUSE_DIR / "vault"
        assert vault_dir.exists(), f"Vault directory missing: {vault_dir}"

        pdfs = list(vault_dir.glob("doc_*.pdf"))
        assert len(pdfs) >= 60, (
            f"Expected >= 60 vault PDFs, found {len(pdfs)}"
        )

        tiny = [p for p in pdfs if p.stat().st_size < 5 * 1024]
        assert not tiny, (
            f"{len(tiny)} vault PDFs are suspiciously tiny (< 5KB): "
            f"{[p.name for p in tiny[:5]]}"
        )

    def test_total_doc_count_matches_source(self, state, conn):
        """DB documents count must match routed_documents count in source."""
        source_count = len(get_routed_docs_from_state(state))
        db_count = conn.execute(
            "SELECT COUNT(*) as c FROM documents WHERE house_id = '500'"
        ).fetchone()["c"]
        assert db_count == source_count, (
            f"DB has {db_count} documents but source has {source_count} routed_documents."
        )

    def test_tree_view_tenant_ordering_latest_first(self, conn):
        """Tenants for house 500 in tree view must be ordered latest tenant first."""
        from src.db.repository import Repository
        from src.api.server import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        app.state.repo = Repository(conn)
        app.state.db_path = str(DB_PATH)
        res = client.get("/api/tree")
        assert res.status_code == 200
        tree = res.json()
        safra = next((a for a in tree if "Safra" in a["name"]), None)
        assert safra is not None
        h500 = next((h for h in safra["children"] if "500" in h["id"]), None)
        assert h500 is not None
        tenant_names = [t["name"] for t in h500["children"]]
        assert tenant_names == [
            "فواز خليل الطارش",
            "عبد الله حميدة رضا فرج",
            "عادل عبد الرحيم جاسم"
        ], f"Expected latest tenant first, got {tenant_names}"
