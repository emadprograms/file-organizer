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
        
        # Fail fast if multiple folders for this house exist
        output_dir = target_house_dir.parent
        all_house_folders = [d for d in output_dir.iterdir() if d.is_dir() and (d.name == house_number or d.name.startswith(f"{house_number} -"))]
        if len(all_house_folders) > 1:
            logger.error(f"Found multiple folders for house {house_number} in {output_dir}. This can cause dangerous conflicts.")
            for d in all_house_folders:
                logger.error(f"  - {d.name}")
            logger.error("Please consolidate the files into a single canonical folder and run ingest on that folder.")
            has_errors = True
            reports.setdefault(target_house_dir, {'pdfs_processed': 0, 'errors': 0, 'pages_ingested': 0})['errors'] += 1
            continue
            
        if not getattr(args, 'dry_run', False):
            # 1. Pipeline passes
            from src.core.state import State
            state_dir = target_house_dir / ".source_files"
            state_dir.mkdir(parents=True, exist_ok=True)
            
            master_state = State(house_number, state_dir)
            if master_state.state_file.exists():
                master_state.load()
            
            is_prepend_mode = bool(master_state.data.get("cleaned_pages"))
            
            state = State(house_number, state_dir)
            if state.state_file.exists():
                state.load()
                
            if is_prepend_mode:
                logger.info("Existing state found. Triggering PREPEND mode for new PDF.")
                # Clear state arrays so we only process the new document
                state.data.pop("cleaned_pages", None)
                state.data.pop("fine_categorized_pages", None)
                state.data.pop("grouped_documents", None)
                state.data.pop("routed_documents", None)
            
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
                    documents, str(pdf_path), house_number, output_dir, yaml_data=yaml_data, dry_run=True, prepend_mode=False
                )
                
                output_files = {p["output_file"] for p in per_page}
                unaccounted_pages = []
                accounted_page_indices = {p["page_index"] for p in per_page}
                for i in range(pdf_pages):
                    if i not in accounted_page_indices:
                        unaccounted_pages.append(i)
                        
                manifest = {
                    "summary": {
                        "house_id": house_number,
                        "total_input_pages": pdf_pages,
                        "total_output_pages": len(per_page),
                        "output_file_count": len(output_files),
                        "unaccounted_pages": unaccounted_pages
                    },
                    "per_page": per_page
                }
                
                # We will prepare grouped_with_source here so we can use it for both grouped_documents and routed_documents
                grouped_with_source = []
                for doc in documents:
                    d_dict = doc.model_dump()
                    d_dict["source_pdf"] = pdf_path.name
                    d_dict["relative_start_page"] = d_dict["start_page"]
                    d_dict["relative_end_page"] = d_dict["end_page"]
                    grouped_with_source.append(d_dict)
                    
                state.data["manifest"] = manifest
                state.data["routed_documents"] = grouped_with_source
                
                # Because organize computed the full_house_id, we need to
                # create the directory structure ourselves (organize ran with
                # dry_run=True so it didn't create anything on disk).
                target_house_dir = output_dir / full_house_id
                state_dir = target_house_dir / ".source_files"
                
                # Rename existing house dir if needed (e.g., "777" -> "777 - Test Tenant")
                if not target_house_dir.exists():
                    # Look for any existing dir matching this house number
                    old_house_dir = output_dir / house_number
                    if not old_house_dir.exists():
                        # Try finding a dir with the house number prefix
                        candidates = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith(f"{house_number} -")]
                        if candidates:
                            old_house_dir = candidates[0]
                    if old_house_dir.exists() and old_house_dir != target_house_dir:
                        # Save reference before rename
                        saved_old = Path(str(old_house_dir))
                        old_house_dir.rename(target_house_dir)
                        # Fix raw_dump_path and pdf_path if they were inside the renamed dir
                        try:
                            rel = raw_dump_path.relative_to(saved_old)
                            raw_dump_path = target_house_dir / rel
                        except ValueError:
                            pass
                        try:
                            rel = pdf_path.relative_to(saved_old)
                            pdf_path = target_house_dir / rel
                        except ValueError:
                            pass
                
                # Ensure directories exist
                target_house_dir.mkdir(parents=True, exist_ok=True)
                state_dir.mkdir(parents=True, exist_ok=True)
                
                if is_prepend_mode:
                    shift_amount = len(state.data.get("cleaned_pages", []))
                    
                    new_grouped = []
                    for doc in documents:
                        d_dict = doc.model_dump()
                        d_dict["source_pdf"] = pdf_path.name
                        d_dict["relative_start_page"] = d_dict["start_page"]
                        d_dict["relative_end_page"] = d_dict["end_page"]
                        new_grouped.append(d_dict)
                        
                    for doc_dict in master_state.data.get("grouped_documents", []):
                        if "start_page" in doc_dict: doc_dict["start_page"] += shift_amount
                        if "end_page" in doc_dict: doc_dict["end_page"] += shift_amount
                            
                    master_routed = master_state.data.get("routed_documents", [])
                    if isinstance(master_routed, list):
                        for route in master_routed:
                            if "start_page" in route: route["start_page"] += shift_amount
                            if "end_page" in route: route["end_page"] += shift_amount
                            
                    master_manifest = master_state.data.get("manifest")
                    if not master_manifest and isinstance(master_state.data.get("routed_documents"), dict):
                        master_manifest = master_state.data.get("routed_documents")
                        
                    if master_manifest and isinstance(master_manifest, dict):
                        for page_route in master_manifest.get("per_page", []):
                            if "page_index" in page_route: page_route["page_index"] += shift_amount
                            
                    for page in master_state.data.get("cleaned_pages", []):
                        if "original_index" in page: page["original_index"] += shift_amount
                    for page in master_state.data.get("fine_categorized_pages", []):
                        if "original_index" in page: page["original_index"] += shift_amount
                            
                    master_state.data["cleaned_pages"] = state.data.get("cleaned_pages", []) + master_state.data.get("cleaned_pages", [])
                    master_state.data["fine_categorized_pages"] = state.data.get("fine_categorized_pages", []) + master_state.data.get("fine_categorized_pages", [])
                    master_state.data["grouped_documents"] = new_grouped + master_state.data.get("grouped_documents", [])
                    
                    if isinstance(master_routed, list):
                        master_state.data["routed_documents"] = state.data["routed_documents"] + master_routed
                    else:
                        # Fallback for legacy states where routed_documents was mistakenly a dict
                        # grouped_documents corresponds structurally to routed_documents
                        master_state.data["routed_documents"] = state.data["routed_documents"] + master_state.data.get("grouped_documents", [])
                        
                    if master_manifest and isinstance(master_manifest, dict):
                        master_manifest["per_page"] = state.data["manifest"]["per_page"] + master_manifest.get("per_page", [])
                        if "summary" not in master_manifest:
                            master_manifest["summary"] = {"total_output_pages": 0, "output_file_count": 0, "total_input_pages": 0}
                        master_manifest["summary"]["total_output_pages"] = master_manifest["summary"].get("total_output_pages", 0) + state.data["manifest"]["summary"]["total_output_pages"]
                        master_manifest["summary"]["total_input_pages"] = master_manifest["summary"].get("total_input_pages", 0) + state.data["manifest"]["summary"]["total_input_pages"]
                    else:
                        master_state.data["manifest"] = state.data["manifest"]
                        
                    try:
                        for p in master_state.data.get("manifest", {}).get("per_page", []):
                            if p.get("vault_id"):
                                logger.info(f"DOC VAULT ID: {p.get('vault_id')}")
                    except Exception: pass
                    master_state.save()
                    logger.info(f"Saved prepended pipeline state to {master_state.state_file.name}")
                else:
                    # Save grouped_documents with source_pdf metadata so reconcile
                    # Phase 42 can extract vault PDFs from the source PDF.
                    grouped_with_source = []
                    for doc in documents:
                        d_dict = doc.model_dump()
                        d_dict["source_pdf"] = pdf_path.name
                        d_dict["relative_start_page"] = d_dict["start_page"]
                        d_dict["relative_end_page"] = d_dict["end_page"]
                        grouped_with_source.append(d_dict)
                    state.data["grouped_documents"] = grouped_with_source
                    
                    state.state_dir = state_dir
                    state.house_id = house_number
                    state.state_file = state_dir / f"{house_number}_state.json"
                    state.save()
                    logger.info(f"Saved pipeline state to {state.state_file.name}")
                
            logger.info(f"Ingested {pdf_path.name} into {target_house_dir.name}")
            
            # Move raw dump to .source_files
            # The raw_dump_path is originally created next to the PDF.
            if raw_dump_path and raw_dump_path.exists():
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

    return 1 if has_errors else 0


