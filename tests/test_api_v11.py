import pytest
import time
from pathlib import Path
from fastapi.testclient import TestClient
from src.api.server import app
from src.db.connection import get_db_connection
from src.db.schema import init_db
from src.db.repository import Repository
from src.core.config import AppConfig

client = TestClient(app)

@pytest.fixture
def db_setup(tmp_path):
    db_file = tmp_path / "organizer.db"
    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)
    
    # 1. Areas
    repo.add_area(area_id="Safra C", code="SAF C")
    repo.add_area(area_id="Riffa A", code="RIF A")
    
    # 2. Houses
    # House 101: short tenure (<5y)
    h101 = repo.add_house(house_id="101 - ShortStay", area_id="Safra C")
    # House 102: medium tenure (5-10y)
    h102 = repo.add_house(house_id="102 - MedStay", area_id="Safra C")
    # House 103: long tenure (>10y)
    h103 = repo.add_house(house_id="103 - LongStay", area_id="Safra C")
    # House in Riffa A
    repo.add_house(house_id="201 - RiffaHouse", area_id="Riffa A")
    
    # 3. Tenants
    # Tenant 1 on H101 (active, started 2024 -> <5y)
    t1 = repo.add_tenant(house_id="101 - ShortStay", name="Ali Short", start_date="2024-01-01", end_date=None)
    # Past tenant on H101
    t1_past = repo.add_tenant(house_id="101 - ShortStay", name="Old Ali", start_date="2020-01-01", end_date="2023-12-31")
    
    # Tenant 2 on H102 (active, started 2019 -> 5-10y)
    t2 = repo.add_tenant(house_id="102 - MedStay", name="Hassan Medium", start_date="2019-03-01", end_date=None)
    
    # Tenant 3 on H103 (active, started 2012 -> >10y)
    t3 = repo.add_tenant(house_id="103 - LongStay", name="Khalid Long", start_date="2012-05-15", end_date=None)
    
    # 4. Batches
    b1 = repo.create_batch(house_id="101 - ShortStay", filename="batch_01.pdf", file_path=str(tmp_path / "batch_01.pdf"), page_count=2)
    b2 = repo.create_batch(house_id="102 - MedStay", filename="batch_02.pdf", file_path=str(tmp_path / "batch_02.pdf"), page_count=1)
    
    # 5. Documents
    # H101 docs
    doc1 = repo.add_document(
        vault_id="v101_1",
        house_id="101 - ShortStay",
        tenant_id=t1.id,
        batch_id=b1.id,
        primary_date="2024-02-01",
        arabic_title="عقد إيجار جديد",
        category="05 - عقود",
        page_count=1
    )
    doc2 = repo.add_document(
        vault_id="v101_2",
        house_id="101 - ShortStay",
        tenant_id=t1.id,
        batch_id=b1.id,
        primary_date="2024-06-15",
        arabic_title="إيصال كهرباء",
        category="06 - كهرباء وماء",
        page_count=1
    )
    # H102 doc
    doc3 = repo.add_document(
        vault_id="v102_1",
        house_id="102 - MedStay",
        tenant_id=t2.id,
        batch_id=b2.id,
        primary_date="2019-04-01",
        arabic_title="أمر تخصيص المسكن",
        category="03 - أمر تخصيص",
        page_count=1
    )
    
    # 6. Pages with content_explanation for search testing
    repo.add_pages_bulk([
        {
            "batch_id": b1.id,
            "page_number": 1,
            "house_id": "101 - ShortStay",
            "content_explanation": "وثيقة إيجار رسمية وتحتوي على شروط العقد والتوقيع",
            "vault_id": "v101_1",
            "subject": "عقد الإيجار الرسمي",
        },
        {
            "batch_id": b1.id,
            "page_number": 2,
            "house_id": "101 - ShortStay",
            "content_explanation": "فاتورة استهلاك الكهرباء والماء لشهر يونيو",
            "vault_id": "v101_2",
            "subject": "فاتورة كهرباء",
        },
    ])
    
    # 7. Create real PDF file for pdf endpoint testing
    # modern path: {areas_root}/{area_id}/{house_id}/vault/doc_{vault_id}.pdf
    areas_root = tmp_path / "areas"
    vault_dir = areas_root / "Safra C" / "101 - ShortStay" / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    pdf_file = vault_dir / "doc_v101_1.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 mock pdf content for phase 95")
    
    # Configure app state
    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C", "Riffa A": "RIF A"}
        db_path = str(db_file)
        
    app.state.config = MockConfig()
    app.state.db_path = str(db_file)
    app.state.repo = repo
    
    yield {
        "repo": repo,
        "conn": conn,
        "db_file": db_file,
        "areas_root": areas_root,
        "h101": h101,
        "t1": t1,
        "doc1": doc1,
        "doc2": doc2,
        "pdf_file": pdf_file,
    }
    
    app.state.repo = None
    app.state.db_path = None
    try:
        conn.close()
    except Exception:
        pass


