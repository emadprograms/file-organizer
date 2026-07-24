import argparse
import os
import sys
import logging
from pathlib import Path
import json
import fitz
from typing import Any
import re

# Ensure src module is resolvable when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

from src.utils.logger import setup_logging
from src.presentation.ui import set_verbosity
from src.llm.llm import LLMClient
from src.timeline.phase import process_cleaning_phase
from src.core.exceptions import ConfigurationError, ValidationError, FileOrganizerError
from src.categorization.categorization import process_unclassified_pdf
from src.pipeline.runner import run_cleaning_pass, run_grouping_pass, run_routing_pass, run_generation_pass

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
        
    # Make globs more permissive in case of renames (e.g., _categorized (1).pdf)
    pdf_files = list(target_dir.glob("*_categorized*.pdf")) + list((target_dir / ".source_files").glob("*_categorized*.pdf"))
    json_files = list(target_dir.glob("*_report*.json")) + list((target_dir / ".source_files").glob("*_report*.json"))
    
    if len(pdf_files) == 0:
        raise ValidationError("No *_categorized.pdf found in the target directory.")
        
    if len(json_files) == 0:
        raise ValidationError("No *_report.json found in the target directory.")
        
    ids = []
    
    for pdf_file in pdf_files:
        pdf_match = re.search(r'^(.*?)_categorized', pdf_file.name)
        pdf_id = pdf_match.group(1) if pdf_match else pdf_file.stem
        
        # Check if there's a matching JSON report
        matching_jsons = [j for j in json_files if j.name.startswith(f"{pdf_id}_report")]
        if not matching_jsons:
            logger.warning(f"ID mismatch: PDF ({pdf_id}) has no matching JSON report.")
            continue
            
        ids.append(pdf_id)
        
    if not ids:
        raise ValidationError("No matching PDF and JSON pairs found.")
        
    return ids

def run_append_mode(config: Any, skip_llm: bool = False) -> None:
    """Run the listener in append mode with a process-exclusive lock.
    
    Args:
        config (AppConfig): The application configuration.
    """
    import os
    import sys
    import logging
    from pathlib import Path
    from src.llm.llm import LLMClient
    from src.fs_ui.lock import acquire_lock, release_lock, LockExistsError
    from src.fs_ui.orchestrator import FSUIOrchestrator
    from dotenv import load_dotenv

    load_dotenv()

    inbox_dir = Path(config.inbox_path)
    os.makedirs(str(inbox_dir), exist_ok=True)
    
    llm_client = LLMClient(api_key=os.getenv("GEMINI_API_KEY") or "dummy")
    llm_client.skip_llm = skip_llm
    lock_path = inbox_dir / ".inbox.lock"
    
    try:
        acquire_lock(lock_path)
    except LockExistsError:
        logger.warning("Listener is already running (lockfile exists). Exiting gracefully.")
        sys.exit(0)
        
    try:
        logger.info("Listener started...")
        orchestrator = FSUIOrchestrator(config, llm_client)
        orchestrator.process_inbox()
    finally:
        release_lock(lock_path)

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
        default="gemma-4-31b-it", 
        choices=["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"],
        help="LLM model to use for the main tasks"
    )
    create_parser.add_argument(
        "--routing-model", 
        type=str, 
        choices=["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"],
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
    
    # append mode
    append_parser = subparsers.add_parser("append", help="Start the listener on the inbox")
    append_parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM calls and return mocked schemas."
    )
    
    # reconcile mode
    reconcile_parser = subparsers.add_parser("reconcile", help="Reconcile documents with updated configurations")
    reconcile_parser.add_argument("target_dir", type=Path, help="Path to the target house directory")
    reconcile_parser.add_argument("--tenants", action="store_true", help="Reconcile based on updated _tenants.yaml")
    reconcile_parser.add_argument("--dry-run", action="store_true", help="Preview the operations without moving files")
    reconcile_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
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

    if args.command == "append":
        run_append_mode(config, skip_llm=getattr(args, 'skip_llm', False))
        return 0

    if args.command == "reconcile":
        setup_logging(verbose=getattr(args, 'verbose', False))
        set_verbosity(getattr(args, 'verbose', False))
        if getattr(args, 'tenants', False):
            return run_reconcile_mode(args)
        else:
            logger.error("Must specify --tenants with reconcile mode")
            return 1

    # Ensure create mode paths are within allowed root
    target_path = args.target_dir.resolve()
    areas_root = Path(config.areas_root_path).resolve()
    
    if args.command == "create" and not target_path.is_relative_to(areas_root):
        logger.error(f"Error: Target path {target_path} is outside the allowed areas root {areas_root}")
        return 1

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
                process_unclassified_pdf(target_dir, llm_client)
                
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
                    
                    json_paths = list(target_dir.glob(f"{house_id}_report*.json")) + list((target_dir / ".source_files").glob(f"{house_id}_report*.json"))
                    json_path = json_paths[0]
                    output_json_path = output_dir / ".source_files" / f"{house_id}_1_cleaned.json"
                    
                    cleaned_pages, yaml_data = run_cleaning_pass(json_path, output_json_path, llm_client, logger, args.dry_run, house_id, target_dir)
                    documents = run_grouping_pass(cleaned_pages, house_id, output_dir, llm_client, logger, args.dry_run)
                    documents = run_routing_pass(documents, house_id, output_dir, llm_client, logger, args.dry_run, args.routing_model)
                    run_generation_pass(documents, target_dir, house_id, output_dir, logger, args.dry_run, json_path, yaml_data)
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

