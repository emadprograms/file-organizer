import pytest
from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_list_houses_not_found():
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

def test_get_tree_empty():
    class MockConfig:
        areas_root_path = "/does/not/exist/at/all"
        area_mappings = {}
    app.state.config = MockConfig()
    response = client.get("/api/tree")
    assert response.status_code == 404

def test_get_tree_valid(tmp_path):
    """
    Real disk structure:
        areas_root/
            Safra C/          <- Area
                1245 - Ali/   <- House
                    .source_files/1245_state.json
    """
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    area_dir = areas_root / "Safra C"
    area_dir.mkdir()
    house_dir = area_dir / "1245 - Ali"
    house_dir.mkdir()
    sf = house_dir / ".source_files"
    sf.mkdir()
    import json
    with open(sf / "1245_state.json", "w") as f:
        json.dump({"grouped_documents": [{"primary_tenant": "Ali"}]}, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}
    app.state.config = MockConfig()

    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    area = data[0]
    assert area["name"] == "Safra C"
    assert area["type"] == "area"
    assert len(area["children"]) == 1
    house = area["children"][0]
    assert house["name"] == "1245 - Ali"
    assert house["type"] == "house"
    assert len(house["children"]) == 1
    assert house["children"][0]["name"] == "Ali"
    assert house["children"][0]["type"] == "tenant"


def test_timeline_uses_area_and_house(tmp_path):
    """
    GET /api/areas/{area_id}/houses/{house_id}/timeline
    Path: areas_root / area_id / house_id / .source_files / {num}_state.json
    """
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    (areas_root / "Safra C").mkdir()
    house_dir = areas_root / "Safra C" / "1245 - Ali"
    house_dir.mkdir()
    sf = house_dir / ".source_files"
    sf.mkdir()
    import json
    with open(sf / "1245_state.json", "w") as f:
        json.dump({"grouped_documents": [
            {"vault_id": "v1", "primary_tenant": "Ali", "dates": ["2020"], "brief_arabic_title": "Doc A"}
        ]}, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}
    app.state.config = MockConfig()

    res = client.get("/api/areas/Safra%20C/houses/1245%20-%20Ali/timeline")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["primary_tenant"] == "Ali"


def test_timeline_404_missing_state(tmp_path):
    """Returns 404 when state.json is absent."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    (areas_root / "Safra C").mkdir()
    (areas_root / "Safra C" / "1245 - Ali").mkdir()

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {}
    app.state.config = MockConfig()

    res = client.get("/api/areas/Safra%20C/houses/1245%20-%20Ali/timeline")
    assert res.status_code == 404


def test_categories_uses_area_and_house(tmp_path):
    """
    GET /api/areas/{area_id}/houses/{house_id}/categories
    Path: areas_root / area_id / house_id / .source_files / {num}_state.json
    """
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    (areas_root / "Safra C").mkdir()
    house_dir = areas_root / "Safra C" / "1245 - Ali"
    house_dir.mkdir()
    sf = house_dir / ".source_files"
    sf.mkdir()
    import json
    with open(sf / "1245_state.json", "w") as f:
        json.dump({"grouped_documents": [
            {"primary_tenant": "Ali", "folder_path": "عقد", "category": "عقد"},
            {"primary_tenant": "Ali", "folder_path": "عقد", "category": "عقد"},
            {"primary_tenant": "Bob", "folder_path": "إيصال", "category": "إيصال"},
        ]}, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}
    app.state.config = MockConfig()

    res = client.get("/api/areas/Safra%20C/houses/1245%20-%20Ali/categories")
    assert res.status_code == 200
    data = res.json()
    names = {d["name"] for d in data}
    assert any(c.get("tenant") == "Ali" and c["name"] == "عقد" for c in res.json()), res.json()
    assert any(c.get("tenant") == "Bob" and c["name"] == "إيصال" for c in res.json())


def test_search_endpoint(tmp_path):
    """areas_root / Safra C / 456 - Search House / .source_files / ..."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    area_dir = areas_root / "Safra C"
    area_dir.mkdir()
    house_dir = area_dir / "456 - Search House"
    house_dir.mkdir()
    sf = house_dir / ".source_files"
    sf.mkdir()
    import json
    with open(sf / "456_state.json", "w") as f:
        json.dump({"grouped_documents": [{"primary_tenant": "Zaid Searcher"}]}, f)
    with open(sf / "456_report.json", "w") as f:
        json.dump({"documents": [{
            "vault_id": "doc_abc",
            "brief_arabic_title": "Hidden Contract",
            "content": "some very specific hidden term inside the document text"
        }]}, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}
    app.state.config = MockConfig()

    res = client.get("/api/search?q=search house")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["type"] == "house"
    assert data[0]["id"] == "456 - Search House"

    res2 = client.get("/api/search?q=zaid")
    assert res2.status_code == 200
    assert res2.json()[0]["type"] == "tenant"
    assert res2.json()[0]["title"] == "Zaid Searcher"

    res_fuzzy = client.get("/api/search?q=zeid")
    assert res_fuzzy.status_code == 200
    assert res_fuzzy.json()[0]["title"] == "Zaid Searcher"

    res_doc = client.get("/api/search?q=hidden term")
    assert res_doc.status_code == 200
    doc_data = res_doc.json()
    assert len(doc_data) == 1
    assert doc_data[0]["type"] == "document"
    assert doc_data[0]["title"] == "Hidden Contract"
    assert "456 - Search House" in doc_data[0]["id"]

    res3 = client.get("/api/search?q=notfound")
    assert res3.status_code == 200
    assert len(res3.json()) == 0
