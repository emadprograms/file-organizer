import json
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

from src.core.config import AppConfig

logger = logging.getLogger(f"file_organizer.{__name__}")

def _house_sort_key(entry: Path) -> tuple[int, str]:
    match = re.search(r'(\d+)', entry.name)
    num = int(match.group(1)) if match else 999999999
    return (num, entry.name)

def _get_document_groups(state_data: dict) -> list[dict]:
    routed = state_data.get("routed_documents", [])
    if isinstance(routed, list) and routed and routed[0].get("vault_id"):
        return routed
    grouped = state_data.get("grouped_documents", [])
    if isinstance(grouped, list) and grouped and grouped[0].get("vault_id"):
        return grouped
    if isinstance(routed, list) and routed:
        return routed
    if isinstance(grouped, list) and grouped:
        return grouped
    return []

def build_tree_data(areas_root: Path) -> list[dict[str, Any]]:
    """Build the tree hierarchy matching the API /api/tree schema."""
    if not areas_root.exists():
        return []

    areas: dict[str, dict[str, Any]] = {}

    for area_entry in sorted(areas_root.iterdir()):
        if not area_entry.is_dir() or area_entry.name.startswith("."):
            continue

        area_name = area_entry.name

        if area_name not in areas:
            areas[area_name] = {
                "id": f"area_{area_name}",
                "name": area_name,
                "type": "area",
                "children": []
            }

        # Walk house folders inside this area
        for house_entry in sorted(area_entry.iterdir(), key=_house_sort_key):
            if not house_entry.is_dir() or house_entry.name.startswith("."):
                continue

            house_dir_name = house_entry.name
            house_id = house_dir_name.split(" - ")[0] if " - " in house_dir_name else house_dir_name

            house_node: dict[str, Any] = {
                "id": house_dir_name,
                "name": house_dir_name,
                "type": "house",
                "children": []
            }

            report_path = house_entry / ".source_files" / f"{house_id}_report.json"
            state_path = house_entry / ".source_files" / f"{house_id}_state.json"
            tenants_with_dates: dict[str, set[int]] = {}
            tenant_is_present: dict[str, bool] = {}
            category_counts: dict[str, int] = {}
            total_docs = 0

            if report_path.exists():
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        rep_data = json.load(f)
                    doc_list = rep_data if isinstance(rep_data, list) else rep_data.get("documents", [])
                    if isinstance(doc_list, list):
                        total_docs = len(doc_list)
                        for doc in doc_list:
                            cat_raw = doc.get("folder_path") or doc.get("category")
                            if cat_raw:
                                clean_cat = re.sub(r'^\d+\s*-\s*', '', cat_raw)
                                category_counts[clean_cat] = category_counts.get(clean_cat, 0) + 1
                            tenant = doc.get("primary_tenant") or doc.get("tenant")
                            if tenant:
                                if tenant not in tenants_with_dates:
                                    tenants_with_dates[tenant] = set()
                                for d in doc.get("dates", []):
                                    if d and d != "NONE":
                                        year_match = re.search(r'(\d{4})', d)
                                        if year_match:
                                            tenants_with_dates[tenant].add(int(year_match.group(1)))
                                for sc in doc.get("shortcuts", []):
                                    if "الآن" in sc or "present" in sc.lower():
                                        tenant_is_present[tenant] = True
                except Exception as e:
                    logger.warning(f"Error reading report file {report_path}: {e}")

            if not tenants_with_dates and state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)

                    per_page = state_data.get("manifest", {}).get("per_page", [])
                    for doc in per_page:
                        tenant = doc.get("tenant")
                        if tenant:
                            tf = doc.get("target_folder", "")
                            if "الآن" in tf or "present" in tf.lower():
                                tenant_is_present[tenant] = True

                    doc_groups = _get_document_groups(state_data)
                    if not total_docs:
                        total_docs = len(doc_groups)
                    for group in doc_groups:
                        cat_raw = group.get("folder_path") or group.get("category")
                        if cat_raw:
                            clean_cat = re.sub(r'^\d+\s*-\s*', '', cat_raw)
                            category_counts[clean_cat] = category_counts.get(clean_cat, 0) + 1
                        tenant = group.get("primary_tenant")
                        if tenant:
                            if tenant not in tenants_with_dates:
                                tenants_with_dates[tenant] = set()

                            doc_dates = group.get("dates", [])
                            for d in doc_dates:
                                if d and d != "NONE":
                                    year_match = re.search(r'(\d{4})', d)
                                    if year_match:
                                        tenants_with_dates[tenant].add(int(year_match.group(1)))
                except Exception as e:
                    logger.warning(f"Error reading state file {state_path}: {e}")

            if not tenants_with_dates and house_entry.exists():
                # Fast fallback: examine directory names directly without recursive globbing
                for tenant_dir in house_entry.iterdir():
                    if tenant_dir.is_dir() and not tenant_dir.name.startswith("."):
                        m = re.match(r'^(.*?)\s*‎?\((.*?)\)‎?$', tenant_dir.name)
                        t_name = m.group(1).strip() if m else tenant_dir.name
                        if "الآن" in tenant_dir.name or "present" in tenant_dir.name.lower():
                            tenant_is_present[t_name] = True
                        if t_name not in tenants_with_dates:
                            tenants_with_dates[t_name] = set()
                        if m and m.group(2):
                            year_matches = re.findall(r'(\d{4})', m.group(2))
                            for y in year_matches:
                                tenants_with_dates[t_name].add(int(y))

            current_year = datetime.now().year
            for t, years in sorted(tenants_with_dates.items()):
                subtitle = None
                duration_category = None
                if years:
                    min_val = min(years)
                    max_val = max(years)

                    actual_max = current_year if tenant_is_present.get(t) else max_val
                    duration = actual_max - min_val
                    if duration < 5:
                        duration_category = "short"
                    elif duration < 10:
                        duration_category = "medium"
                    else:
                        duration_category = "long"

                    if tenant_is_present.get(t):
                        subtitle = f"{min_val} - Present"
                    elif min_val == max_val:
                        subtitle = f"{min_val}"
                    else:
                        subtitle = f"{min_val} - {max_val}"

                house_node["children"].append({
                    "id": f"{house_dir_name}_{t}",
                    "name": t,
                    "subtitle": subtitle,
                    "duration_category": duration_category,
                    "type": "tenant"
                })

            # Determine active tenant and house-level metrics for grid view
            active_tenant = None
            for t in tenants_with_dates.keys():
                if tenant_is_present.get(t):
                    active_tenant = t
                    break

            if not active_tenant and " - " in house_dir_name:
                cand = house_dir_name.split(" - ", 1)[1].strip()
                if cand in tenants_with_dates:
                    active_tenant = cand

            if not active_tenant and len(tenants_with_dates) == 1:
                active_tenant = next(iter(tenants_with_dates.keys()))

            house_duration_cat = None
            house_sub = None

            if active_tenant and tenants_with_dates.get(active_tenant):
                years = tenants_with_dates[active_tenant]
                min_val = min(years)
                max_val = max(years)
                is_pres = tenant_is_present.get(active_tenant, False)
                if is_pres or active_tenant == (house_dir_name.split(" - ", 1)[1].strip() if " - " in house_dir_name else ""):
                    duration = current_year - min_val
                    if duration < 5:
                        house_duration_cat = "short"
                    elif duration < 10:
                        house_duration_cat = "medium"
                    else:
                        house_duration_cat = "long"
                    house_sub = f"Since {min_val} ({duration}y)"
                elif min_val == max_val:
                    house_sub = f"{min_val}"
                else:
                    house_sub = f"{min_val} - {max_val}"

            house_node["current_tenant"] = active_tenant
            house_node["duration_category"] = house_duration_cat
            house_node["subtitle"] = house_sub
            house_node["total_documents"] = total_docs
            house_node["category_counts"] = category_counts

            areas[area_name]["children"].append(house_node)

    return list(areas.values())

