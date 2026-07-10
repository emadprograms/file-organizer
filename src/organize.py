import argparse
import os
import sys
import logging
from pathlib import Path
import json
import fitz
from typing import Any

# Ensure src module is resolvable when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

from src.logger import setup_logging
from src.core.ui import set_verbosity
from src.llm.llm import LLMClient
from src.cleaning import process_cleaning_phase
from src.core.exceptions import ConfigurationError, ValidationError, FileOrganizerError

logger = logging.getLogger(f"file_organizer.{__name__}")

def validate_environment():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        raise ConfigurationError("GEMINI_API_KEY is missing from the environment.")

def validate_target_directory(target_dir: Path) -> str:
    if not target_dir.is_dir():
        raise ValidationError(f"Target directory does not exist or is not a directory: {target_dir}")
        
    pdf_files = list(target_dir.glob("*_categorized.pdf"))
    json_files = list(target_dir.glob("*_report.json"))
    
    if len(pdf_files) == 0:
        raise ValidationError("No *_categorized.pdf found in the target directory.")
    if len(pdf_files) > 1:
        raise ValidationError("Multiple *_categorized.pdf files found in the target directory.")
        
    if len(json_files) == 0:
        raise ValidationError("No *_report.json found in the target directory.")
    if len(json_files) > 1:
        raise ValidationError("Multiple *_report.json files found in the target directory.")
        
    pdf_id = pdf_files[0].name.split('_categorized.pdf')[0]
    json_id = json_files[0].name.split('_report.json')[0]
    
    if pdf_id != json_id:
        raise ValidationError(f"ID mismatch between PDF ({pdf_id}) and JSON ({json_id}).")
        
    return pdf_id

def get_parser():
    parser = argparse.ArgumentParser(description="File Organizer Post-Processor")
    parser.add_argument("target_dir", type=Path, help="Path to the target directory containing the categorized PDF and report JSON")
    parser.add_argument(
        "--model", 
        type=str, 
        default="gemma-4-26b-a4b-it", 
        choices=["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"],
        help="LLM model to use"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the pipeline output without writing physical files or PDFs."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM calls and return mocked schemas."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional: Path to the output base directory. Defaults to the parent of the house folder if target_dir is the house folder, otherwise to target_dir."
    )
    return parser

def run_cleaning_pass(json_path: Path, output_json_path: Path, llm_client: Any, logger: logging.Logger, dry_run: bool) -> list:
    if output_json_path.exists():
        logger.info(f"Skipping Pass 1 (found {output_json_path}). Loading cleaned data.")
        with open(output_json_path, 'r', encoding='utf-8') as f:
            from src.cleaning import PageData
            return [PageData(**p) for p in json.load(f)]
            
    logger.info("Starting Pass 1 — Document Cleaning")
    cleaned_pages = process_cleaning_phase(json_path, llm_client)
    
    unique_tenants = len(set(p.canonical_tenant for p in cleaned_pages))
    logger.info(f"Cleaned {len(cleaned_pages)} pages successfully. Resolved {unique_tenants} unique tenant(s).")
    
    if not dry_run:
        from src.fs_utils import atomic_write
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with atomic_write(str(output_json_path)) as tmp_path:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump([p.model_dump() for p in cleaned_pages], f, ensure_ascii=False, indent=2)
        logger.info(f"Wrote cleaned data to {output_json_path}")
    else:
        logger.info(f"  [DRY RUN] Would write cleaned data to {output_json_path}")
        
    return cleaned_pages

def run_grouping_pass(cleaned_pages: list, house_id: str, output_dir: Path, llm_client: Any, logger: logging.Logger, dry_run: bool) -> list:
    from src.processing.pipeline import Pipeline
    from src.core.schemas import DocumentGroup
    
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    grouped_checkpoint_path = checkpoint_dir / f"{house_id}_grouped.json"
    run_checkpoint_path = checkpoint_dir / f"{house_id}_runs_checkpoint.json"
    
    if grouped_checkpoint_path.exists():
        logger.info(f"Skipping Pass 2 (found {grouped_checkpoint_path}). Loading grouped documents.")
        with open(grouped_checkpoint_path, 'r', encoding='utf-8') as f:
            return [DocumentGroup(**d) for d in json.load(f)]
            
    logger.info("Starting Pass 2 — Grouping and Routing")
    raw_pages = [(p.original_index, p) for p in cleaned_pages]
    
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY"))
    pipeline.client = llm_client
    
    documents = pipeline._group_and_route_documents(raw_pages, str(run_checkpoint_path))
    
    if not dry_run:
        from src.fs_utils import atomic_write
        with atomic_write(str(grouped_checkpoint_path)) as tmp_path:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump([doc.model_dump() for doc in documents], f, ensure_ascii=False, indent=2)
        logger.info(f"Wrote grouped documents to {grouped_checkpoint_path}")
    else:
        logger.info(f"  [DRY RUN] Would write grouped documents to {grouped_checkpoint_path}")
        
    return documents

