import pytest
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
    db_file = tmp_path / "doc_test.db"
    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)

    # Setup Area and House
    repo.add_area(area_id="Safra C", code="SAF C")
    repo.add_house(house_id="514", area_id="Safra C")
    repo.add_house(house_id="515", area_id="Safra C")

    # Tenants for 514
    t1 = repo.add_tenant(house_id="514", name="محمد مبارك", start_date="2020-01-01", end_date="2022-12-31")
    t2 = repo.add_tenant(house_id="514", name="خالد العتيبي", start_date="2023-01-01", end_date="None")

    # Tenant for 515 (different house)
    t_other = repo.add_tenant(house_id="515", name="سلطان الدوسري", start_date="2020-01-01", end_date="None")

    # Batch in 514
    b1 = repo.create_batch(house_id="514", filename="batch_01.pdf", file_path="batches/batch_01.pdf", page_count=2)

    # Document 1 (2021 date, under Tenant 1)
    doc1 = repo.add_document(
        vault_id="v_doc_001",
        house_id="514",
        tenant_id=t1.id,
        batch_id=b1.id,
        primary_date="2021-05-10",
        arabic_title="فاتورة قديمة",
        category="كهرباء وماء",
        page_count=1,
        is_manual=0
    )

    # Vault directory and mock PDF file
    house_vault_dir = tmp_path / "Safra C" / "514" / "vault"
    house_vault_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = house_vault_dir / "doc_v_doc_001.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock pdf content")

    app.state.repo = repo
    app.state.db_path = str(db_file)
    app.state.config = AppConfig(areas_root_path=str(tmp_path), inbox_path=str(tmp_path / "inbox"))

    return {
        "repo": repo,
        "conn": conn,
        "t1": t1,
        "t2": t2,
        "t_other": t_other,
        "doc1": doc1,
        "tmp_path": tmp_path,
    }


def test_update_document_title_and_standard_category(db_setup):
    res = client.patch(
        "/api/areas/Safra C/houses/514/documents/v_doc_001",
        json={
            "arabic_title": "عقد إيجار محدث",
            "category": "عقود",
        }
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "success"
    assert data["arabic_title"] == "عقد إيجار محدث"
    assert data["category"] == "05 - عقود"
    assert data["is_manual"] == 1


def test_custom_folder_sequential_numbering(db_setup):
    # First custom folder: should get 14
    res1 = client.patch(
        "/api/areas/Safra C/houses/514/documents/v_doc_001",
        json={"category": "مستندات بنكية"}
    )
    assert res1.status_code == 200
    assert res1.json()["category"] == "14 - مستندات بنكية"

    # Add a second document
    repo = db_setup["repo"]
    doc2 = repo.add_document(
        vault_id="v_doc_002",
        house_id="514",
        tenant_id=db_setup["t1"].id,
        batch_id=1,
        primary_date="2021-06-01",
        arabic_title="شهادة راتب",
        category="14 - مستندات بنكية"
    )

    # Move doc2 to another new custom folder: should get 15
    res2 = client.patch(
        "/api/areas/Safra C/houses/514/documents/v_doc_002",
        json={"category": "تصاريح رسمية"}
    )
    assert res2.status_code == 200
    assert res2.json()["category"] == "15 - تصاريح رسمية"

    # Move doc1 back to "مستندات بنكية": should reuse 14
    res3 = client.patch(
        "/api/areas/Safra C/houses/514/documents/v_doc_001",
        json={"category": "مستندات بنكية"}
    )
    assert res3.status_code == 200
    assert res3.json()["category"] == "14 - مستندات بنكية"


def test_move_document_between_tenants_in_same_house(db_setup):
    t2 = db_setup["t2"]
    res = client.patch(
        "/api/areas/Safra C/houses/514/documents/v_doc_001",
        json={"tenant_id": t2.id}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["tenant_id"] == t2.id
    assert data["tenant_name"] == t2.name
    assert data["is_manual"] == 1


def test_reject_move_document_to_tenant_outside_house(db_setup):
    t_other = db_setup["t_other"]
    res = client.patch(
        "/api/areas/Safra C/houses/514/documents/v_doc_001",
        json={"tenant_id": t_other.id}
    )
    assert res.status_code == 400
    assert "different house" in res.text or "outside this house" in res.text


def test_permanent_manual_lock_blocks_reallocation(db_setup):
    t2 = db_setup["t2"]
    # Manually assign doc1 (dated 2021) to Tenant 2 (2023+). Since is_manual=1, it is locked.
    patch_res = client.patch(
        "/api/areas/Safra C/houses/514/documents/v_doc_001",
        json={"tenant_id": t2.id}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_manual"] == 1

    # Trigger automatic house reallocation
    realloc_res = client.post("/api/areas/Safra C/houses/514/reallocate")
    assert realloc_res.status_code == 200

    # Verify doc1 is STILL assigned to Tenant 2!
    repo = db_setup["repo"]
    doc = repo.get_document("v_doc_001")
    assert doc.tenant_id == t2.id
    assert doc.is_manual == 1


def test_reset_manual_lock_restores_automatic_behavior(db_setup):
    t1 = db_setup["t1"]
    t2 = db_setup["t2"]

    # Manually move to t2
    client.patch("/api/areas/Safra C/houses/514/documents/v_doc_001", json={"tenant_id": t2.id})

    # Reset lock
    reset_res = client.post("/api/areas/Safra C/houses/514/documents/v_doc_001/reset-lock")
    assert reset_res.status_code == 200
    assert reset_res.json()["is_manual"] == 0

    # Since date is 2021-05-10 and t1 covers 2020-2022, reallocate in reset-lock restores it to t1!
    repo = db_setup["repo"]
    doc = repo.get_document("v_doc_001")
    assert doc.tenant_id == t1.id
    assert doc.is_manual == 0


def test_copy_document_creates_duplicate_and_preserves_original(db_setup):
    res = client.post(
        "/api/areas/Safra C/houses/514/documents/v_doc_001/copy",
        json={
            "target_category": "02 - بيانات شخصية",
            "target_title": "نسخة من المستند"
        }
    )
    assert res.status_code == 200
    data = res.json()
    new_vault_id = data["vault_id"]
    assert new_vault_id != "v_doc_001"
    assert data["category"] == "02 - بيانات شخصية"
    assert data["arabic_title"] == "نسخة من المستند"
    assert data["is_manual"] == 1

    # Verify original document remains untouched
    repo = db_setup["repo"]
    orig_doc = repo.get_document("v_doc_001")
    assert orig_doc.category == "06 - كهرباء وماء" or "كهرباء وماء" in orig_doc.category

    # Verify physical file on disk was duplicated
    tmp_path = db_setup["tmp_path"]
    copy_pdf = tmp_path / "Safra C" / "514" / "vault" / f"doc_{new_vault_id}.pdf"
    assert copy_pdf.exists()
    assert copy_pdf.read_bytes() == b"%PDF-1.4 mock pdf content"
