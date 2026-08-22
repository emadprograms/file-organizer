import argparse
import os
import sys
import json
import logging
from pathlib import Path

from typing import Any
import re

# Ensure src module is resolvable when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.utils.logger import setup_logging
from src.presentation.ui import set_verbosity
from src.llm.llm import LLMClient
from src.timeline.phase import process_cleaning_phase
from src.core.exceptions import ConfigurationError, ValidationError, FileOrganizerError
from src.categorization.categorization import process_unclassified_pdf
from src.pipeline.runner import run_cleaning_pass, run_fine_categorization_pass, run_grouping_pass, run_routing_pass, run_generation_pass
logger = logging.getLogger(f"file_organizer.{__name__}")

def validate_environment() -> None:
    """Validate that required environment variables are set.
    
    Raises:
        ConfigurationError: If GEMINI_API_KEY is missing.
    """
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        raise ConfigurationError("GEMINI_API_KEY is missing from the environment.")

def validate_target_directory(target_dir: Path) -> list[str]:
    """Validate the target directory contains the required categorized PDF and JSON report.
    
    Args:
        target_dir (Path): The directory to validate.
        
    Returns:
        list[str]: The extracted base IDs from the filenames.
        
    Raises:
        ValidationError: If files are missing, duplicates exist, or IDs mismatch.
    """
    if not target_dir.is_dir():
        raise ValidationError(f"Target directory does not exist or is not a directory: {target_dir}")
        
    # Check for resume state
    state_file = target_dir / ".source_files" / f"{target_dir.name}_state.json"
    
    # Make globs more permissive in case of renames (e.g., _categorized (1).pdf)
    pdf_files = [p for p in (list(target_dir.glob("*.pdf")) + list((target_dir / ".source_files").glob("*.pdf"))) if p.is_file()]
    json_files = [p for p in (list(target_dir.glob("*_report*.json")) + list((target_dir / ".source_files").glob("*_report*.json")) + list(target_dir.glob("*.raw_dump.json")) + list((target_dir / ".source_files").glob("*.raw_dump.json"))) if p.is_file()]
    
        
    if len(json_files) == 0:
        raise ValidationError("No .raw_dump.json or _report.json found in the target directory.")
        
    ids = []
    
    for json_file in json_files:
        name = json_file.name
        if "_old" in name or name == "ingest_report.json":
            continue
        if "_report" in name:
            json_id = name.split("_report")[0]
            ids.append(json_id)
        elif ".raw_dump.json" in name:
            json_id = name.split(".raw_dump.json")[0]
            ids.append(json_id)
            
    if not ids:
        raise ValidationError("No valid JSON reports found.")
        
    # Return unique IDs preserving order
    return list(dict.fromkeys(ids))

