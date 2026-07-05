import argparse
import os
import sys
import logging
from pathlib import Path
import json
import fitz

# Ensure src module is resolvable when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

from src.logger import setup_logging
from src.llm.llm import LLMClient
from src.cleaning import process_cleaning_phase

def validate_environment():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY is missing from the environment.", file=sys.stderr)
        sys.exit(1)

def validate_target_directory(target_dir: Path) -> str:
    if not target_dir.is_dir():
        print(f"ERROR: Target directory does not exist or is not a directory: {target_dir}", file=sys.stderr)
        sys.exit(1)
        
    pdf_files = list(target_dir.glob("*_categorized.pdf"))
    json_files = list(target_dir.glob("*_report.json"))
    
    if len(pdf_files) == 0:
        print("ERROR: No *_categorized.pdf found in the target directory.", file=sys.stderr)
        sys.exit(1)
    if len(pdf_files) > 1:
        print("ERROR: Multiple *_categorized.pdf files found in the target directory.", file=sys.stderr)
        sys.exit(1)
        
    if len(json_files) == 0:
        print("ERROR: No *_report.json found in the target directory.", file=sys.stderr)
        sys.exit(1)
    if len(json_files) > 1:
        print("ERROR: Multiple *_report.json files found in the target directory.", file=sys.stderr)
        sys.exit(1)
        
    pdf_id = pdf_files[0].name.split('_categorized.pdf')[0]
    json_id = json_files[0].name.split('_report.json')[0]
    
    if pdf_id != json_id:
        print(f"ERROR: ID mismatch between PDF ({pdf_id}) and JSON ({json_id}).", file=sys.stderr)
        sys.exit(1)
        
    output_dir = target_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    return pdf_id

def get_parser():
    parser = argparse.ArgumentParser(description="File Organizer Post-Processor")
    parser.add_argument("target_dir", type=Path, help="Path to the target directory containing the categorized PDF and report JSON")
    parser.add_argument(
        "--model", 
        type=str, 
        default="gemma-4-26b-a4b-it", 
        choices=["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-3.5-flash"],
        help="LLM model to use"
    )
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    validate_environment()
    house_id = validate_target_directory(args.target_dir)
    
    log_dir = setup_logging()
    logger = logging.getLogger("file_organizer")
    
    logger.info(f"Starting File Organizer Post-Processor for house ID: {house_id}")
    logger.info(f"Target directory: {args.target_dir}")
    logger.info(f"Using LLM model: {args.model}")
    logger.info(f"Logs will be written to: {log_dir}")
    
    llm_client = LLMClient(api_key=os.getenv("GEMINI_API_KEY"))
    llm_client.default_model = args.model
    
    logger.info("Initialization and validation successful.")
    
    json_path = list(args.target_dir.glob("*_report.json"))[0]
    output_json_path = args.target_dir / "output" / f"{house_id}_cleaned.json"
    
    if output_json_path.exists():
        logger.info(f"Skipping Pass 1 (found {output_json_path}). Loading cleaned data.")
        with open(output_json_path, 'r', encoding='utf-8') as f:
            from src.cleaning import PageData
            cleaned_pages = [PageData(**p) for p in json.load(f)]
    else:
        logger.info("Starting Pass 1 — Document Cleaning")
        cleaned_pages = process_cleaning_phase(json_path, llm_client)
        
        unique_tenants = len(set(p.canonical_tenant for p in cleaned_pages))
        logger.info(f"Cleaned {len(cleaned_pages)} pages successfully. Resolved {unique_tenants} unique tenant(s).")
        
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump([p.model_dump() for p in cleaned_pages], f, ensure_ascii=False, indent=2)
        logger.info(f"Wrote cleaned data to {output_json_path}")
    
    from src.processing.pipeline import Pipeline
    from src.processing.organizer import FileOrganizer, run_reconciliation
    
    checkpoint_dir = args.target_dir / "output" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    grouped_checkpoint_path = checkpoint_dir / "grouped.json"
    
    if grouped_checkpoint_path.exists():
        logger.info(f"Skipping Pass 2 (found {grouped_checkpoint_path}). Loading grouped documents.")
        from src.core.schemas import DocumentGroup
        with open(grouped_checkpoint_path, 'r', encoding='utf-8') as f:
            documents = [DocumentGroup(**d) for d in json.load(f)]
    else:
        logger.info("Starting Pass 2 — Grouping and Routing")
        raw_pages = [(p.original_index, p) for p in cleaned_pages]
        
        pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY"))
        pipeline.client = llm_client
        
        documents = pipeline._group_and_route_documents(raw_pages, None)
        
        tmp_path = grouped_checkpoint_path.with_suffix('.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump([doc.model_dump() for doc in documents], f, ensure_ascii=False, indent=2)
        tmp_path.replace(grouped_checkpoint_path)
        logger.info(f"Wrote grouped documents to {grouped_checkpoint_path}")

    pdf_path = list(args.target_dir.glob("*_categorized.pdf"))[0]
    output_dir = args.target_dir / "output"
    
    organizer = FileOrganizer()
    per_page = organizer.organize(documents, str(pdf_path), house_id, output_dir, None)
    
    with fitz.open(str(pdf_path)) as pdf_doc:
        total_input_pages = pdf_doc.page_count
    
    output_files = {p["output_file"] for p in per_page}
    summary = {
        "total_output_pages": len(per_page),
        "output_file_count": len(output_files)
    }
    
    logger.info("Running reconciliation...")
    run_reconciliation(summary, per_page, total_input_pages, house_id, output_dir)
    
    # If reconciliation succeeds, clean up checkpoints
    if output_json_path.exists():
        output_json_path.unlink()
    if grouped_checkpoint_path.exists():
        grouped_checkpoint_path.unlink()
        
    logger.info(f"Successfully generated {summary['output_file_count']} PDFs in {output_dir / house_id}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