def test_config_db_path_resolution(tmp_path):
    """Test AppConfig db_path field and automatic discovery of organizer.db."""
    # 1. Explicit db_path
    cfg1 = AppConfig(
        inbox_path=str(tmp_path / "inbox"),
        areas_root_path=str(tmp_path / "areas"),
        db_path=str(tmp_path / "custom.db")
    )
    assert cfg1.db_path == str(tmp_path / "custom.db")
    
    # 2. Not explicitly configured, but organizer.db exists in areas_root_path
    areas_dir = tmp_path / "areas_with_db"
    areas_dir.mkdir(parents=True, exist_ok=True)
    db_in_areas = areas_dir / "organizer.db"
    db_in_areas.write_text("sqlite")
    
    cfg2 = AppConfig(
        inbox_path=str(tmp_path / "inbox"),
        areas_root_path=str(areas_dir),
    )
    assert cfg2.db_path == str(db_in_areas.resolve())


def test_get_tree_with_db(db_setup):
    """Test /api/tree directly querying SQLite database."""
    res = client.get("/api/tree")
    assert res.status_code == 200
    data = res.json()
    
    # Check areas
    assert len(data) == 2
    area_names = {a["name"] for a in data}
    assert "Safra C" in area_names
    assert "Riffa A" in area_names
    
    safra = next(a for a in data if a["name"] == "Safra C")
    houses = safra["children"]
    assert len(houses) == 3
    
    h101 = next(h for h in houses if "101" in h["id"])
    h102 = next(h for h in houses if "102" in h["id"])
    h103 = next(h for h in houses if "103" in h["id"])
    
    # Check active tenant names
    assert h101["current_tenant"] == "Ali Short"
    assert h102["current_tenant"] == "Hassan Medium"
    assert h103["current_tenant"] == "Khalid Long"
    
    # Check tenure color calculation ('<5y' -> 'short', '5-10y' -> 'medium', '>10y' -> 'long')
    assert h101["duration_category"] in ("short", "<5y")
    assert h102["duration_category"] in ("medium", "5-10y")
    assert h103["duration_category"] in ("long", ">10y")
    
    # Check document counts
    assert h101["total_documents"] == 2
    assert h102["total_documents"] == 1
    assert h103["total_documents"] == 0
    
    # Check category counts
    assert "عقود" in h101["category_counts"]
    assert "كهرباء وماء" in h101["category_counts"]
    assert h101["category_counts"]["عقود"] == 1
    assert h101["category_counts"]["كهرباء وماء"] == 1
    
    # Check tenant children ordering: latest tenant comes first, then older tenants
    assert len(h101["children"]) == 2
    assert h101["children"][0]["name"] == "Ali Short"
    assert h101["children"][1]["name"] == "Old Ali"

    active_t_node = h101["children"][0]
    past_t_node = h101["children"][1]
    assert active_t_node["duration_category"] in ("short", "<5y")
    assert "Present" in active_t_node["subtitle"]
    assert past_t_node["duration_category"] is None
    assert "2020 - 2023" in past_t_node["subtitle"]


def test_get_tree_subchildren_options(db_setup):
    """Test /api/tree with optional subchildren query parameters."""
    res = client.get("/api/tree?include_categories=true")
    assert res.status_code == 200
    data = res.json()
    safra = next(a for a in data if a["name"] == "Safra C")
    h101 = next(h for h in safra["children"] if "101" in h["id"])
    child_types = {c["type"] for c in h101["children"]}
    assert "category" in child_types


