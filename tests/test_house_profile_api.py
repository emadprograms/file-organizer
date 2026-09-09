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
def db_profile_setup(tmp_path):
    db_file = tmp_path / "profile_test.db"
    conn = get_db_connection(str(db_file))
    init_db(conn)
    repo = Repository(conn)

    # Area & House
    repo.add_area(area_id="Safra D", code="SAF D")
    repo.add_house(house_id="500", area_id="Safra D")

    # Past Tenant
    t_past = repo.add_tenant(house_id="500", name="أحمد عبدالله المطوع", start_date="2017-01-01", end_date="2019-12-31")
    # Active Tenant
    t_active = repo.add_tenant(house_id="500", name="فواز خليل الطارش", start_date="2020-01-01", end_date=None)

    # Batch
    b1 = repo.create_batch(house_id="500", filename="batch_01.pdf", file_path="batches/batch_01.pdf", page_count=5)
    b2 = repo.create_batch(house_id="500", filename="batch_02.pdf", file_path="batches/batch_02.pdf", page_count=10)

    # Documents for Past Tenant
    repo.add_document(
        vault_id="v500_past_1",
        house_id="500",
        tenant_id=t_past.id,
        batch_id=b1.id,
        primary_date="2017-03-15",
        arabic_title="عقد إيجار قديم",
        category="01 - عقود الإيجار",
        page_count=3
    )

    # Documents for Active Tenant
    repo.add_document(
        vault_id="v500_active_1",
        house_id="500",
        tenant_id=t_active.id,
        batch_id=b2.id,
        primary_date="2020-02-10",
        arabic_title="عقد إيجار فواز",
        category="01 - عقود الإيجار",
        page_count=4
    )
    repo.add_document(
        vault_id="v500_active_2",
        house_id="500",
        tenant_id=t_active.id,
        batch_id=b2.id,
        primary_date="2023-08-01",
        arabic_title="فاتورة كهرباء حديثة",
        category="06 - كهرباء وماء",
        page_count=2
    )

    app.state.db_path = str(db_file)
    app.state.repo = repo
    app.state.config = AppConfig(
        database_path=str(db_file),
        areas_root_path=str(tmp_path / "areas"),
        inbox_path=str(tmp_path / "inbox"),
    )

    return repo


def test_get_house_profile_endpoint(db_profile_setup):
    res = client.get("/api/areas/Safra%20D/houses/500/profile")
    assert res.status_code == 200
    data = res.json()

    assert data["house_id"] == "500"
    assert data["area_id"] == "Safra D"

    # Verify tenants (active tenant sorted first)
    tenants = data["tenants"]
    assert len(tenants) == 2
    
    active = tenants[0]
    assert active["name"] == "فواز خليل الطارش"
    assert active["is_active"] is True
    assert "مستمر" in active["duration_str_ar"]
    assert active["document_count"] == 2
    assert active["category_count"] == 2

    past = tenants[1]
    assert past["name"] == "أحمد عبدالله المطوع"
    assert past["is_active"] is False
    assert "2017 – 2019" in past["duration_str_ar"]
    assert past["document_count"] == 1
    assert past["category_count"] == 1

    # Verify archive profile
    archive = data["archive"]
    assert archive["total_documents"] == 3
    assert archive["batch_count"] == 2
    assert archive["oldest_date"] == "2017-03-15"
    assert archive["newest_date"] == "2023-08-01"
    assert "من 2017 إلى 2023" in archive["timespan_str_ar"]
    assert len(archive["categories"]) >= 2


def test_get_house_profile_not_found(db_profile_setup):
    res = client.get("/api/areas/Safra%20D/houses/999_nonexistent/profile")
    assert res.status_code == 404