def build_search_index(areas_root: Path) -> dict[str, list[dict[str, Any]]]:
    """Build the search index matching the API /api/search schema."""
    houses: list[dict[str, Any]] = []
    tenants: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    if not areas_root.exists():
        return {"houses": [], "tenants": [], "documents": []}

    for area_entry in sorted(areas_root.iterdir()):
        if not area_entry.is_dir() or area_entry.name.startswith("."):
            continue

        area_name = area_entry.name

        for house_entry in sorted(area_entry.iterdir(), key=_house_sort_key):
            if not house_entry.is_dir() or house_entry.name.startswith("."):
                continue

            house_dir_name = house_entry.name
            house_id = house_dir_name.split(" - ")[0] if " - " in house_dir_name else house_dir_name

            houses.append({
                "house_dir_name": house_dir_name,
                "area_name": area_name
            })

            state_path = house_entry / ".source_files" / f"{house_id}_state.json"
            if state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        state_data = json.load(f)

                    house_tenants: set[str] = set()
                    for group in _get_document_groups(state_data):
                        tenant = group.get("primary_tenant")
                        if tenant:
                            house_tenants.add(tenant)

                    for t in house_tenants:
                        tenants.append({
                            "tenant_name": t,
                            "house_dir_name": house_dir_name,
                            "area_name": area_name
                        })
                except Exception as e:
                    logger.warning(f"Error reading state file for search in {state_path}: {e}")

            report_path = house_entry / ".source_files" / f"{house_id}_report.json"
            if report_path.exists():
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)

                    for doc in report_data.get("documents", []):
                        documents.append({
                            "content": doc.get("content", "").lower(),
                            "title_field": doc.get("brief_arabic_title", "").lower(),
                            "vault_id": doc.get("vault_id", ""),
                            "doc_title": doc.get("brief_arabic_title", "Document"),
                            "house_dir_name": house_dir_name,
                            "area_name": area_name
                        })
                except Exception as e:
                    logger.warning(f"Error reading report file for search in {report_path}: {e}")

    return {
        "houses": houses,
        "tenants": tenants,
        "documents": documents
    }

