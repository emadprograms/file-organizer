import pytest
import io
import zipfile
import urllib.parse
from pathlib import Path
import fitz
from fastapi.testclient import TestClient
from src.api.server import app
from src.db.schema import init_db
from src.db.connection import get_db_connection
from src.db.repository import Repository

client = TestClient(app)

@pytest.fixture
def test_setup(tmp_path):
    db_file = tmp_path / "test_v14.db"
    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)
        
    repo.add_area(area_id="Area A")
    repo.add_house(house_id="House 100", area_id="Area A")
    t = repo.add_tenant(house_id="House 100", name="Test Tenant", start_date="2024-01-01")
    
    # Create physical vault directory and sample document
    areas_root = tmp_path / "data"
    vault_dir = areas_root / "Area A" / "House 100" / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    # Write sample pdf (valid PDF starting with %PDF-1.4)
    sample_pdf = vault_dir / "doc_v14test01.pdf"
    doc_new = fitz.open()
    doc_new.new_page()
    pdf_bytes = doc_new.tobytes().replace(b"%PDF-1.7", b"%PDF-1.4")
    doc_new.close()
    sample_pdf.write_bytes(pdf_bytes)
    
    # Register document in DB
    batch = repo.create_batch(filename="test.pdf", file_path=str(sample_pdf), house_id="House 100", page_count=1)
    repo.add_document(
        vault_id="v14test01",
        house_id="House 100",
        tenant_id=t.id,
        batch_id=batch.id,
        primary_date="2024-05-15",
        arabic_title="عقد إيجار تجريبي",
        category="05 - عقود",
        page_count=1,
    )
    
    class DummyConfig:
        areas_root_path = str(areas_root)
        
    app.state.repo = repo
    app.state.db_path = str(db_file)
    app.state.config = DummyConfig()
    
    return {
        "repo": repo,
        "conn": conn,
        "areas_root": areas_root,
        "vault_dir": vault_dir,
        "tenant": t,
    }

def test_export_house_archive_zip(test_setup):
    res = client.get("/api/areas/Area A/houses/House 100/export-zip")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert "attachment;" in res.headers["content-disposition"]
    
    # Read zip content
    zip_bytes = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        file_list = zf.namelist()
        assert len(file_list) == 1
        assert "05 - عقود" in file_list[0]
        assert "2024-05-15" in file_list[0]
        content = zf.read(file_list[0])
        assert b"%PDF-1.4" in content

def test_export_house_archive_zip_empty_house(test_setup):
    # House with no documents returns zip with README.txt
    test_setup["repo"].add_house(house_id="House 101", area_id="Area A")
    res = client.get("/api/areas/Area A/houses/House 101/export-zip")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    
    zip_bytes = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        assert "README.txt" in zf.namelist()


