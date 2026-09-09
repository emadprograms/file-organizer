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
    db_file = tmp_path / "tenant_test.db"
    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)

    # Area & House
    repo.add_area(area_id="Safra C", code="SAF C")
    repo.add_house(house_id="514", area_id="Safra C")

    # Initial Tenants: Tenant A covering 2020 to 2022
    tA = repo.add_tenant(house_id="514", name="محمد مبارك الشمري", start_date="2020-01-01", end_date="2022-12-31")

    # Batch
    b1 = repo.create_batch(house_id="514", filename="batch_01.pdf", file_path="batches/batch_01.pdf", page_count=3)

    # Doc 1: Unnamed utility bill dated 2021-06-15 (initially under Tenant A)
    doc1 = repo.add_document(
        vault_id="doc_unnamed_bill",
        house_id="514",
        tenant_id=tA.id,
        batch_id=b1.id,
        primary_date="2021-06-15",
        arabic_title="فاتورة كهرباء",
        category="كهرباء وماء",
        page_count=1
    )

    # Doc 2: Letter dated 2021-06-20, BUT explicitly addressed to Tenant A!
    doc2 = repo.add_document(
        vault_id="doc_named_letter",
        house_id="514",
        tenant_id=tA.id,
        batch_id=b1.id,
        primary_date="2021-06-20",
        arabic_title="خطاب موجه لمحمد مبارك",
        category="رسائل",
        page_count=1
    )

    repo.add_pages_bulk([
        {
            "batch_id": b1.id,
            "page_number": 1,
            "house_id": "514",
            "vault_id": "doc_unnamed_bill",
            "tenant_id": tA.id,
            "resolved_date": "2021-06-15",
            "expected_tenant_name": None,  # <--- Unnamed!
        },
        {
            "batch_id": b1.id,
            "page_number": 2,
            "house_id": "514",
            "vault_id": "doc_named_letter",
            "tenant_id": tA.id,
            "resolved_date": "2021-06-20",
            "expected_tenant_name": "محمد مبارك الشمري",  # <--- Explicit previous tenant name!
        }
    ])

    app.state.db_path = str(db_file)
    app.state.repo = repo
    app.state.config = AppConfig(inbox_path=str(tmp_path / "inbox"), areas_root_path=str(tmp_path), db_path=str(db_file))

    yield repo, tA, b1, doc1, doc2


def test_get_house_tenants(db_setup):
    repo, tA, _, _, _ = db_setup
    res = client.get("/api/areas/Safra C/houses/514/tenants")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "محمد مبارك الشمري"
    assert data[0]["start_date"] == "2020-01-01"
    assert data[0]["end_date"] == "2022-12-31"


def test_bulk_update_and_reallocation_priority(db_setup):
    repo, tA, b1, doc1, doc2 = db_setup

    # User adjusts timeline:
    # Tenant A now ended on 2020-12-31
    # New Tenant B starts on 2021-01-01
    payload = {
        "tenants": [
            {
                "id": tA.id,
                "name": "محمد مبارك الشمري",
                "start_date": "2020-01-01",
                "end_date": "2020-12-31"
            },
            {
                "name": "سعد علي العتيبي",
                "start_date": "2021-01-01",
                "end_date": None
            }
        ],
        "reallocate": True
    }

    res = client.post("/api/areas/Safra C/houses/514/tenants", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "success"
    assert res_data["tenants_count"] == 2

    # Verify tenants table
    tenants = repo.list_tenants_by_house("514")
    assert len(tenants) == 2
    tB = [t for t in tenants if t.id != tA.id][0]
    assert tB.name == "سعد علي العتيبي"

    # CRITICAL CHECK 1: Doc 1 (unnamed utility bill in 2021-06-15) MUST be reallocated to Tenant B!
    updated_doc1 = repo.get_document("doc_unnamed_bill")
    assert updated_doc1.tenant_id == tB.id

    # CRITICAL CHECK 2: Doc 2 (letter in 2021-06-20 explicitly named to Tenant A) MUST STAY WITH Tenant A!
    updated_doc2 = repo.get_document("doc_named_letter")
    assert updated_doc2.tenant_id == tA.id


def test_manual_document_tenant_patch(db_setup):
    repo, tA, _, doc1, _ = db_setup

    # Add another tenant
    tC = repo.add_tenant(house_id="514", name="فهد المطيري", start_date="2023-01-01", end_date=None)

    # Manually patch doc1 to belong to Tenant C
    res = client.patch(
        "/api/areas/Safra C/houses/514/documents/doc_unnamed_bill/tenant",
        json={"tenant_id": tC.id}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["tenant_id"] == tC.id

    updated_doc = repo.get_document("doc_unnamed_bill")
    assert updated_doc.tenant_id == tC.id


def test_tenant_bulk_update_nonexistent_house_404(db_setup):
    res = client.post(
        "/api/areas/Safra C/houses/999_nonexistent/tenants",
        json={"tenants": [{"name": "Ghost", "start_date": "2020-01-01"}]}
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "House not found."


def test_reallocate_endpoint_direct(db_setup):
    res = client.post("/api/areas/Safra C/houses/514/reallocate")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "reallocated_count" in data
    assert data["total_documents"] == 2


def test_manual_override_nonexistent_doc_404(db_setup):
    repo, tA, _, _, _ = db_setup
    res = client.patch(
        "/api/areas/Safra C/houses/514/documents/nonexistent_vault_id/tenant",
        json={"tenant_id": tA.id}
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Document not found."


def test_manual_override_invalid_tenant_404(db_setup):
    res = client.patch(
        "/api/areas/Safra C/houses/514/documents/doc_unnamed_bill/tenant",
        json={"tenant_id": 999999}
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Tenant not found."

