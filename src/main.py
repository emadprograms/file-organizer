"""Command-line entry point for the File Categorizer application.

Initializes the environment, loads configuration, parses arguments,
and orchestrates the pipeline and file organizer.
"""
import logging
import os
import argparse
logger = logging.getLogger(__name__)
from pathlib import Path
from dotenv import load_dotenv
import sys

# Add project root to sys.path to allow 'src' module imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.pipeline import Pipeline
from src.organizer import FileOrganizer
from src.config import load_config, setup_logging

def main():
    """Main execution function.
    
    Sets up logging, loads environment variables, initializes the pipeline,
    processes the input PDF, and organizes the resulting documents.
    """
    setup_logging()
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    load_dotenv()
    
    config = load_config()
    
    parser = argparse.ArgumentParser(description="Process and categorize housing documents.")
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument("-o", "--output", default="./output", help="Base output directory")
    args = parser.parse_args()
    
    pipeline = Pipeline(api_key=config.gemini_api_key)
    
    if not os.path.exists(args.pdf_path):
        logger.info(f"Please provide a valid PDF file at {args.pdf_path} to run.")
        return
        
    documents = pipeline.process_pdf(args.pdf_path)
    logger.info(f"Identified {len(documents)} documents.")
    
    organizer = FileOrganizer()
    summary = organizer.organize(documents, args.pdf_path, Path(args.output))
    
    if summary:
        house_number = organizer._resolve_house_number(args.pdf_path)
        num_residents = len(organizer._build_resident_order(documents))
        output_dir = Path(args.output) / house_number
        
        logger.info(f"\n{'='*50}")
        logger.info(f"  House: {house_number}")
        logger.info(f"  Residents: {num_residents}")
        logger.info(f"  PDFs generated: {len(summary)}")
        logger.info(f"  Output: {output_dir}")
        logger.info(f"{'='*50}")

if __name__ == "__main__":
    main()