WEB_CONFIG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <staticContent>
            <remove fileExtension=".json" />
            <mimeMap fileExtension=".json" mimeType="application/json" />
            <remove fileExtension=".pdf" />
            <mimeMap fileExtension=".pdf" mimeType="application/pdf" />
        </staticContent>
        <defaultDocument>
            <files>
                <clear />
                <add value="index.html" />
            </files>
        </defaultDocument>
        <httpProtocol>
            <customHeaders>
                <add name="Access-Control-Allow-Origin" value="*" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>
"""

def export_static_web(config: AppConfig, output_dir: Path | None = None) -> int:
    """Export static web files (tree.json, search_index.json, web.config, index.html) to output_dir."""
    areas_root = Path(config.areas_root_path).resolve()
    target_dir = output_dir.resolve() if output_dir else areas_root

    if not areas_root.exists():
        logger.error(f"Areas root path does not exist: {areas_root}")
        return 1

    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating static web bundle in: {target_dir}")

    # 1. Build tree.json
    tree_data = build_tree_data(areas_root)
    tree_path = target_dir / "tree.json"
    with open(tree_path, "w", encoding="utf-8") as f:
        json.dump(tree_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote tree data ({len(tree_data)} areas) to {tree_path}")

    # 2. Build search_index.json
    search_data = build_search_index(areas_root)
    search_path = target_dir / "search_index.json"
    with open(search_path, "w", encoding="utf-8") as f:
        json.dump(search_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote search index ({len(search_data['houses'])} houses, {len(search_data['tenants'])} tenants, {len(search_data['documents'])} docs) to {search_path}")

    # 3. Write web.config for IIS
    web_config_path = target_dir / "web.config"
    with open(web_config_path, "w", encoding="utf-8") as f:
        f.write(WEB_CONFIG_TEMPLATE)
    logger.info(f"Wrote IIS web.config to {web_config_path}")

    # 4. Copy index.html from static dir
    src_index = Path(__file__).resolve().parent.parent / "api" / "static" / "index.html"
    if src_index.exists():
        dst_index = target_dir / "index.html"
        shutil.copy2(src_index, dst_index)
        logger.info(f"Copied index.html to {dst_index}")
    else:
        logger.warning(f"Could not find source index.html at {src_index}")

    logger.info(f"Static web bundle successfully exported to: {target_dir}")
    logger.info("Files created:")
    logger.info(f"  - {tree_path.name}")
    logger.info(f"  - {search_path.name}")
    logger.info(f"  - {web_config_path.name}")
    logger.info("  - index.html")
    return 0
