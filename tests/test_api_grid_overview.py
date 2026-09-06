import pytest
import json
from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_get_tree_house_overview_metrics(tmp_path):
    """Verify get_tree extracts house-level metrics, tenure duration, and category counts."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    area_dir = areas_root / "Safra C"
    area_dir.mkdir()

    # House 1: short tenure (< 5 years)
    h1 = area_dir / "101 - ShortStay"
    h1.mkdir()
    sf1 = h1 / ".source_files"
    sf1.mkdir()
    with open(sf1 / "101_state.json", "w") as f:
        json.dump({
            "manifest": {
                "per_page": [
                    {"tenant": "ShortTenant", "target_folder": "present"}
                ]
            },
            "grouped_documents": [
                {"primary_tenant": "ShortTenant", "folder_path": "02 - عقد الإيجار", "dates": ["2024-01-01"], "vault_id": "v1"},
                {"primary_tenant": "ShortTenant", "folder_path": "06 - سند قبض", "dates": ["2024-06-01"], "vault_id": "v2"}
            ]
        }, f)

    # House 2: medium tenure (5-10 years)
    h2 = area_dir / "102 - MediumStay"
    h2.mkdir()
    sf2 = h2 / ".source_files"
    sf2.mkdir()
    with open(sf2 / "102_state.json", "w") as f:
        json.dump({
            "manifest": {
                "per_page": [
                    {"tenant": "MedTenant", "target_folder": "الآن"}
                ]
            },
            "grouped_documents": [
                {"primary_tenant": "MedTenant", "folder_path": "عقد الإيجار", "dates": ["2018-05-10"], "vault_id": "v3"},
                {"primary_tenant": "MedTenant", "folder_path": "بيانات شخصية", "dates": ["2019-01-01"], "vault_id": "v4"}
            ]
        }, f)

    # House 3: long tenure (> 10 years)
    h3 = area_dir / "103 - LongStay"
    h3.mkdir()
    sf3 = h3 / ".source_files"
    sf3.mkdir()
    with open(sf3 / "103_state.json", "w") as f:
        json.dump({
            "manifest": {
                "per_page": [
                    {"tenant": "LongTenant", "target_folder": "present"}
                ]
            },
            "grouped_documents": [
                {"primary_tenant": "LongTenant", "folder_path": "عقد الإيجار", "dates": ["2010-01-01"], "vault_id": "v5"}
            ]
        }, f)

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}

    app.state.config = MockConfig()

    res = client.get("/api/tree")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    area = data[0]
    assert area["name"] == "Safra C"
    houses = area["children"]
    assert len(houses) == 3

    # House 1 (<5 years -> short)
    house1 = next(h for h in houses if "101" in h["id"])
    assert house1["current_tenant"] == "ShortTenant"
    assert house1["duration_category"] == "short"
    assert house1["total_documents"] == 2
    assert "عقد الإيجار" in house1["category_counts"]
    assert "سند قبض" in house1["category_counts"]

    # House 2 (5-10 years -> medium)
    house2 = next(h for h in houses if "102" in h["id"])
    assert house2["current_tenant"] == "MedTenant"
    assert house2["duration_category"] == "medium"
    assert house2["total_documents"] == 2

    # House 3 (>10 years -> long)
    house3 = next(h for h in houses if "103" in h["id"])
    assert house3["current_tenant"] == "LongTenant"
    assert house3["duration_category"] == "long"
    assert house3["total_documents"] == 1


def test_get_tree_ignores_hidden_directories(tmp_path):
    """Ensure get_tree ignores system hidden directories like .Spotlight-V100, .Trashes, .DS_Store."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    (areas_root / "Safra C").mkdir()
    (areas_root / ".Spotlight-V100").mkdir()
    (areas_root / ".Trashes").mkdir()
    (areas_root / ".DS_Store").write_text("dummy")

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}

    app.state.config = MockConfig()
    import src.api.routes as routes
    routes.clear_tree_cache() if hasattr(routes, "clear_tree_cache") else None

    res = client.get("/api/tree")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "Safra C"


def test_get_tree_unorganized_houses_no_hang(tmp_path):
    """Ensure get_tree processes unorganized houses (without .source_files) rapidly without hanging or deep globbing."""
    import time
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    area_dir = areas_root / "Safra D"
    area_dir.mkdir()

    # Create 20 unorganized houses with nested subfolders
    for i in range(950, 970):
        h_dir = area_dir / str(i)
        h_dir.mkdir()
        sub = h_dir / "RandomFolder" / "SubFolder"
        sub.mkdir(parents=True)
        (sub / f"{i}.pdf").write_bytes(b"%PDF-1.4 dummy")

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra D": "SAF D"}

    app.state.config = MockConfig()
    import src.api.routes as routes
    routes.clear_tree_cache() if hasattr(routes, "clear_tree_cache") else None

    t0 = time.time()
    res = client.get("/api/tree")
    elapsed = time.time() - t0

    assert res.status_code == 200
    assert elapsed < 1.0, f"get_tree took {elapsed:.2f}s, expected < 1.0s"
    data = res.json()
    assert len(data) == 1
    area = data[0]
    assert area["name"] == "Safra D"
    assert len(area["children"]) == 20


def test_get_tree_caching(tmp_path):
    """Ensure get_tree caches the result and serves subsequent calls from cache."""
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    (areas_root / "Safra C").mkdir()

    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {"Safra C": "SAF C"}

    app.state.config = MockConfig()
    import src.api.routes as routes
    routes.clear_tree_cache() if hasattr(routes, "clear_tree_cache") else None

    res1 = client.get("/api/tree")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1) == 1

    # Modify disk directly without clearing cache
    (areas_root / "Safra C" / "NewHouse").mkdir()

    res2 = client.get("/api/tree")
    assert res2.status_code == 200
    data2 = res2.json()
    # Should be served from cache, so NewHouse is not in data2
    assert len(data2[0]["children"]) == len(data1[0]["children"])

    # Now clear cache and verify it reflects the update
    if hasattr(routes, "clear_tree_cache"):
        routes.clear_tree_cache()
        res3 = client.get("/api/tree")
        assert res3.status_code == 200
        data3 = res3.json()
        assert len(data3[0]["children"]) == 1

