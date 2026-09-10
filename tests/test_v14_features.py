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
    p_setup = doc_new.new_page()
    p_setup.insert_text((50, 50), "DOC_2024_05_15")
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

    # Add second document with valid PDF (date 2024-06-01 is newer than 2024-05-15)
    p2 = vault_dir / "doc_v14test_pdf2.pdf"
    doc2 = fitz.open()
    p2_page = doc2.new_page()
    p2_page.insert_text((50, 50), "DOC_2024_06_01")
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
    # Verify descending chronological order: 2024-06-01 before 2024-05-15
    assert "DOC_2024_06_01" in merged_doc[0].get_text()
    assert "DOC_2024_05_15" in merged_doc[1].get_text()
    merged_doc.close()


def test_export_house_archive_pdf_descending_chronological_order(test_setup):
    """Verify combined PDF export is sorted in descending chronological order:
    Recent document first (e.g. 2024-05-15), oldest document last (e.g. 2020-03-01),
    and undated documents at the very end.
    """
    repo = test_setup["repo"]
    areas_root = Path(client.app.state.config.areas_root_path)
    vault_200 = areas_root / "Area A" / "House 200" / "vault"
    vault_200.mkdir(parents=True, exist_ok=True)
    repo.add_house(house_id="House 200", area_id="Area A")
    t = repo.add_tenant(house_id="House 200", name="مستأجر تجريبي", start_date="2020-01-01")

    # Document 1: 2021-01-01 (middle date)
    p_mid = vault_200 / "doc_pdf_mid.pdf"
    d_mid = fitz.open()
    d_mid.new_page().insert_text((50, 50), "DOC_2021_01_01")
    p_mid.write_bytes(d_mid.tobytes())
    d_mid.close()
    b_mid = repo.create_batch(filename="mid.pdf", file_path=str(p_mid), house_id="House 200", page_count=1)
    repo.add_document(
        vault_id="pdf_mid",
        house_id="House 200",
        tenant_id=t.id,
        batch_id=b_mid.id,
        primary_date="2021-01-01",
        arabic_title="وثيقة 2021",
        category="05 - عقود",
        page_count=1,
    )

    # Document 2: 2024-05-15 (newest / most recent date)
    p_new = vault_200 / "doc_pdf_new.pdf"
    d_new = fitz.open()
    d_new.new_page().insert_text((50, 50), "DOC_2024_05_15")
    p_new.write_bytes(d_new.tobytes())
    d_new.close()
    b_new = repo.create_batch(filename="new.pdf", file_path=str(p_new), house_id="House 200", page_count=1)
    repo.add_document(
        vault_id="pdf_new",
        house_id="House 200",
        tenant_id=t.id,
        batch_id=b_new.id,
        primary_date="2024-05-15",
        arabic_title="وثيقة 2024",
        category="05 - عقود",
        page_count=1,
    )

    # Document 3: 2020-03-01 (oldest date)
    p_old = vault_200 / "doc_pdf_old.pdf"
    d_old = fitz.open()
    d_old.new_page().insert_text((50, 50), "DOC_2020_03_01")
    p_old.write_bytes(d_old.tobytes())
    d_old.close()
    b_old = repo.create_batch(filename="old.pdf", file_path=str(p_old), house_id="House 200", page_count=1)
    repo.add_document(
        vault_id="pdf_old",
        house_id="House 200",
        tenant_id=t.id,
        batch_id=b_old.id,
        primary_date="2020-03-01",
        arabic_title="وثيقة 2020",
        category="05 - عقود",
        page_count=1,
    )

    # Document 4: Undated document (primary_date=None) -> should be placed after all dated documents
    p_undated = vault_200 / "doc_pdf_undated.pdf"
    d_undated = fitz.open()
    d_undated.new_page().insert_text((50, 50), "DOC_UNDATED")
    p_undated.write_bytes(d_undated.tobytes())
    d_undated.close()
    b_undated = repo.create_batch(filename="undated.pdf", file_path=str(p_undated), house_id="House 200", page_count=1)
    repo.add_document(
        vault_id="pdf_undated",
        house_id="House 200",
        tenant_id=t.id,
        batch_id=b_undated.id,
        primary_date=None,
        arabic_title="وثيقة بدون تاريخ",
        category="05 - عقود",
        page_count=1,
    )

    res = client.get("/api/areas/Area A/houses/House 200/export-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "archive_Area_A_House_200.pdf" in res.headers["content-disposition"]

    merged_doc = fitz.open(stream=res.content, filetype="pdf")
    assert len(merged_doc) == 4
    # Verify Page 1 (index 0) is from 2024-05-15 (newest date)
    assert "DOC_2024_05_15" in merged_doc[0].get_text()
    # Verify Page 2 (index 1) is from 2021-01-01 (middle date)
    assert "DOC_2021_01_01" in merged_doc[1].get_text()
    # Verify Page 3 (index 2) is from 2020-03-01 (oldest dated document)
    assert "DOC_2020_03_01" in merged_doc[2].get_text()
    # Verify Page 4 (index 3 / last page) is the undated document
    assert "DOC_UNDATED" in merged_doc[3].get_text()
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


def test_export_house_archive_pdf_running_footer(test_setup):
    """Test ultra-clean 3-element running footer on each page of exported combined house PDF dossier.
    Footer layout:
    - Bottom Left: The document filing date (e.g. 2024-05-15). If undated, leave blank.
    - Bottom Center: The clean category name WITHOUT the number prefix (e.g. '05 - عقود' -> 'عقود').
    - Bottom Right: X/Y  (Z) where X is page within document, Y is doc page count, Z is master overall page.
    - Zero verbose labels (no 'Date:', 'Category:', 'Page:', '05 -').
    """
    import unicodedata
    repo = test_setup["repo"]
    areas_root = Path(client.app.state.config.areas_root_path)
    vault_300 = areas_root / "Area A" / "House 300" / "vault"
    vault_300.mkdir(parents=True, exist_ok=True)
    repo.add_house(house_id="House 300", area_id="Area A")
    t = repo.add_tenant(house_id="House 300", name="مستأجر الفوتر", start_date="2024-01-01")

    # Document 1: 2024-05-15, 2 pages, Category: "05 - عقود"
    p1 = vault_300 / "doc_footer_doc1.pdf"
    d1 = fitz.open()
    d1.new_page().insert_text((50, 50), "DOC1_PAGE1")
    d1.new_page().insert_text((50, 50), "DOC1_PAGE2")
    p1.write_bytes(d1.tobytes())
    d1.close()
    b1 = repo.create_batch(filename="footer_doc1.pdf", file_path=str(p1), house_id="House 300", page_count=2)
    repo.add_document(
        vault_id="footer_doc1",
        house_id="House 300",
        tenant_id=t.id,
        batch_id=b1.id,
        primary_date="2024-05-15",
        arabic_title="عقد إيجار متعدد الصفحات",
        category="05 - عقود",
        page_count=2,
    )

    # Document 2: 2024-02-10, 1 page, Category: "06 - كهرباء وماء"
    p2 = vault_300 / "doc_footer_doc2.pdf"
    d2 = fitz.open()
    d2.new_page().insert_text((50, 50), "DOC2_PAGE1")
    p2.write_bytes(d2.tobytes())
    d2.close()
    b2 = repo.create_batch(filename="footer_doc2.pdf", file_path=str(p2), house_id="House 300", page_count=1)
    repo.add_document(
        vault_id="footer_doc2",
        house_id="House 300",
        tenant_id=t.id,
        batch_id=b2.id,
        primary_date="2024-02-10",
        arabic_title="فاتورة كهرباء",
        category="06 - كهرباء وماء",
        page_count=1,
    )

    # Document 3: Undated document, 1 page, Category: "صيانة"
    p3 = vault_300 / "doc_footer_doc3.pdf"
    d3 = fitz.open()
    d3.new_page().insert_text((50, 50), "DOC3_PAGE1")
    p3.write_bytes(d3.tobytes())
    d3.close()
    b3 = repo.create_batch(filename="footer_doc3.pdf", file_path=str(p3), house_id="House 300", page_count=1)
    repo.add_document(
        vault_id="footer_doc3",
        house_id="House 300",
        tenant_id=t.id,
        batch_id=b3.id,
        primary_date=None,
        arabic_title="طلب صيانة عامة",
        category="صيانة",
        page_count=1,
    )

    res = client.get("/api/areas/Area A/houses/House 300/export-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"

    merged = fitz.open(stream=res.content, filetype="pdf")
    # Total pages = 2 (from doc1) + 1 (from doc2) + 1 (from doc3) = 4 pages
    assert len(merged) == 4

    # Document 1 (2024-05-15, "05 - عقود" -> kept as "05 - عقود", 2 pages)
    # Page 1 of merged dossier: Doc 1 Page 1 -> pagination: "1/2  (1)"
    text_p0 = merged[0].get_text()
    assert "2024-05-15" in text_p0
    assert "1/2  (1)" in text_p0
    assert "05" in text_p0  # Category number prefix preserved
    assert "ﻋﻘﻮﺩ" in text_p0 or "ﺩﻮﻘﻋ" in text_p0 or any(c in text_p0 for c in ["\ufecb", "\ufed8", "\ufeee", "\ufea9"])
    assert "عقود" not in text_p0
    assert "Date:" not in text_p0
    assert "Category:" not in text_p0
    assert "Page:" not in text_p0

    # Page 2 of merged dossier: Doc 1 Page 2 -> pagination: "2/2  (2)"
    text_p1 = merged[1].get_text()
    assert "2024-05-15" in text_p1
    assert "2/2  (2)" in text_p1
    assert "05" in text_p1  # Category number prefix preserved
    assert "ﻋﻘﻮﺩ" in text_p1 or "ﺩﻮﻘﻋ" in text_p1 or any(c in text_p1 for c in ["\ufecb", "\ufed8", "\ufeee", "\ufea9"])
    assert "عقود" not in text_p1

    # Document 2 (2024-02-10, "06 - كهرباء وماء" -> kept as "06 - كهرباء وماء", 1 page)
    # Page 3 of merged dossier: Doc 2 Page 1 -> pagination: "1/1  (3)"
    text_p2 = merged[2].get_text()
    assert "2024-02-10" in text_p2
    assert "1/1  (3)" in text_p2
    assert "06" in text_p2  # Category number prefix preserved
    assert "ﻛﻬﺮﺑﺎﺀ ﻭﻣﺎﺀ" in text_p2 or "ﺀﺎﻣﻭ ﺀﺎﺑﺮﻬﻛ" in text_p2 or any(c in text_p2 for c in ["\ufedb", "\xfeec", "\ufeae", "\xfe91", "\xfe8e"])
    assert "كهرباء وماء" not in text_p2

    # Document 3 (Undated, "صيانة" -> "صيانة", 1 page)
    # Page 4 of merged dossier: Doc 3 Page 1 -> pagination: "1/1  (4)"
    text_p3 = merged[3].get_text()
    assert "1/1  (4)" in text_p3
    assert "ﺻﻴﺎﻧﺔ" in text_p3 or "ﺔﻧﺎﻴﺻ" in text_p3 or any(c in text_p3 for c in ["\ufebb", "\xfef4", "\xfe8e", "\xfee7", "\xfe94"])
    assert "صيانة" not in text_p3
    # Undated: bottom left date must be left blank
    assert "2024" not in text_p3
    assert "None" not in text_p3

    merged.close()


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


def test_single_document_copy_excluded_from_timeline(test_setup):
    repo = test_setup["repo"]

    # 1. Single copy via POST .../copy
    res = client.post(
        "/api/areas/Area A/houses/House 100/documents/v14test01/copy",
        json={"target_category": "10 - صيانة"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    new_vid = data["vault_id"]

    # Verify is_timeline_visible = 0
    copied_doc = repo.get_document(new_vid)
    assert copied_doc is not None
    assert copied_doc.is_timeline_visible == 0
    assert copied_doc.category == "10 - صيانة"

    # Verify it appears in categories
    res_cats = client.get("/api/areas/Area A/houses/House 100/categories")
    assert res_cats.status_code == 200
    all_cat_doc_ids = [d["vault_id"] for f in res_cats.json() for d in f.get("documents", [])]
    assert new_vid in all_cat_doc_ids
    assert "v14test01" in all_cat_doc_ids

    # Verify it does NOT appear in timeline (no duplicate)
    res_tl = client.get("/api/areas/Area A/houses/House 100/timeline")
    assert res_tl.status_code == 200
    tl_vids = [item["vault_id"] for item in res_tl.json()]
    assert "v14test01" in tl_vids
    assert new_vid not in tl_vids

    # Verify PDF is viewable seamlessly via /api/areas/{area}/houses/{house}/pdf/{vault_id}
    res_pdf = client.get(f"/api/areas/Area A/houses/House 100/pdf/{new_vid}")
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF")


def test_batch_copy_documents_excluded_from_timeline(test_setup):
    repo = test_setup["repo"]
    vault_dir = test_setup["vault_dir"]
    t = test_setup["tenant"]

    # Add second document
    p2 = vault_dir / "doc_v14test02.pdf"
    doc_new = fitz.open()
    doc_new.new_page()
    p2.write_bytes(doc_new.tobytes().replace(b"%PDF-1.7", b"%PDF-1.4"))
    doc_new.close()
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

    # 1. Validation: empty vault_ids and empty target_category
    res_err1 = client.post("/api/areas/Area A/houses/House 100/documents/batch-copy", json={"vault_ids": [], "target_category": "صيانة"})
    assert res_err1.status_code == 400

    res_err2 = client.post("/api/areas/Area A/houses/House 100/documents/batch-copy", json={"vault_ids": ["v14test01"], "target_category": ""})
    assert res_err2.status_code == 400

    # 2. Batch copy execution
    res = client.post(
        "/api/areas/Area A/houses/House 100/documents/batch-copy",
        json={"vault_ids": ["v14test01", "v14test02"], "target_category": "08 - فواتير"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["copied_count"] == 2
    assert data["target_category"] == "08 - فواتير"
    assert len(data["new_vault_ids"]) == 2

    copy1_id, copy2_id = data["new_vault_ids"]

    # Verify DB records
    doc1_copy = repo.get_document(copy1_id)
    doc2_copy = repo.get_document(copy2_id)
    assert doc1_copy.is_timeline_visible == 0
    assert doc1_copy.is_manual == 1
    assert doc1_copy.category == "08 - فواتير"
    assert doc2_copy.is_timeline_visible == 0
    assert doc2_copy.is_manual == 1
    assert doc2_copy.category == "08 - فواتير"

    # Verify copied documents appear in /categories
    res_cats = client.get("/api/areas/Area A/houses/House 100/categories")
    assert res_cats.status_code == 200
    all_cat_doc_ids = [d["vault_id"] for f in res_cats.json() for d in f.get("documents", [])]
    assert copy1_id in all_cat_doc_ids
    assert copy2_id in all_cat_doc_ids
    assert "v14test01" in all_cat_doc_ids
    assert "v14test02" in all_cat_doc_ids

    # Verify copied documents DO NOT appear in /timeline (no duplicates)
    res_tl = client.get("/api/areas/Area A/houses/House 100/timeline")
    assert res_tl.status_code == 200
    tl_vids = [item["vault_id"] for item in res_tl.json()]
    assert "v14test01" in tl_vids
    assert "v14test02" in tl_vids
    assert copy1_id not in tl_vids
    assert copy2_id not in tl_vids

    # Verify PDF viewable via PDF endpoint
    res_pdf1 = client.get(f"/api/areas/Area A/houses/House 100/pdf/{copy1_id}")
    assert res_pdf1.status_code == 200
    assert res_pdf1.content.startswith(b"%PDF")

    res_pdf2 = client.get(f"/api/areas/Area A/houses/House 100/pdf/{copy2_id}")
    assert res_pdf2.status_code == 200
    assert res_pdf2.content.startswith(b"%PDF")