def validate_report_json(json_path: Path) -> None:
    """Validate that every page in the JSON report has a valid, known category.
    
    Args:
        json_path (Path): Path to the _report.json file.
        
    Raises:
        ValidationError: If a missing or invalid category is found.
    """
    from src.routing.config import CATEGORY_TO_FOLDERS, DIRECT_ROUTING_MAP, FORM_CATEGORIES, LETTER_CATEGORIES, FOLDER_PREFIXES
    
    valid_categories = {"others", "other_letters"}
    valid_categories.update(c.lower() for c in CATEGORY_TO_FOLDERS.keys())
    valid_categories.update(DIRECT_ROUTING_MAP.keys())
    valid_categories.update(c.lower() for c in FORM_CATEGORIES)
    valid_categories.update(c.lower() for c in LETTER_CATEGORIES)
    valid_categories.update(FOLDER_PREFIXES.keys())
    for folder, prefix in FOLDER_PREFIXES.items():
        valid_categories.add(f"{prefix}_{folder}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for i, page in enumerate(data):
        cat = page.get("category")
        if not cat:
            raise ValidationError(f"Page {i+1} in {json_path.name} is missing a category (found: {cat}). Please fix the report JSON.")
        if cat.lower() not in valid_categories:
            raise ValidationError(f"Page {i+1} in {json_path.name} has unknown category '{cat}'. Please fix the report JSON.")

def get_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: The configured parser object.
    """
    parser = argparse.ArgumentParser(description="File Organizer Post-Processor")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # create mode
    create_parser = subparsers.add_parser("create", help="Run standard document pipeline on a path")
    create_parser.add_argument("target_dir", type=Path, help="Path to the target directory containing the categorized PDF and report JSON")
    create_parser.add_argument(
        "--model", 
        type=str, 
        default="gemini-3.5-flash", 
        choices=["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash"],
        help="LLM model to use for the main tasks"
    )
    create_parser.add_argument(
        "--categorization-model", 
        type=str, 
        choices=["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash"],
        help="Optional: LLM model to use specifically for categorization. Defaults to the main model if not set."
    )
    create_parser.add_argument(
        "--routing-model", 
        type=str, 
        choices=["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash"],
        help="Optional: LLM model to use specifically for routing. Defaults to the main model if not set."
    )
    create_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the pipeline output without writing physical files or PDFs."
    )
    create_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    create_parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM calls and return mocked schemas."
    )
    create_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional: Path to the output base directory. Defaults to the parent of the house folder if target_dir is the house folder, otherwise to target_dir."
    )
    # ingest mode
    ingest_parser = subparsers.add_parser("ingest", help="Ingest raw PDFs into target house folders")
    ingest_parser.add_argument("input_path", type=Path, help="Path to the PDF file or directory to ingest")
    ingest_parser.add_argument(
        "--model", 
        type=str, 
        default="gemma-4-31b-it", 
        help="LLM model to use for the main tasks (fine categorization, grouping, routing)"
    )
    ingest_parser.add_argument(
        "--categorization-model", 
        type=str, 
        default="gemini-3.5-flash-lite", 
        help="LLM model to use for the initial OCR categorization pass"
    )
    ingest_parser.add_argument("--dry-run", action="store_true", help="Preview the operations without moving files")
    ingest_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    
    # reconcile mode
    reconcile_parser = subparsers.add_parser("reconcile", help="Reconcile existing categorized documents")
    reconcile_parser.add_argument("target_dir", type=Path, help="Path to the target house directory")
    reconcile_parser.add_argument(
        "--tenants", action="store_true", help="Only run tenant reallocation logic"
    )
    reconcile_parser.add_argument("--dry-run", action="store_true", help="Preview the operations without moving files")
    reconcile_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    # migrate mode
    migrate_parser = subparsers.add_parser("migrate", help="Migrate a v4 house to v5 vault architecture")
    migrate_parser.add_argument("target_dir", type=Path, help="Path to the target house directory")
    migrate_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    
    # verify mode
    verify_parser = subparsers.add_parser("verify", help="Deep verify the integrity of a v5 house vault structure")
    verify_parser.add_argument("target_dir", type=Path, help="Path to the target house directory to verify")
    verify_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    # undo mode
    undo_parser = subparsers.add_parser("undo", help="Undo the pipeline and reconstruct the original PDF")
    undo_parser.add_argument("target_dir", type=Path, help="Path to the target house directory to undo")
    undo_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    return parser

from src.reconcile.core import run_reconcile_mode


def main() -> int:
    """The main CLI entry point for the file organizer.
    
    Returns:
        int: The exit status code (0 for success, 1 for failure).
    """
    parser = get_parser()
    args = parser.parse_args()
    
    # Load config early
    try:
        from src.core.config import AppConfig
        config_env = os.getenv("FILE_ORGANIZER_CONFIG")
        if config_env:
            config_path = Path(config_env)
        else:
            config_path = Path("config.yaml")
            if not config_path.exists():
                # fallback to root path if run from a different directory
                config_path = Path(__file__).resolve().parent.parent / "config.yaml"
        config = AppConfig.load(config_path)
    except ConfigurationError as e:
        logger.exception(f"Failed to load configuration: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error loading config: {e}")
        return 1
    if args.command == "ingest":
        setup_logging(verbose=getattr(args, 'verbose', False))
        set_verbosity(getattr(args, 'verbose', False))
        from src.ingest.core import run_ingest_mode
        llm_client = LLMClient(api_key=os.getenv("GEMINI_API_KEY"))
        llm_client.default_model = getattr(args, 'model', "gemma-4-31b-it")
        try:
            return run_ingest_mode(args, config, llm_client)
        finally:
            llm_client.close()

    if args.command == "reconcile":
        setup_logging(verbose=getattr(args, 'verbose', False))
        set_verbosity(getattr(args, 'verbose', False))
        return run_reconcile_mode(args)

    if args.command == "migrate":
        setup_logging(verbose=getattr(args, 'verbose', False))
        set_verbosity(getattr(args, 'verbose', False))
        from src.migration.v5_migration import migrate_to_v5
        return migrate_to_v5(args.target_dir.resolve(), dry_run=getattr(args, 'dry_run', False))

    if args.command == "verify":
        setup_logging(verbose=getattr(args, 'verbose', False))
        set_verbosity(getattr(args, 'verbose', False))
        from src.core.verification import run_verification
        return run_verification(args.target_dir.resolve())

    if args.command == "undo":
        setup_logging(verbose=getattr(args, 'verbose', False))
        set_verbosity(getattr(args, 'verbose', False))
        from src.pipeline.undo import run_undo
        return run_undo(args.target_dir.resolve())

    # Ensure create mode paths are within allowed root
    target_path = args.target_dir.resolve()
    areas_root = Path(config.areas_root_path).resolve()
    
    if args.command == "create" and not target_path.is_relative_to(areas_root):
        logger.warning(f"Warning: Target path {target_path} is outside the allowed areas root {areas_root}")
        # return 1
    if getattr(args, 'dry_run', False) and sys.platform == 'win32':
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
        
        try:
            validate_target_directory(args.target_dir)
            targets = [args.target_dir]
        except ValidationError as original_err:
            # If the current directory has raw PDFs, it's a valid target
            if list(args.target_dir.glob("*.pdf")):
                targets = [args.target_dir]
            else:
                # Otherwise, check subdirectories for categorized or raw PDFs
                targets = [d for d in args.target_dir.iterdir() if d.is_dir() and list(d.glob("*.pdf"))]
            
            if not targets:
                raise original_err
                
        log_dir = setup_logging(verbose=getattr(args, 'verbose', False))
        set_verbosity(getattr(args, 'verbose', False))
        
        logger.info(f"Logs will be written to: {log_dir}")
        logger.info(f"Using LLM model: {args.model}")
        
        llm_client = LLMClient(api_key=os.getenv("GEMINI_API_KEY"))
        llm_client.default_model = args.model
        llm_client.skip_llm = getattr(args, 'skip_llm', False)
        llm_client.verbose = getattr(args, 'verbose', False)
        logger.info("Initialization and validation successful.")
        
        has_errors = False
        for target_dir in targets:
            try:
                # 1. Process unclassified PDFs
                categorization_model = getattr(args, 'categorization_model', None) or args.model
                process_unclassified_pdf(target_dir, llm_client, model=categorization_model, create_categorized_copy=False)
                
                # 2. Validate and get list of house_ids
                house_ids = validate_target_directory(target_dir)
                
                for house_id in house_ids:
                    if args.output_dir:
                        output_dir = args.output_dir
                    elif target_dir.name == house_id or target_dir.name.startswith(f"{house_id} -"):
                        output_dir = target_dir.parent
                    else:
                        output_dir = target_dir
                    
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    logger.info(f"Starting File Organizer Post-Processor for house ID: {house_id}")
                    logger.info(f"Target directory: {target_dir}")
                    logger.info(f"Output directory: {output_dir}")
                    
                    house_dir = output_dir / house_id
                    
                    json_paths = list(target_dir.glob(f"{house_id}*.raw_dump.json")) + list((target_dir / ".source_files").glob(f"{house_id}*.raw_dump.json"))
                    if not json_paths:
                        # Fallback for older .json reports if .raw_dump doesn't exist
                        json_paths = list(target_dir.glob(f"{house_id}_report*.json")) + list((target_dir / ".source_files").glob(f"{house_id}_report*.json"))
                        if not json_paths:
                             raise FileNotFoundError(f"Could not find .raw_dump.json or _report.json for house ID {house_id}")

                    json_path = json_paths[0]
                    
                    # Fail fast if report json has invalid categories
                    validate_report_json(json_path)
                    
                    state_dir = target_dir / ".source_files"
                    from src.core.state import State
                    state = State(house_id, state_dir)
                    
                    cleaned_pages, yaml_data = run_cleaning_pass(json_path, state, llm_client, logger, args.dry_run, house_id, target_dir)
                    
                    routing_model_to_use = getattr(args, 'routing_model', None) or args.model
                    
                    fine_categorized_pages = run_fine_categorization_pass(cleaned_pages, state, llm_client, logger, args.dry_run, routing_model_to_use)
                    
                    documents = run_grouping_pass(fine_categorized_pages, state, house_id, output_dir, llm_client, logger, args.dry_run)
                    documents = run_routing_pass(documents, state, house_id, output_dir, llm_client, logger, args.dry_run, routing_model_to_use)
                    run_generation_pass(documents, target_dir, house_id, output_dir, logger, args.dry_run, json_path, yaml_data, state=state)
            except Exception as e:
                logger.exception(f"Failed processing {target_dir}: {e}")
                has_errors = True
                
        return 1 if has_errors else 0
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




