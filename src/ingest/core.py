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
            continue
            
        with open(raw_dump_path, 'r', encoding='utf-8') as f:
            dump_data = json.load(f)
            
        if not dump_data:
            logger.error(f"Raw dump is empty for {pdf_path.name}")
            has_errors = True
            continue
            
        # Find expected house number
        house_number = None
        for page in dump_data:
            if page.get("expected_house_number"):
                house_number = page.get("expected_house_number")
                break
                
        if not house_number:
            logger.error(f"Could not determine house number for {pdf_path.name}")
            has_errors = True
            continue
            
        # Find target house directory
        target_house_dir = None
        for d in areas_root.iterdir():
            if d.is_dir() and (d.name == house_number or d.name.startswith(f"{house_number} -")):
                target_house_dir = d
                break
                
        if not target_house_dir:
            logger.error(f"Target house directory for {house_number} not found in {areas_root}")
            has_errors = True
            continue
            
        if not getattr(args, 'dry_run', False):
            # Move PDF
            dest_pdf = target_house_dir / pdf_path.name
            shutil.move(str(pdf_path), str(dest_pdf))
            
            # Create _ingest_manifest.json
            dest_manifest = target_house_dir / f"{pdf_path.stem}_ingest_manifest.json"
            with atomic_write(str(dest_manifest)) as tmp_path:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(dump_data, f, indent=2, ensure_ascii=False)
                    
            logger.info(f"Ingested {pdf_path.name} into {target_house_dir.name}")
        else:
            logger.info(f"[DRY RUN] Would ingest {pdf_path.name} into {target_house_dir.name}")
            
        # Cleanup raw dump
        try:
            os.remove(str(raw_dump_path))
        except OSError:
            pass

    return 1 if has_errors else 0