def test_timeline_endpoint_with_db(db_setup):
    """Test /api/areas/{area}/houses/{house}/timeline with DB."""
    res = client.get("/api/areas/Safra%20C/houses/101%20-%20ShortStay/timeline")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    
    # Verify chronological descending order (2024-06-15 before 2024-02-01)
    assert data[0]["vault_id"] == "v101_2"
    assert data[0]["dates"] == ["2024-06-15"]
    assert data[0]["brief_arabic_title"] == "إيصال كهرباء"
    assert data[0]["primary_tenant"] == "Ali Short"
    
    assert data[1]["vault_id"] == "v101_1"
    assert data[1]["dates"] == ["2024-02-01"]
    assert data[1]["brief_arabic_title"] == "عقد إيجار جديد"
    assert data[1]["primary_tenant"] == "Ali Short"


def test_categories_endpoint_with_db(db_setup):
    """Test /api/areas/{area}/houses/{house}/categories with DB."""
    res = client.get("/api/areas/Safra%20C/houses/101%20-%20ShortStay/categories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    
    cat_names = {c["name"] for c in data}
    assert any("عقود" in name for name in cat_names)
    assert any("كهرباء وماء" in name for name in cat_names)
    
    cat1 = next(c for c in data if "عقود" in c["name"])
    assert cat1["tenant"] == "Ali Short"
    assert cat1["document_count"] == 1
    assert len(cat1["documents"]) == 1
    assert cat1["documents"][0]["vault_id"] == "v101_1"
    assert cat1["documents"][0]["brief_arabic_title"] == "عقد إيجار جديد"


def test_search_endpoint_with_db(db_setup):
    """Test /api/search querying SQLite database."""
    # 1. House search
    res_house = client.get("/api/search?q=shortstay")
    assert res_house.status_code == 200
    houses = [r for r in res_house.json() if r["type"] == "house"]
    assert len(houses) >= 1
    assert houses[0]["id"] == "101 - ShortStay"
    assert "Safra C" in houses[0]["subtitle"]
    
    # 2. Tenant search (exact & fuzzy)
    res_tenant = client.get("/api/search?q=hassan")
    assert res_tenant.status_code == 200
    tenants = [r for r in res_tenant.json() if r["type"] == "tenant"]
    assert len(tenants) >= 1
    assert tenants[0]["title"] == "Hassan Medium"
    
    # 3. Document Arabic title search
    res_doc_title = client.get("/api/search?q=كهرباء")
    assert res_doc_title.status_code == 200
    docs = [r for r in res_doc_title.json() if r["type"] == "document"]
    assert len(docs) >= 1
    assert any("كهرباء" in d["title"] for d in docs)
    
    # 4. Document page content search
    res_doc_content = client.get("/api/search?q=شروط العقد")
    assert res_doc_content.status_code == 200
    docs_content = [r for r in res_doc_content.json() if r["type"] == "document"]
    assert len(docs_content) >= 1
    assert docs_content[0]["id"] == "101 - ShortStay_doc_v101_1"


def test_search_tenants_timeline_color_coding(db_setup):
    """Test /api/search tenant results contain accurate is_current and duration_category."""
    # Active tenant < 5 years (Ali Short, started 2024) -> short
    res_short = client.get("/api/search?q=Ali Short")
    assert res_short.status_code == 200
    tenants_short = [r for r in res_short.json() if r["type"] == "tenant" and r["title"] == "Ali Short"]
    assert len(tenants_short) >= 1
    assert tenants_short[0]["is_current"] is True
    assert tenants_short[0]["duration_category"] == "short"

    # Past tenant (Old Ali, 2020 - 2023) -> is_current False, duration_category None
    res_past = client.get("/api/search?q=Old Ali")
    assert res_past.status_code == 200
    tenants_past = [r for r in res_past.json() if r["type"] == "tenant" and r["title"] == "Old Ali"]
    assert len(tenants_past) >= 1
    assert tenants_past[0]["is_current"] is False
    assert tenants_past[0]["duration_category"] is None

    # Active tenant 5-10 years (Hassan Medium, started 2019) -> medium
    res_med = client.get("/api/search?q=Hassan Medium")
    assert res_med.status_code == 200
    tenants_med = [r for r in res_med.json() if r["type"] == "tenant" and r["title"] == "Hassan Medium"]
    assert len(tenants_med) >= 1
    assert tenants_med[0]["is_current"] is True
    assert tenants_med[0]["duration_category"] == "medium"

    # Active tenant > 10 years (Khalid Long, started 2012) -> long
    res_long = client.get("/api/search?q=Khalid Long")
    assert res_long.status_code == 200
    tenants_long = [r for r in res_long.json() if r["type"] == "tenant" and r["title"] == "Khalid Long"]
    assert len(tenants_long) >= 1
    assert tenants_long[0]["is_current"] is True
    assert tenants_long[0]["duration_category"] == "long"



def test_pdf_endpoint_with_db(db_setup):
    """Test /api/areas/{area}/houses/{house}/pdf/{vault_id} serving PDF from vault."""
    res = client.get("/api/areas/Safra%20C/houses/101%20-%20ShortStay/pdf/v101_1")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert b"mock pdf content for phase 95" in res.content
    
    # Non-existent vault ID returns 404
    res_404 = client.get("/api/areas/Safra%20C/houses/101%20-%20ShortStay/pdf/nonexistent")
    assert res_404.status_code == 404


def test_benchmark_get_tree_performance(db_setup):
    """Benchmark /api/tree completes in < 50ms with SQLite database."""
    # Warm-up call
    res = client.get("/api/tree")
    assert res.status_code == 200
    
    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        r = client.get("/api/tree")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert r.status_code == 200
        times.append(elapsed_ms)
        
    avg_ms = sum(times) / len(times)
    max_ms = max(times)
    assert avg_ms < 50.0, f"Average /api/tree latency {avg_ms:.2f}ms exceeds 50ms threshold"
    assert max_ms < 50.0, f"Max /api/tree latency {max_ms:.2f}ms exceeds 50ms threshold"


def test_db_info_endpoint(db_setup):
    """Test /api/db/info returns connection status and table row counts."""
    res = client.get("/api/db/info")
    assert res.status_code == 200
    data = res.json()
    assert data["connected"] is True
    assert "tables" in data
    assert data["tables"]["areas"] == 2
    assert data["tables"]["houses"] == 4
    assert data["tables"]["tenants"] == 4
    assert data["tables"]["batches"] == 2
    assert data["tables"]["documents"] == 3
    assert data["tables"]["pages"] == 2


def test_db_tables_endpoint(db_setup):
    """Test /api/db/tables/{table_name} returns rows, columns, and supports pagination/search."""
    res = client.get("/api/db/tables/houses")
    assert res.status_code == 200
    data = res.json()
    assert data["table"] == "houses"
    assert "id" in data["columns"]
    assert data["total"] == 4
    assert len(data["rows"]) == 4

    # Test pagination
    res_page = client.get("/api/db/tables/houses?limit=2&offset=0")
    assert res_page.status_code == 200
    data_page = res_page.json()
    assert len(data_page["rows"]) == 2

    # Test search filter
    res_search = client.get("/api/db/tables/houses?search=Riffa")
    assert res_search.status_code == 200
    assert len(res_search.json()["rows"]) == 1

    # Invalid table returns 400
    res_invalid = client.get("/api/db/tables/invalid_table")
    assert res_invalid.status_code == 400


def test_get_tree_vacant_house_no_active_tenant(db_setup):
    """Test that a house whose tenants all vacated in the past has current_tenant=None and duration_category=None."""
    repo = db_setup["repo"]
    repo.add_house(house_id="538", area_id="Safra C")
    repo.add_tenant(house_id="538", name="فهد المغادر", start_date="2020-01-01", end_date="2024-12-31")

    res = client.get("/api/tree")
    assert res.status_code == 200
    data = res.json()
    safra = next(a for a in data if a["name"] == "Safra C")
    h538 = next(h for h in safra["children"] if h["id"] == "538")

    assert h538["current_tenant"] is None
    assert h538["duration_category"] is None
    assert h538["subtitle"] == "2020 - 2024"
    assert len(h538["children"]) == 1
    assert h538["children"][0]["duration_category"] is None
    assert "Present" not in (h538["children"][0]["subtitle"] or "")


