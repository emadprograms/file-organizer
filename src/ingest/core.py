import os
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from src.core.config import AppConfig
from src.categorization.categorization import process_unclassified_pdf
from src.utils.fs import atomic_write

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
    input_path = Path(args.input_path).resolve()
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1
        
    pdf_files = []
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        pdf_files.append(input_path)
    elif input_path.is_dir():
        pdf_files.extend(list(input_path.glob("*.pdf")))
        
    if not pdf_files:
        logger.info(f"No PDFs found to ingest in {input_path}")
        return 0
        
    areas_root = Path(config.areas_root_path).resolve()
    
    has_errors = False
    dry_run_per_page = []
    
    report = {
        "pdfs_processed": 0,
        "errors": 0,
        "pages_ingested": 0
    }
    touched_houses = set()
    
    for pdf_path in pdf_files:
        if "_categorized" in pdf_path.name or "_finalized" in pdf_path.name:
            continue
            
        logger.info(f"Ingesting {pdf_path.name}...")
        
        # 1. Process the PDF to get categorization data
        # We can run process_unclassified_pdf on a temp directory, or directly in the input directory.
        # It's cleaner to run it in the input directory, and then move files.
        process_unclassified_pdf(
            target_dir=pdf_path.parent,
            llm_client=llm_client,
            specific_pdf_path=pdf_path,
            create_categorized_copy=False,
            model=getattr(args, 'model', None)
        )
        
        raw_dump_path = pdf_path.parent / f"{pdf_path.stem}.raw_dump.json"
        if not raw_dump_path.exists():
            logger.error(f"Failed to generate raw dump for {pdf_path.name}")
            has_errors = True
            report['errors'] += 1
            continue
            
        import pypdf
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            pdf_pages = len(reader.pages)
        except Exception as e:
            logger.error(f"Failed to read PDF {pdf_path.name}: {e}")
            has_errors = True
            report['errors'] += 1
            continue
            
        with open(raw_dump_path, 'r', encoding='utf-8') as f:
            dump_data = json.load(f)
            
        if not dump_data:
            logger.error(f"Raw dump is empty for {pdf_path.name}")
            has_errors = True
            report['errors'] += 1
            continue
            
        is_group_manifest = isinstance(dump_data, dict) and "groups" in dump_data
        
        if is_group_manifest:
            dump_pages = 0
            for g in dump_data["groups"]:
                if g["end_page"] + 1 > dump_pages:
                    dump_pages = g["end_page"] + 1
            if pdf_pages != dump_pages:
                logger.error(f"Page count mismatch for {pdf_path.name}: PDF has {pdf_pages} pages, but group manifest covers up to {dump_pages} pages.")
                has_errors = True
                report['errors'] += 1
                continue
        else:
            dump_pages = len(dump_data)
            if pdf_pages != dump_pages:
                logger.error(f"Page count mismatch for {pdf_path.name}: PDF has {pdf_pages} pages, dump has {dump_pages} pages.")
                has_errors = True
                report['errors'] += 1
                continue
            
        # Find expected house number
        house_number = None
        if is_group_manifest:
            for group in dump_data["groups"]:
                if group.get("expected_house_number"):
                    house_number = group.get("expected_house_number")
                    break
        else:
            for page in dump_data:
                if page.get("expected_house_number"):
                    house_number = page.get("expected_house_number")
                    break
                
        if not house_number:
            logger.error(f"Could not determine house number for {pdf_path.name}")
            has_errors = True
            report['errors'] += 1
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
                    with open(yaml_path, "w", encoding="utf-8") as yf:
                        yf.write(yaml_content)
                        
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
            dest_raw_dump = source_files_dir / raw_dump_path.name
            shutil.move(str(raw_dump_path), str(dest_raw_dump))
            
            report["pdfs_processed"] += 1
            report["pages_ingested"] += pdf_pages
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
            with open(report_path, "w", encoding="utf-8") as rf:
                json.dump(report, rf, indent=2, ensure_ascii=False)

    return 1 if has_errors else 0

