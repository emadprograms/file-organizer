import json
import pytest
from pathlib import Path

from src.presentation.export_static import build_tree_data, build_search_index, export_static_web
from src.core.config import AppConfig

def test_build_tree_data_and_search(tmp_path):
    areas_root = tmp_path / "areas"
    areas_root.mkdir()
    area_dir = areas_root / "Safra C"
    area_dir.mkdir()
    house_dir = area_dir / "1245 - Ali"
    house_dir.mkdir()
    sf = house_dir / ".source_files"
    sf.mkdir()

    state_content = {
        "grouped_documents": [
            {
                "vault_id": "v001",
                "primary_tenant": "Ali",
                "folder_path": "عقد الإيجار",
                "dates": ["2023-01-15"],
                "brief_arabic_title": "عقد إيجار علي"
            }
        ],
        "manifest": {
            "per_page": [
                {"tenant": "Ali", "target_folder": "عقد الإيجار"}
            ]
        }
    }
    with open(sf / "1245_state.json", "w", encoding="utf-8") as f:
        json.dump(state_content, f)

    report_content = {
        "documents": [
            {
                "vault_id": "v001",
                "brief_arabic_title": "عقد إيجار علي",
                "content": "نص العقد"
            }
        ]
    }
    with open(sf / "1245_report.json", "w", encoding="utf-8") as f:
        json.dump(report_content, f)

    tree = build_tree_data(areas_root)
    assert len(tree) == 1
    assert tree[0]["name"] == "Safra C"
    assert len(tree[0]["children"]) == 1
    house_node = tree[0]["children"][0]
    assert house_node["name"] == "1245 - Ali"
    assert house_node["current_tenant"] == "Ali"
    assert house_node["total_documents"] == 1
    assert "عقد الإيجار" in house_node["category_counts"]
    assert len(house_node["children"]) == 1
    assert house_node["children"][0]["name"] == "Ali"

    search = build_search_index(areas_root)
    assert len(search["houses"]) == 1
    assert search["houses"][0]["house_dir_name"] == "1245 - Ali"
    assert len(search["tenants"]) == 1
    assert search["tenants"][0]["tenant_name"] == "Ali"
    assert len(search["documents"]) == 1
    assert search["documents"][0]["vault_id"] == "v001"

    # Test full export
    class MockConfig:
        areas_root_path = str(areas_root)
        area_mappings = {}

    out_dir = tmp_path / "web_export"
    res = export_static_web(MockConfig(), output_dir=out_dir)
    assert res == 0
    assert (out_dir / "tree.json").exists()
    assert (out_dir / "search_index.json").exists()
    assert (out_dir / "web.config").exists()
    assert (out_dir / "index.html").exists()

    with open(out_dir / "web.config", "r", encoding="utf-8") as f:
        config_text = f.read()
    assert ".json" in config_text
    assert "application/json" in config_text
    assert "application/pdf" in config_text
