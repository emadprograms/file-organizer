import pytest
from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_list_houses_not_found(monkeypatch):
    from pathlib import Path
    class MockConfig:
        areas_root_path = "/does/not/exist/at/all"
    app.state.config = MockConfig()
    response = client.get("/api/houses")
    assert response.status_code == 404

def test_pdf_endpoint_invalid_id():
    class MockConfig:
        areas_root_path = "/tmp"
    app.state.config = MockConfig()
    response = client.get("/api/houses/123/pdf/invalid/id")
    assert response.status_code == 404

def test_get_tree_empty(monkeypatch):
    from pathlib import Path
    class MockConfig:
        areas_root_path = "/does/not/exist/at/all"
        area_mappings = {}
    app.state.config = MockConfig()
    response = client.get("/api/tree")
    assert response.status_code == 404

def test_get_tree_valid(tmp_path):
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    house_dir = areas_root / "123 - Test House"
    house_dir.mkdir()
    
    source_files = house_dir / ".source_files"
    source_files.mkdir()
    import json
    with open(source_files / "123_state.json", "w") as f:
        json.dump({"grouped_documents": [{"primary_tenant": "Ali"}]}, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"TestArea": "12"}
    app.state.config = MockConfig()

    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "TestArea"
    assert data[0]["type"] == "area"
    assert len(data[0]["children"]) == 1
    assert data[0]["children"][0]["name"] == "123 - Test House"
    assert data[0]["children"][0]["type"] == "house"
    assert len(data[0]["children"][0]["children"]) == 1
    assert data[0]["children"][0]["children"][0]["name"] == "Ali"
    assert data[0]["children"][0]["children"][0]["type"] == "tenant"
    
def test_search_endpoint(tmp_path):
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    house_dir = areas_root / "456 - Search House"
    house_dir.mkdir()
    
    source_files = house_dir / ".source_files"
    source_files.mkdir()
    import json
    with open(source_files / "456_state.json", "w") as f:
        json.dump({"grouped_documents": [{"primary_tenant": "Zaid Searcher"}]}, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"SearchArea": "45"}
    app.state.config = MockConfig()

    # Search for house
    res = client.get("/api/search?q=search house")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["type"] == "house"
    assert data[0]["id"] == "456 - Search House"
    
    # Search for tenant
    res2 = client.get("/api/search?q=zaid")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2) == 1
    assert data2[0]["type"] == "tenant"
    assert data2[0]["title"] == "Zaid Searcher"

    # Search empty
    res3 = client.get("/api/search?q=notfound")
    assert res3.status_code == 200
    assert len(res3.json()) == 0
