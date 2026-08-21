import os
import sys
import json
import logging
import shutil
from pathlib import Path
from typing import Any


from src.core.config import AppConfig
from src.categorization.categorization import process_unclassified_pdf
from src.utils.fs import atomic_write
import fitz

logger = logging.getLogger(f"file_organizer.{__name__}")

def run_ingest_mode(args: Any, config: AppConfig, llm_client: Any) -> int:
    """Run the ingest mode to process raw PDFs and move them to target house folders.
    
    Args:
        args: Parsed command-line arguments.
        config: Application configuration.
        llm_client: LLM client for categorization.
        
    Returns:
        int: The exit status code.
    """
    if getattr(args, 'dry_run', False) and sys.platform == 'win32':
        if sys.stdout.encoding.lower() != 'utf-8':
            logger.warning("Terminal encoding is not UTF-8. Arabic characters may not render correctly.")
            logger.warning("Recommend setting environment variable: PYTHONIOENCODING=utf8")
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    input_path = Path(args.input_path).resolve()
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1
        
    json_files = []
    if input_path.is_file() and input_path.name.endswith('.raw_dump.json'):
        json_files.append(input_path)
    elif input_path.is_dir():
        json_files.extend([p for p in input_path.glob("*.raw_dump.json") if p.is_file()])
        
    if not json_files:
        logger.info(f"No JSON dumps found to ingest in {input_path}")
        return 0
        
    areas_root = Path(config.areas_root_path).resolve()
    
    has_errors = False
    dry_run_per_page = []
    
    reports = {}
    touched_houses = set()
    
    for json_path in json_files:
        target_house_dir = None
        
        logger.info(f"Processing raw dump {json_path.name}...")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            dump_data = json.load(f)
            
        if not dump_data:
            logger.error(f"Raw dump is empty for {json_path.name}")
            has_errors = True
            reports.setdefault(target_house_dir or 'unknown', {'pdfs_processed': 0, 'errors': 0, 'pages_ingested': 0})['errors'] += 1
            continue

        is_group_manifest = isinstance(dump_data, dict) and "groups" in dump_data
        
        if is_group_manifest:
            dump_pages = 0
            for g in dump_data["groups"]:
                if g["end_page"] + 1 > dump_pages:
                    dump_pages = g["end_page"] + 1
        else:
            dump_pages = len(dump_data)
            
        pdf_path = None
        pdf_pages = 0
        candidate_pdfs = [p for p in json_path.parent.glob("*.pdf") if p.is_file()]
        for candidate in candidate_pdfs:
            if "_categorized" in candidate.name or "_finalized" in candidate.name:
                continue
            with fitz.open(str(candidate)) as doc:
                if doc.page_count == dump_pages:
                    pdf_path = candidate
                    pdf_pages = doc.page_count
                    break
                
        if not pdf_path:
            logger.error(f"Could not find a matching PDF with {dump_pages} pages for {json_path.name}")
            has_errors = True
            reports.setdefault(target_house_dir or 'unknown', {'pdfs_processed': 0, 'errors': 0, 'pages_ingested': 0})['errors'] += 1
            continue
            
        logger.info(f"Matched {json_path.name} to {pdf_path.name} ({pdf_pages} pages)")
        
        # Validate report categories
        from src.routing.config import CATEGORY_TO_FOLDERS, DIRECT_ROUTING_MAP, FORM_CATEGORIES, LETTER_CATEGORIES, FOLDER_PREFIXES
        valid_categories = {"others", "other_letters"}
        valid_categories.update(c.lower() for c in CATEGORY_TO_FOLDERS.keys())
        valid_categories.update(DIRECT_ROUTING_MAP.keys())
        valid_categories.update(c.lower() for c in FORM_CATEGORIES)
        valid_categories.update(c.lower() for c in LETTER_CATEGORIES)
        valid_categories.update(FOLDER_PREFIXES.keys())
        for folder, prefix in FOLDER_PREFIXES.items():
            valid_categories.add(f"{prefix}_{folder}")

        items_to_check = dump_data.get("groups", []) if isinstance(dump_data, dict) and "groups" in dump_data else (dump_data if isinstance(dump_data, list) else [])
        for i, item in enumerate(items_to_check):
            cat = item.get("category")
            if not cat:
                from src.core.exceptions import ValidationError
                raise ValidationError(f"Page {i+1} in {json_path.name} is missing a category (found: {cat}). Please fix the report JSON.")
            if cat.lower() not in valid_categories:
                from src.core.exceptions import ValidationError
                raise ValidationError(f"Page {i+1} in {json_path.name} has unknown category '{cat}'. Please fix the report JSON.")

        # Find expected house number
        house_number = json_path.name.split('.raw_dump.json')[0]
                
        if not house_number:
            logger.error(f"Could not determine house number for {json_path.name}")
            has_errors = True
            reports.setdefault(target_house_dir or 'unknown', {'pdfs_processed': 0, 'errors': 0, 'pages_ingested': 0})['errors'] += 1
            continue
            
        # Find target house directory
        target_house_dir = None
        for d in areas_root.iterdir():
            if d.is_dir() and (d.name == house_number or d.name.startswith(f"{house_number} -")):
                target_house_dir = d
                break
                
        if not target_house_dir:
            target_house_dir = areas_root / house_number
            target_house_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created new house directory: {target_house_dir.name}")
            

        if not getattr(args, 'dry_run', False):
            # Extract tenants for YAML
            found_tenants = []
            if is_group_manifest:
                for group in dump_data["groups"]:
                    t = group.get("expected_tenant_name")
                    if t and t not in found_tenants and not t.startswith("Unassigned") and not t.startswith("غير محدد"):
                        found_tenants.append(t)
            else:
                for page in dump_data:
                    t = page.get("expected_tenant_name")
                    if t and t not in found_tenants and not t.startswith("Unassigned") and not t.startswith("غير محدد"):
                        found_tenants.append(t)
                        
            if found_tenants:
                source_files_dir = target_house_dir / ".source_files"
                source_files_dir.mkdir(parents=True, exist_ok=True)
                yaml_path = source_files_dir / f"{house_number}_1_tenants.yaml"
                if not yaml_path.exists():
                    yaml_content = ""
                    for tenant in found_tenants:
                        yaml_content += f"- name: {tenant}\n  start_date: '2000-01-01'\n  end_date: present\n"
                    with atomic_write(str(yaml_path)) as tmp_path:
                        with open(tmp_path, "w", encoding="utf-8") as yf:
                            yf.write(yaml_content)
                else:
                    import yaml
                    with open(yaml_path, "r", encoding="utf-8") as yf:
                        existing_data = yaml.safe_load(yf) or []
                    existing_names = [item["name"] for item in existing_data if isinstance(item, dict)]
                    added = False
                    for tenant in found_tenants:
                        if tenant not in existing_names:
                            existing_data.append({"name": tenant, "start_date": "2000-01-01", "end_date": "present"})
                            existing_names.append(tenant)
                            added = True
                    if added:
                        with atomic_write(str(yaml_path)) as tmp_path:
                            with open(tmp_path, "w", encoding="utf-8") as yf:
                                yaml.dump(existing_data, yf, allow_unicode=True, default_flow_style=False, sort_keys=False)
                        
            # Move PDF

            dest_pdf = target_house_dir / pdf_path.name
            shutil.move(str(pdf_path), str(dest_pdf))
            
            # Create _ingest_manifest.json
            dest_manifest = target_house_dir / f"{pdf_path.stem}_ingest_manifest.json"
            with atomic_write(str(dest_manifest)) as tmp_path:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(dump_data, f, indent=2, ensure_ascii=False)
                    
            logger.info(f"Ingested {pdf_path.name} into {target_house_dir.name}")
            
            # Move raw dump to .source_files
            source_files_dir = target_house_dir / ".source_files"
            source_files_dir.mkdir(parents=True, exist_ok=True)
            dest_raw_dump = source_files_dir / json_path.name
            shutil.move(str(json_path), str(dest_raw_dump))
            
            r = reports.setdefault(target_house_dir, {"pdfs_processed": 0, "errors": 0, "pages_ingested": 0})
            r["pdfs_processed"] += 1
            r["pages_ingested"] += pdf_pages
            touched_houses.add(target_house_dir)
        else:
            logger.info(f"[DRY RUN] Would ingest {pdf_path.name} into {target_house_dir.name}")
            if is_group_manifest:
                for idx, group in enumerate(dump_data["groups"]):
                    tenant = group.get("expected_tenant_name", "Unassigned") or "Unassigned"
                    cat = group.get("category", "Unassigned") or "Unassigned"
                    start = group.get("start_page", 0)
                    end = group.get("end_page", 0)
                    for i in range(start, end + 1):
                        dry_run_per_page.append({
                            "output_file": f"{target_house_dir.name}/{tenant}/{cat}/{pdf_path.stem}_part_{idx + 1}.pdf"
                        })
            else:
                for idx, page in enumerate(dump_data):
                    tenant = page.get("expected_tenant_name", "Unassigned") or "Unassigned"
                    cat = page.get("category", "Unassigned") or "Unassigned"
                    dry_run_per_page.append({
                        "output_file": f"{target_house_dir.name}/{tenant}/{cat}/{pdf_path.stem}_page_{idx + 1}.pdf"
                    })

    if getattr(args, 'dry_run', False) and dry_run_per_page:
        from src.pipeline.visualizer import Visualizer
        vis = Visualizer()
        summary = {
            "total_output_pages": len(dry_run_per_page),
            "output_file_count": len(set([p["output_file"] for p in dry_run_per_page]))
        }
        house_id = dry_run_per_page[0]["output_file"].split("/")[0] if dry_run_per_page else "Unknown"
        vis.print_summary(house_id, summary, dry_run_per_page, [])


    if not getattr(args, 'dry_run', False):
        for house_dir in touched_houses:
            sf_dir = house_dir / ".source_files"
            sf_dir.mkdir(parents=True, exist_ok=True)
            report_path = sf_dir / "ingest_report.json"
            with atomic_write(str(report_path)) as tmp_path:
                with open(tmp_path, "w", encoding="utf-8") as rf:
                    json.dump(reports.get(house_dir, {'pdfs_processed': 0, 'errors': 0, 'pages_ingested': 0}), rf, indent=2, ensure_ascii=False)

    return 1 if has_errors else 0

