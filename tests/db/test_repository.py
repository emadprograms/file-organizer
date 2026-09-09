import pytest
from datetime import date
from src.db.connection import get_db_connection
from src.db.schema import init_db
from src.db.models import Area, House, Tenant, Batch, Page, Document
from src.db.repository import Repository


@pytest.fixture
def repo(tmp_path):
    db_file = tmp_path / "repo_test.db"
    conn = get_db_connection(db_file)
    init_db(conn)
    repository = Repository(conn)
    yield repository
    conn.close()


def test_area_crud(repo):
    # Add area
    area = repo.add_area("AREA_A", code="A")
    assert area.id == "AREA_A"
    assert area.code == "A"

    # Get area
    fetched = repo.get_area("AREA_A")
    assert fetched is not None
    assert fetched.id == "AREA_A"
    assert fetched.code == "A"

    # Get non-existent
    assert repo.get_area("NON_EXISTENT") is None

    # List areas
    repo.add_area("AREA_B", code="B")
    areas = repo.list_areas()
    assert len(areas) == 2
    area_ids = [a.id for a in areas]
    assert "AREA_A" in area_ids
    assert "AREA_B" in area_ids


def test_house_crud(repo):
    repo.add_area("AREA_A")
    repo.add_area("AREA_B")

    # Add house
    h1 = repo.add_house("H01", area_id="AREA_A")
    assert h1.id == "H01"
    assert h1.area_id == "AREA_A"

    h2 = repo.add_house("H02", area_id="AREA_A")
    h3 = repo.add_house("H03", area_id="AREA_B")

    # Get house
    assert repo.get_house("H01").id == "H01"
    assert repo.get_house("UNKNOWN") is None

    # List houses by area
    area_a_houses = repo.list_houses_by_area("AREA_A")
    assert len(area_a_houses) == 2
    assert {h.id for h in area_a_houses} == {"H01", "H02"}

    area_b_houses = repo.list_houses_by_area("AREA_B")
    assert len(area_b_houses) == 1
    assert area_b_houses[0].id == "H03"


def test_tenant_crud(repo):
    repo.add_area("AREA_A")
    repo.add_house("H01", area_id="AREA_A")

    # Add tenants
    t1 = repo.add_tenant(
        house_id="H01",
        name="John Doe",
        start_date="2023-01-01",
        end_date="2023-12-31",
    )
    assert t1.id is not None
    assert t1.name == "John Doe"

    t2 = repo.add_tenant(
        house_id="H01",
        name="Jane Smith",
        start_date="2024-01-01",
        end_date=None,
    )
    assert t2.id is not None
    assert t2.name == "Jane Smith"

    # List tenants by house
    tenants = repo.list_tenants_by_house("H01")
    assert len(tenants) == 2

    # Get active tenant by date
    active_2023 = repo.get_active_tenant("H01", target_date="2023-06-15")
    assert active_2023 is not None
    assert active_2023.name == "John Doe"

    active_2024 = repo.get_active_tenant("H01", target_date="2024-05-01")
    assert active_2024 is not None
    assert active_2024.name == "Jane Smith"

    active_2020 = repo.get_active_tenant("H01", target_date="2020-01-01")
    assert active_2020 is None

    # Adding duplicate normalized name returns existing tenant
    t1_dup = repo.add_tenant(
        house_id="H01",
        name="  john doe  ",
        start_date="2023-01-01",
    )
    assert t1_dup.id == t1.id
    assert len(repo.list_tenants_by_house("H01")) == 2


def test_batch_crud(repo):
    repo.add_area("AREA_A")
    repo.add_house("H01", area_id="AREA_A")

    # Create batch
    b1 = repo.create_batch(
        house_id="H01",
        filename="batch1.pdf",
        file_path="/data/batch1.pdf",
        page_count=10,
        status="completed",
    )
    assert b1.id is not None
    assert b1.house_id == "H01"
    assert b1.page_count == 10
    assert b1.status == "completed"

    # Get batch
    fetched = repo.get_batch(b1.id)
    assert fetched is not None
    assert fetched.filename == "batch1.pdf"
    assert repo.get_batch(9999) is None

    # Update batch status
    updated = repo.update_batch_status(b1.id, "processing")
    assert updated.status == "processing"
    assert repo.get_batch(b1.id).status == "processing"

    # List batches by house
    repo.create_batch(
        house_id="H01",
        filename="batch2.pdf",
        file_path="/data/batch2.pdf",
        page_count=5,
    )
    batches = repo.list_batches_by_house("H01")
    assert len(batches) == 2


def test_page_crud(repo):
    repo.add_area("AREA_A")
    repo.add_house("H01", area_id="AREA_A")
    b = repo.create_batch("H01", "scan.pdf", "/path/scan.pdf", 2)

    # Bulk add pages
    p1_data = Page(
        batch_id=b.id,
        page_number=1,
        house_id="H01",
        raw_date="2023-05-01",
        subject="Electricity Bill",
    )
    p2_data = Page(
        batch_id=b.id,
        page_number=2,
        house_id="H01",
        is_continuation=True,
    )

    created_pages = repo.add_pages_bulk([p1_data, p2_data])
    assert len(created_pages) == 2
    assert created_pages[0].id is not None
    assert created_pages[1].id is not None

    # Get pages by batch
    pages = repo.get_pages_by_batch(b.id)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert pages[1].page_number == 2
    assert pages[0].subject == "Electricity Bill"
    assert pages[1].is_continuation is True

    # Update page cleaning
    updated_page = repo.update_page_cleaning(
        pages[0].id,
        category="Utilities",
        fine_category="DEWA Bill",
        fine_category_reason="Contains DEWA logo and account number",
        resolved_date="2023-05-01",
    )
    assert updated_page.category == "Utilities"
    assert updated_page.fine_category == "DEWA Bill"
    assert updated_page.fine_category_reason == "Contains DEWA logo and account number"
    assert updated_page.resolved_date == "2023-05-01"


