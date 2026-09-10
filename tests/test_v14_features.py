import pytest
import io
import zipfile
from pathlib import Path
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
    
    # Write sample pdf
    sample_pdf = vault_dir / "doc_v14test01.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4 sample content for house 100")
    
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
        "vault_dir": vault_dir
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
