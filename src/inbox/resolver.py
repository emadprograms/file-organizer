import json
import collections
from pathlib import Path
from typing import Any
import logging

from src.categorization.categorization import process_unclassified_pdf
from src.core.schemas import ParsedCommand
from src.tenant_config.yaml_loader import load_tenant_config
from src.grouping.name_matcher import canonicalize_with_llm
from src.routing.config import FOLDER_PREFIXES

logger = logging.getLogger(f"file_organizer.{__name__}")

class ConflictError(Exception):
    pass

def infer_missing_data(pdf_path: Path, parsed_cmd: ParsedCommand, llm_client: Any) -> dict:
    if parsed_cmd.house == 'U' or parsed_cmd.date == 'U':
        process_unclassified_pdf(
            target_dir=pdf_path.parent,
            llm_client=llm_client,
            specific_pdf_path=pdf_path,
            create_categorized_copy=False
        )
        report_path = pdf_path.parent / f"{pdf_path.stem}_report.json"
        
        house_counter = collections.Counter()
        date_counter = collections.Counter()
        
        if report_path.exists():
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    
                for page in report:
                    house = page.get("expected_house_number")
                    if house is not None and house != "":
                        house_counter[house] += 1
                        
                    date = page.get("date")
                    if date is not None and date != "":
                        date_counter[date] += 1
                        
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse report {report_path}: {e}")
                
        # Majority vote
        inferred_house = house_counter.most_common(1)[0][0] if house_counter else 'U'
        inferred_date = date_counter.most_common(1)[0][0] if date_counter else 'U'
        
        return {
            "expected_house_number": inferred_house,
            "date": inferred_date
        }
    
    return {
        "expected_house_number": parsed_cmd.house,
        "date": parsed_cmd.date
    }

def resolve_area(house_id: str, areas_root: Path) -> str:
    found_areas = []
    
    if not areas_root.exists() or not areas_root.is_dir():
        raise ValueError(f"areas_root {areas_root} does not exist or is not a directory.")
        
    for area_dir in areas_root.iterdir():
        if not area_dir.is_dir():
            continue
        house_dir = area_dir / house_id
        if house_dir.exists() and house_dir.is_dir():
            found_areas.append(area_dir.name)
            
    if len(found_areas) > 1:
        raise ConflictError(f"House {house_id} found in multiple areas: {', '.join(found_areas)}")
    elif len(found_areas) == 0:
        raise ValueError(f"House {house_id} not found in any area.")
        
    return found_areas[0]

def resolve_tenant(target_dir: Path, tenant_hint: str, llm_client: Any) -> str:
    if tenant_hint == 'U':
        return 'U'
        
    house_id = target_dir.name
    tenant_configs = load_tenant_config(target_dir, house_id)
    
    if not tenant_configs:
        return 'U'
        
    allowed_tenants = [tc["name"] for tc in tenant_configs if "name" in tc]
    if not allowed_tenants:
        return 'U'
        
    mappings = canonicalize_with_llm([tenant_hint], llm_client, allowed_tenants=allowed_tenants)
    match = mappings.get(tenant_hint)
    
    return match if match else 'U'

def resolve_group_mode(group: str) -> dict:
    if group == 'G':
        return {"skip_grouping": True, "skip_routing": False}
    elif group == 'U':
        return {"skip_grouping": False, "skip_routing": False}
    elif group.isdigit():
        group_int = int(group)
        if 1 <= group_int <= 13:
            prefix = f"{group_int:02d}"
            target_key = None
            for key, val in FOLDER_PREFIXES.items():
                if val == prefix:
                    target_key = key
                    break
            
            if target_key:
                return {
                    "skip_grouping": True,
                    "skip_routing": True,
                    "folder_name": f"{prefix}_{target_key}"
                }
    
    # Default or fallback
    return {"skip_grouping": False, "skip_routing": False}
