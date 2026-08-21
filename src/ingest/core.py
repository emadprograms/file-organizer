import os
import sys
import json
import json
import logging
import shutil
from pathlib import Path
from typing import Any


from src.core.config import AppConfig
from src.categorization.categorization import process_unclassified_pdf
from src.utils.fs import atomic_write
from src.core.exceptions import ValidationError
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
        
    pdf_files = []
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        pdf_files.append(input_path)
    elif input_path.is_dir():
        pdf_files.extend([p for p in input_path.glob("*.pdf") if p.is_file() and "_categorized" not in p.name and "_finalized" not in p.name])
        
    if not pdf_files:
        logger.info(f"No PDFs found to ingest in {input_path}")
        return 0
        
    areas_root = Path(config.areas_root_path).resolve()
    
    has_errors = False
    dry_run_per_page = []
    
    reports = {}
    touched_houses = set()
    
    for pdf_path in pdf_files:
        target_house_dir = None
        
        logger.info(f"Processing PDF {pdf_path.name}...")
        
        raw_dump_path = pdf_path.parent / f"{pdf_path.stem}.raw_dump.json"
        
        if not raw_dump_path.exists():
            logger.info(f"Generating raw dump for {pdf_path.name} via LLM...")
            try:
                process_unclassified_pdf(
                    target_dir=pdf_path.parent,
                    llm_client=llm_client,
                    specific_pdf_path=pdf_path,
                    create_categorized_copy=False,
                    model=getattr(args, 'categorization_model', None) or getattr(args, 'model', None)
                )
            except Exception as e:
                logger.error(f"LLM processing failed for {pdf_path.name}: {e}")
                has_errors = True
                continue
                
            if not raw_dump_path.exists():
                logger.error(f"Failed to generate raw dump for {pdf_path.name}")
                has_errors = True
                continue
                
        with open(raw_dump_path, 'r', encoding='utf-8') as f:
            dump_data = json.load(f)
            
        if not dump_data:
            logger.error(f"Raw dump is empty for {raw_dump_path.name}")
            has_errors = True
            reports.setdefault(target_house_dir or 'unknown', {'pdfs_processed': 0, 'errors': 0, 'pages_ingested': 0})['errors'] += 1
            continue

        try:
            with fitz.open(str(pdf_path)) as doc:
                pdf_pages = doc.page_count
        except Exception as e:
            logger.error(f"Failed to read PDF {pdf_path.name}: {e}")
            has_errors = True
            continue

        is_group_manifest = isinstance(dump_data, dict) and "groups" in dump_data
        
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
                raise ValidationError(f"Page {i+1} in {raw_dump_path.name} is missing a category (found: {cat}). Please fix the report JSON.")
            if cat.lower() not in valid_categories:
                from src.core.exceptions import ValidationError
                raise ValidationError(f"Page {i+1} in {raw_dump_path.name} has unknown category '{cat}'. Please fix the report JSON.")

        # Find expected house number
        house_number = raw_dump_path.name.split('.raw_dump.json')[0]
                
        if not house_number:
            logger.error(f"Could not determine house number for {raw_dump_path.name}")
            has_errors = True
            reports.setdefault(target_house_dir or 'unknown', {'pdfs_processed': 0, 'errors': 0, 'pages_ingested': 0})['errors'] += 1
            continue
            
        # PDF must already be in the target house directory
        target_house_dir = pdf_path.parent
            

        if not getattr(args, 'dry_run', False):
            # 1. Pipeline passes
            from src.core.state import State
            state_dir = target_house_dir / ".source_files"
            state_dir.mkdir(parents=True, exist_ok=True)
            state = State(house_number, state_dir)
            
            from src.pipeline.runner import run_cleaning_pass, run_fine_categorization_pass, run_grouping_pass, run_routing_pass
            
            cleaned_pages, yaml_data = run_cleaning_pass(raw_dump_path, state, llm_client, logger, getattr(args, 'dry_run', False), house_number, target_house_dir)
            routing_model_to_use = getattr(args, 'routing_model', None) or getattr(args, 'model', None)
            
            fine_categorized_pages = run_fine_categorization_pass(cleaned_pages, state, llm_client, logger, getattr(args, 'dry_run', False), routing_model_to_use)
            
            documents = run_grouping_pass(fine_categorized_pages, state, house_number, target_house_dir, llm_client, logger, getattr(args, 'dry_run', False))
            documents = run_routing_pass(documents, state, house_number, target_house_dir, llm_client, logger, getattr(args, 'dry_run', False), routing_model_to_use)
            

            
            # Extract tenants for YAML from the state yaml_data instead of raw dump
            found_tenants = [t["name"] for t in yaml_data] if yaml_data else []
            if found_tenants:
                yaml_path = state_dir / f"{house_number}_1_tenants.yaml"
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


            if not getattr(args, 'dry_run', False):
                state.data["cleaned_pages"] = [p.model_dump() for p in cleaned_pages]
                state.data["fine_categorized_pages"] = [doc.model_dump() for doc in fine_categorized_pages]
                
                from src.timeline import FileOrganizer
                organizer = FileOrganizer()
                
                output_dir = target_house_dir.parent if target_house_dir.name == house_number or target_house_dir.name.startswith(f"{house_number} -") else target_house_dir
                
                per_page, full_house_id = organizer.organize(
                    documents, str(pdf_path), house_number, output_dir, yaml_data=yaml_data, dry_run=getattr(args, 'dry_run', False), prepend_mode=False
                )
                
                output_files = {p["output_file"] for p in per_page}
                summary = {
                    "total_output_pages": len(per_page),
                    "output_file_count": len(output_files)
                }
                
                state.data["routed_documents"] = {
                    "summary": summary,
                    "per_page": per_page
                }
                
                # Because organize renamed the directory to full_house_id!
                target_house_dir = output_dir / full_house_id
                state_dir = target_house_dir / ".source_files"
                state.state_file = state_dir / f"{full_house_id}_state.json"
                
                state.save()
                logger.info(f"Saved pipeline state to {state.state_file.name}")
                
            # Create _ingest_manifest.json
            dest_manifest = target_house_dir / f"{pdf_path.stem}_ingest_manifest.json"
            from src.utils.fs import atomic_write
            with atomic_write(str(dest_manifest)) as tmp_path:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(dump_data, f, indent=2, ensure_ascii=False)
                    
            logger.info(f"Ingested {pdf_path.name} into {target_house_dir.name}")
            
            # Move raw dump to .source_files
            raw_dump_path = target_house_dir / raw_dump_path.name
            dest_raw_dump = state_dir / raw_dump_path.name
            if raw_dump_path.resolve() != dest_raw_dump.resolve() and not getattr(args, 'dry_run', False):
                import shutil
                shutil.move(str(raw_dump_path), str(dest_raw_dump))
            
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