def test_export_house_archive_zip_with_tenant_filter(test_setup):
    repo = test_setup["repo"]
    vault_dir = test_setup["vault_dir"]

    t2 = repo.add_tenant(house_id="House 100", name="خالد العتيبي", start_date="2024-06-01")
    p2 = vault_dir / "doc_v14test02.pdf"
    p2.write_bytes(b"%PDF-1.4 tenant 2 content")
    b2 = repo.create_batch(filename="test2.pdf", file_path=str(p2), house_id="House 100", page_count=1)
    repo.add_document(
        vault_id="v14test02",
        house_id="House 100",
        tenant_id=t2.id,
        batch_id=b2.id,
        primary_date="2024-07-01",
        arabic_title="أمر تخصيص المسكن",
        category="أمر تخصيص",
        page_count=1,
    )

    res = client.get(f"/api/areas/Area A/houses/House 100/export-zip?tenant_id={t2.id}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert "خالد_العتيبي" in urllib.parse.unquote(res.headers["content-disposition"]) or f"tenant_{t2.id}" in res.headers["content-disposition"]

    zip_bytes = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        file_list = zf.namelist()
        assert len(file_list) == 1
        # Check folder numbering normalization (from urgent user requirement)
        assert file_list[0].startswith("03 - أمر تخصيص/")


def test_export_house_archive_zip_folder_numbering_normalization(test_setup):
    repo = test_setup["repo"]
    vault_dir = test_setup["vault_dir"]
    t = test_setup["tenant"]

    # Ingest document with unnumbered category name 'كهرباء وماء'
    p3 = vault_dir / "doc_v14test03.pdf"
    p3.write_bytes(b"%PDF-1.4 elec doc")
    b3 = repo.create_batch(filename="test3.pdf", file_path=str(p3), house_id="House 100", page_count=1)
    repo.add_document(
        vault_id="v14test03",
        house_id="House 100",
        tenant_id=t.id,
        batch_id=b3.id,
        primary_date="2024-08-01",
        arabic_title="فاتورة كهرباء",
        category="كهرباء وماء",
        page_count=1,
    )

    res = client.get("/api/areas/Area A/houses/House 100/export-zip")
    assert res.status_code == 200
    zip_bytes = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        file_list = zf.namelist()
        assert any(name.startswith("05 - عقود/") for name in file_list)
        assert any(name.startswith("06 - كهرباء وماء/") for name in file_list)


def test_export_house_archive_pdf(test_setup):
    repo = test_setup["repo"]
    vault_dir = test_setup["vault_dir"]
    t = test_setup["tenant"]

    # Add second document with valid PDF
    p2 = vault_dir / "doc_v14test_pdf2.pdf"
    doc2 = fitz.open()
    doc2.new_page()
    p2.write_bytes(doc2.tobytes())
    doc2.close()

    b2 = repo.create_batch(filename="test_pdf2.pdf", file_path=str(p2), house_id="House 100", page_count=1)
    repo.add_document(
        vault_id="v14test_pdf2",
        house_id="House 100",
        tenant_id=t.id,
        batch_id=b2.id,
        primary_date="2024-06-01",
        arabic_title="مستند صيانة",
        category="10 - صيانة",
        page_count=1,
    )

    res = client.get("/api/areas/Area A/houses/House 100/export-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment;" in res.headers["content-disposition"]
    assert "archive_Area_A_House_100.pdf" in res.headers["content-disposition"]

    merged_doc = fitz.open(stream=res.content, filetype="pdf")
    assert len(merged_doc) >= 2
    merged_doc.close()


def test_export_house_archive_pdf_with_tenant_filter(test_setup):
    repo = test_setup["repo"]
    vault_dir = test_setup["vault_dir"]

    t_new = repo.add_tenant(house_id="House 100", name="سعد الشمري", start_date="2024-09-01")
    p = vault_dir / "doc_v14test_saad.pdf"
    doc = fitz.open()
    doc.new_page()
    p.write_bytes(doc.tobytes())
    doc.close()

    b = repo.create_batch(filename="saad.pdf", file_path=str(p), house_id="House 100", page_count=1)
    repo.add_document(
        vault_id="v14test_saad",
        house_id="House 100",
        tenant_id=t_new.id,
        batch_id=b.id,
        primary_date="2024-09-10",
        arabic_title="مستند سعد",
        category="05 - عقود",
        page_count=1,
    )

    res = client.get(f"/api/areas/Area A/houses/House 100/export-pdf?tenant_id={t_new.id}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "سعد_الشمري" in urllib.parse.unquote(res.headers["content-disposition"]) or f"tenant_{t_new.id}" in res.headers["content-disposition"]

    merged_doc = fitz.open(stream=res.content, filetype="pdf")
    assert len(merged_doc) == 1
    merged_doc.close()


def test_export_house_archive_pdf_empty_house(test_setup):
    test_setup["repo"].add_house(house_id="House 102", area_id="Area A")
    res = client.get("/api/areas/Area A/houses/House 102/export-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"

    merged_doc = fitz.open(stream=res.content, filetype="pdf")
    assert len(merged_doc) == 1
    text = merged_doc[0].get_text()
    assert "No documents found in archive" in text
    merged_doc.close()


def test_batch_move_documents(test_setup):
    repo = test_setup["repo"]
    vault_dir = test_setup["vault_dir"]
    t = test_setup["tenant"]

    # Add second document
    p2 = vault_dir / "doc_v14test02.pdf"
    p2.write_bytes(b"%PDF-1.4 doc 2")
    b2 = repo.create_batch(filename="test2.pdf", file_path=str(p2), house_id="House 100", page_count=1)
    repo.add_document(
        vault_id="v14test02",
        house_id="House 100",
        tenant_id=t.id,
        batch_id=b2.id,
        primary_date="2024-05-16",
        arabic_title="فاتورة كهرباء",
        category="05 - عقود",
        page_count=1,
    )

    # Empty payload validation
    res_err1 = client.post("/api/areas/Area A/houses/House 100/documents/batch-move", json={"vault_ids": [], "target_category": "صيانة"})
    assert res_err1.status_code == 400

    res_err2 = client.post("/api/areas/Area A/houses/House 100/documents/batch-move", json={"vault_ids": ["v14test01"], "target_category": ""})
    assert res_err2.status_code == 400

    # Successful batch move to standard category
    res = client.post(
        "/api/areas/Area A/houses/House 100/documents/batch-move",
        json={"vault_ids": ["v14test01", "v14test02"], "target_category": "10 - صيانة"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["moved_count"] == 2
    assert data["target_category"] == "10 - صيانة"
    assert set(data["vault_ids"]) == {"v14test01", "v14test02"}

    # Verify DB update and is_manual flag
    doc1 = repo.get_document("v14test01")
    doc2 = repo.get_document("v14test02")
    assert doc1.category == "10 - صيانة"
    assert doc1.is_manual == 1
    assert doc2.category == "10 - صيانة"
    assert doc2.is_manual == 1


def test_batch_delete_documents(test_setup):
    repo = test_setup["repo"]
    vault_dir = test_setup["vault_dir"]
    t = test_setup["tenant"]

    # Add second document with physical file
    p2 = vault_dir / "doc_v14test03.pdf"
    p2.write_bytes(b"%PDF-1.4 doc 3")
    b3 = repo.create_batch(filename="test3.pdf", file_path=str(p2), house_id="House 100", page_count=1)
    repo.add_document(
        vault_id="v14test03",
        house_id="House 100",
        tenant_id=t.id,
        batch_id=b3.id,
        primary_date="2024-05-17",
        arabic_title="مستند للحذف",
        category="05 - عقود",
        page_count=1,
    )

    pdf1 = vault_dir / "doc_v14test01.pdf"
    assert pdf1.exists()
    assert p2.exists()

    # Empty payload validation
    res_err = client.post("/api/areas/Area A/houses/House 100/documents/batch-delete", json={"vault_ids": []})
    assert res_err.status_code == 400

    # Successful batch delete
    res = client.post(
        "/api/areas/Area A/houses/House 100/documents/batch-delete",
        json={"vault_ids": ["v14test01", "v14test03"]}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["deleted_count"] == 2
    assert set(data["vault_ids"]) == {"v14test01", "v14test03"}

    # Verify documents deleted from DB
    assert repo.get_document("v14test01") is None
    assert repo.get_document("v14test03") is None

    # Verify physical files removed from disk
    assert not pdf1.exists()
    assert not p2.exists()


def test_create_house_with_initial_tenant_and_directories(test_setup):
    repo = test_setup["repo"]
    areas_root = test_setup["areas_root"]

    # 1. Create house with initial tenant in existing area
    res = client.post(
        "/api/areas/Area A/houses",
        json={
            "house_id": "House 102",
            "initial_tenant_name": "خالد العتيبي",
            "start_date": "2024-06-01",
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["area_id"] == "Area A"
    assert data["house_id"] == "House 102"
    assert data["tenant_id"] is not None
    assert "House 'House 102' registered successfully" in data["message"]

    # Verify house in DB
    house = repo.get_house("House 102")
    assert house is not None
    assert house.area_id == "Area A"

    # Verify tenant in DB
    tenant = repo.get_tenant(data["tenant_id"])
    assert tenant is not None
    assert tenant.name == "خالد العتيبي"
    assert str(tenant.start_date) == "2024-06-01"
    assert tenant.house_id == "House 102"

    # Verify physical filesystem directories scaffolded
    batches_dir = areas_root / "Area A" / "House 102" / "batches"
    vault_dir = areas_root / "Area A" / "House 102" / "vault"
    assert batches_dir.exists() and batches_dir.is_dir()
    assert vault_dir.exists() and vault_dir.is_dir()

    # 2. Create house in a brand-new area without initial tenant
    res2 = client.post(
        "/api/areas/Area B/houses",
        json={
            "house_id": "House 201",
        }
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "success"
    assert data2["area_id"] == "Area B"
    assert data2["house_id"] == "House 201"
    assert data2["tenant_id"] is None

    # Verify Area B created
    area_b = repo.get_area("Area B")
    assert area_b is not None

    # Verify directories scaffolded for Area B
    assert (areas_root / "Area B" / "House 201" / "batches").exists()
    assert (areas_root / "Area B" / "House 201" / "vault").exists()


def test_create_house_duplicate_or_invalid(test_setup):
    # 1. Validation failure on empty house_id
    res_empty = client.post(
        "/api/areas/Area A/houses",
        json={"house_id": "  "}
    )
    assert res_empty.status_code == 400

    # 2. Duplicate house error (House 100 already seeded in test_setup)
    res_dup = client.post(
        "/api/areas/Area A/houses",
        json={"house_id": "House 100"}
    )
    assert res_dup.status_code in (400, 409)
    err_msg = res_dup.json()["detail"]
    assert "already exists" in err_msg