def test_document_crud_and_page_linking(repo):
    repo.add_area("AREA_A")
    repo.add_house("H01", area_id="AREA_A")
    tenant = repo.add_tenant("H01", "Tenant 1", "2023-01-01")
    batch = repo.create_batch("H01", "scan.pdf", "/path/scan.pdf", 2)
    pages = repo.add_pages_bulk([
        Page(batch_id=batch.id, page_number=1, house_id="H01"),
        Page(batch_id=batch.id, page_number=2, house_id="H01"),
    ])

    # Add document
    doc = Document(
        vault_id="DOC_V001",
        house_id="H01",
        tenant_id=tenant.id,
        batch_id=batch.id,
        primary_date="2023-05-15",
        arabic_title="فاتورة كهرباء",
        category="Utilities",
        page_count=2,
    )
    created_doc = repo.add_document(doc)
    assert created_doc.vault_id == "DOC_V001"

    # Get document
    fetched = repo.get_document("DOC_V001")
    assert fetched is not None
    assert fetched.arabic_title == "فاتورة كهرباء"
    assert repo.get_document("UNKNOWN") is None

    # Link pages to document
    repo.link_pages_to_document([pages[0].id, pages[1].id], "DOC_V001")
    reloaded_pages = repo.get_pages_by_batch(batch.id)
    assert reloaded_pages[0].vault_id == "DOC_V001"
    assert reloaded_pages[1].vault_id == "DOC_V001"

    # List documents by house
    docs_house = repo.list_documents_by_house("H01")
    assert len(docs_house) == 1
    assert docs_house[0].vault_id == "DOC_V001"

    # List documents by category
    docs_cat = repo.list_documents_by_category("H01", category="Utilities")
    assert len(docs_cat) == 1
    assert docs_cat[0].vault_id == "DOC_V001"

    docs_empty = repo.list_documents_by_category("H01", category="Maintenance")
    assert len(docs_empty) == 0


def test_repository_transaction_rollback(repo):
    repo.add_area("AREA_TX")
    repo.add_house("H_TX", area_id="AREA_TX")

    # Verify transaction rollback
    with pytest.raises(ValueError):
        with repo.transaction():
            repo.create_batch("H_TX", "tx1.pdf", "/tmp/tx1.pdf", 1)
            raise ValueError("Rollback triggered")

    assert len(repo.list_batches_by_house("H_TX")) == 0

    # Verify successful transaction
    with repo.transaction():
        repo.create_batch("H_TX", "tx2.pdf", "/tmp/tx2.pdf", 2)

    assert len(repo.list_batches_by_house("H_TX")) == 1


def test_standalone_functions(tmp_path):
    from src.db.repository import (
        add_area,
        get_area,
        list_areas,
        add_house,
        get_house,
        list_houses_by_area,
        add_tenant,
        get_active_tenant,
        list_tenants_by_house,
        create_batch,
        get_batch,
        update_batch_status,
        list_batches_by_house,
        add_pages_bulk,
        get_pages_by_batch,
        update_page_cleaning,
        link_pages_to_document,
        add_document,
        get_document,
        list_documents_by_house,
        list_documents_by_category,
    )

    db_file = tmp_path / "standalone.db"
    conn = get_db_connection(db_file)
    init_db(conn)

    a = add_area(conn, "A_STANDALONE", "AST")
    assert get_area(conn, "A_STANDALONE").code == "AST"
    assert len(list_areas(conn)) == 1

    h = add_house(conn, "H_STANDALONE", "A_STANDALONE")
    assert get_house(conn, "H_STANDALONE").area_id == "A_STANDALONE"
    assert len(list_houses_by_area(conn, "A_STANDALONE")) == 1

    t = add_tenant(conn, "H_STANDALONE", "Active Tenant", date(2020, 1, 1), None)
    assert get_active_tenant(conn, "H_STANDALONE").name == "Active Tenant"
    assert len(list_tenants_by_house(conn, "H_STANDALONE")) == 1

    b = create_batch(conn, "H_STANDALONE", "f.pdf", "/p/f.pdf", 1)
    assert get_batch(conn, b.id).filename == "f.pdf"
    assert update_batch_status(conn, b.id, "failed").status == "failed"
    assert len(list_batches_by_house(conn, "H_STANDALONE")) == 1

    p = add_pages_bulk(conn, [Page(batch_id=b.id, page_number=1, house_id="H_STANDALONE")])
    assert len(get_pages_by_batch(conn, b.id)) == 1
    assert update_page_cleaning(conn, p[0].id, category="Contracts").category == "Contracts"
    assert update_page_cleaning(conn, p[0].id) is not None

    d = add_document(conn, vault_id="DOC_ST", house_id="H_STANDALONE", tenant_id=t.id, batch_id=b.id, category="Contracts")
    assert get_document(conn, "DOC_ST").vault_id == "DOC_ST"
    assert len(list_documents_by_house(conn, "H_STANDALONE")) == 1
    assert len(list_documents_by_category(conn, "H_STANDALONE", "Contracts")) == 1

    assert link_pages_to_document(conn, [p[0].id], "DOC_ST") == 1
    assert link_pages_to_document(conn, [], "DOC_ST") == 0

    conn.close()

