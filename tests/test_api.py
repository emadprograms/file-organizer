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
    """
    Real disk structure:
        areas_root/
            Safra C/          <- Area (child of areas_root, named in area_mappings)
                1245 - Ali/   <- House (child of Area)
                    .source_files/
                        1245_state.json
    areas_root children are Areas, NOT houses. Houses live one level deeper.
    """
    areas_root = tmp_path / "areas"
    areas_root.mkdir()

    # Area folder — name matches area_mappings key
    area_dir = areas_root / "Safra C"
    area_dir.mkdir()

    # House folder inside the Area
    house_dir = area_dir / "1245 - Ali"
    house_dir.mkdir()

    source_files = house_dir / ".source_files"
    source_files.mkdir()
    import json
    with open(source_files / "1245_state.json", "w") as f:
        json.dump({"grouped_documents": [{"primary_tenant": "Ali"}]}, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}
    app.state.config = MockConfig()

    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()

    # Must return exactly 1 Area node
    assert len(data) == 1
    area = data[0]
    assert area["name"] == "Safra C"
    assert area["type"] == "area"

    # Area must contain 1 House node
    assert len(area["children"]) == 1
    house = area["children"][0]
    assert house["name"] == "1245 - Ali"
    assert house["type"] == "house"

    # House must contain 1 Tenant node
    assert len(house["children"]) == 1
    tenant = house["children"][0]
    assert tenant["name"] == "Ali"
    assert tenant["type"] == "tenant"


def test_search_endpoint(tmp_path):
    """
    Real disk structure:
        areas_root/
            Safra C/               <- Area
                456 - Search House/ <- House
                    .source_files/
                        456_state.json
                        456_report.json
    """
    areas_root = tmp_path / "areas"
    areas_root.mkdir()

    area_dir = areas_root / "Safra C"
    area_dir.mkdir()

    house_dir = area_dir / "456 - Search House"
    house_dir.mkdir()

    source_files = house_dir / ".source_files"
    source_files.mkdir()
    import json
    with open(source_files / "456_state.json", "w") as f:
        json.dump({"grouped_documents": [{"primary_tenant": "Zaid Searcher"}]}, f)

    with open(source_files / "456_report.json", "w") as f:
        json.dump({
            "documents": [
                {
                    "vault_id": "doc_abc",
                    "brief_arabic_title": "Hidden Contract",
                    "content": "some very specific hidden term inside the document text"
                }
            ]
        }, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}
    app.state.config = MockConfig()

    # Search for house by name
    res = client.get("/api/search?q=search house")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["type"] == "house"
    assert data[0]["id"] == "456 - Search House"

    # Search for tenant exact
    res2 = client.get("/api/search?q=zaid")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2) == 1
    assert data2[0]["type"] == "tenant"
    assert data2[0]["title"] == "Zaid Searcher"

    # Search for tenant fuzzy typo (zaid -> zeid)
    res_fuzzy = client.get("/api/search?q=zeid")
    assert res_fuzzy.status_code == 200
    data_fuzzy = res_fuzzy.json()
    assert len(data_fuzzy) == 1
    assert data_fuzzy[0]["type"] == "tenant"
    assert data_fuzzy[0]["title"] == "Zaid Searcher"

    # Search for document content
    res_doc = client.get("/api/search?q=hidden term")
    assert res_doc.status_code == 200
    data_doc = res_doc.json()
    assert len(data_doc) == 1
    assert data_doc[0]["type"] == "document"
    assert data_doc[0]["title"] == "Hidden Contract"
    assert "456 - Search House" in data_doc[0]["id"]

    # Search empty — no results
    res3 = client.get("/api/search?q=notfound")
    assert res3.status_code == 200
    assert len(res3.json()) == 0
