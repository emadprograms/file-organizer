import argparse
import os
import sys
import logging
from pathlib import Path

# Ensure src module is resolvable when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

from src.logger import setup_logging
from src.llm_client import LLMClient

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
    parser.add_argument("--model", type=str, default="gemma-4-26b-a4b-it", help="LLM model to use")
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
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