def run_generation_pass(documents: list, target_dir: Path, house_id: str, output_dir: Path, logger: logging.Logger, dry_run: bool):
    from src.processing.organizer import FileOrganizer, run_reconciliation
    
    pdf_path = list(target_dir.glob("*_categorized.pdf"))[0]
    
    organizer = FileOrganizer()
    per_page = organizer.organize(documents, str(pdf_path), house_id, output_dir, None, dry_run=dry_run)
    
    with fitz.open(str(pdf_path)) as pdf_doc:
        total_input_pages = pdf_doc.page_count
    
    output_files = {p["output_file"] for p in per_page}
    summary = {
        "total_output_pages": len(per_page),
        "output_file_count": len(output_files)
    }
    
    logger.info("Running reconciliation...")
    run_reconciliation(summary, per_page, total_input_pages, house_id, output_dir, dry_run=dry_run)
    
    output_json_path = output_dir / f"{house_id}_cleaned.json"
    grouped_checkpoint_path = output_dir / "checkpoints" / f"{house_id}_grouped.json"
    
    if not dry_run:
        if output_json_path.exists():
            output_json_path.unlink()
        if grouped_checkpoint_path.exists():
            grouped_checkpoint_path.unlink()
            
    if dry_run:
        from src.processing.visualizer import Visualizer
        logger.info("Invoking visualizer for dry run output...")
        visualizer = Visualizer()
        visualizer.print_summary(house_id, summary, per_page, documents)
        
    logger.info(f"Successfully generated {summary['output_file_count']} PDFs in {output_dir / house_id}")

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    if args.dry_run and sys.platform == 'win32':
        if sys.stdout.encoding.lower() != 'utf-8':
            logger.warning("Terminal encoding is not UTF-8. Arabic characters may not render correctly.")
            logger.warning("Recommend setting environment variable: PYTHONIOENCODING=utf8")
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
            
    llm_client = None
    try:
        validate_environment()
        house_id = validate_target_directory(args.target_dir)
        
        if args.output_dir:
            output_dir = args.output_dir
        elif args.target_dir.name == house_id:
            output_dir = args.target_dir.parent
        else:
            output_dir = args.target_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)

        log_dir = setup_logging(verbose=getattr(args, 'verbose', False))
        set_verbosity(getattr(args, 'verbose', False))
        
        logger.info(f"Starting File Organizer Post-Processor for house ID: {house_id}")
        logger.info(f"Target directory: {args.target_dir}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Using LLM model: {args.model}")
        logger.info(f"Logs will be written to: {log_dir}")
        
        llm_client = LLMClient(api_key=os.getenv("GEMINI_API_KEY"))
        llm_client.default_model = args.model
        llm_client.skip_llm = getattr(args, 'skip_llm', False)
        llm_client.verbose = getattr(args, 'verbose', False)
        
        logger.info("Initialization and validation successful.")
        
        json_path = list(args.target_dir.glob("*_report.json"))[0]
        output_json_path = output_dir / f"{house_id}_cleaned.json"
        
        cleaned_pages = run_cleaning_pass(json_path, output_json_path, llm_client, logger, args.dry_run)
        documents = run_grouping_pass(cleaned_pages, house_id, output_dir, llm_client, logger, args.dry_run)
        run_generation_pass(documents, args.target_dir, house_id, output_dir, logger, args.dry_run)
        
        return 0
    except FileOrganizerError as e:
        logger.exception(f"File Organizer failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1
    finally:
        if llm_client:
            llm_client.close()

if __name__ == "__main__":
    sys.exit(main())

