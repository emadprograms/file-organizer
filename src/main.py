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
from src.core.ui import set_verbosity
from src.llm.llm import LLMClient
from src.timeline.phase import process_cleaning_phase
from src.core.exceptions import ConfigurationError, ValidationError, FileOrganizerError
from src.categorization.categorization import process_unclassified_pdf

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

def run_cleaning_pass(json_path: Path, output_json_path: Path, llm_client: Any, logger: logging.Logger, dry_run: bool, house_id: str, target_dir: Path) -> tuple[list[Any], dict[str, Any] | None]:
    """Run the first pass of the document pipeline: Cleaning.
    
    Args:
        json_path (Path): Path to the input JSON file.
        output_json_path (Path): Path to save the cleaned JSON output.
        llm_client (Any): The LLMClient instance.
        logger (logging.Logger): The logger instance.
        dry_run (bool): Whether this is a dry run.
        house_id (str): The identifier for the house.
        target_dir (Path): The target directory.
        
    Returns:
        tuple[list[Any], dict[str, Any] | None]: The cleaned pages and the loaded tenant configuration data.
    """
    yaml_cache_path = output_json_path.parent / f"{house_id}_1_tenants.yaml"
    
    if output_json_path.exists():
        logger.info(f"Skipping Pass 1 (found {output_json_path}). Loading cleaned data.")
        with open(output_json_path, 'r', encoding='utf-8') as f:
            from src.core.models import PageData
            cleaned_pages = [PageData(**p) for p in json.load(f)]
        yaml_data = None
        if yaml_cache_path.exists():
            import yaml
            with open(yaml_cache_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
        return cleaned_pages, yaml_data
            
    logger.info("Starting Pass 1 — Document Cleaning")
    from src.pipeline.pipeline import Pipeline
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY"))
    pipeline.client = llm_client
    cleaned_pages, yaml_data = pipeline._clean_documents(json_path, target_dir, house_id)
    
    unique_tenants = len(set(p.canonical_tenant for p in cleaned_pages))
    logger.info(f"Cleaned {len(cleaned_pages)} pages successfully. Resolved {unique_tenants} unique tenant(s).")
    
    if not dry_run:
        from src.utils.fs import atomic_write
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with atomic_write(str(output_json_path)) as tmp_path:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump([p.model_dump() for p in cleaned_pages], f, ensure_ascii=False, indent=2)
        if yaml_data:
            import yaml
            with atomic_write(str(yaml_cache_path)) as tmp_path:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False)
        logger.info(f"Wrote cleaned data to {output_json_path}")
    else:
        logger.info(f"  [DRY RUN] Would write cleaned data to {output_json_path}")
        
    return cleaned_pages, yaml_data

def run_grouping_pass(cleaned_pages: list[Any], house_id: str, output_dir: Path, llm_client: Any, logger: logging.Logger, dry_run: bool) -> list[Any]:
    """Run the second pass of the document pipeline: Grouping.
    
    Args:
        cleaned_pages (list[Any]): The list of cleaned page data from pass 1.
        house_id (str): The identifier for the house.
        output_dir (Path): The output directory.
        llm_client (Any): The LLMClient instance.
        logger (logging.Logger): The logger instance.
        dry_run (bool): Whether this is a dry run.
        
    Returns:
        list[Any]: The list of grouped documents.
    """
    from src.pipeline.pipeline import Pipeline
    from src.core.schemas import DocumentGroup
    
    checkpoint_dir = output_dir / ".source_files"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    grouped_checkpoint_path = checkpoint_dir / f"{house_id}_2_grouped.json"
    
    if grouped_checkpoint_path.exists():
        with open(grouped_checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
            if isinstance(checkpoint_data, list):
                logger.info(f"Skipping Pass 2 Grouping (found {grouped_checkpoint_path}). Loading grouped documents.")
                return [DocumentGroup(**d) for d in checkpoint_data]
            else:
                logger.info(f"Found midway grouping checkpoint {grouped_checkpoint_path}. Resuming Pass 2.")
            
    logger.info("Starting Pass 2 — Grouping")
    raw_pages = [(p.original_index, p) for p in cleaned_pages]
    
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY"))
    pipeline.client = llm_client
    
    documents = pipeline._group_documents(raw_pages, str(grouped_checkpoint_path))
    
    if not dry_run:
        from src.utils.fs import atomic_write
        with atomic_write(str(grouped_checkpoint_path)) as tmp_path:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump([doc.model_dump() for doc in documents], f, ensure_ascii=False, indent=2)
        logger.info(f"Wrote grouped documents to {grouped_checkpoint_path}")
    else:
        logger.info(f"  [DRY RUN] Would write grouped documents to {grouped_checkpoint_path}")
        
    return documents

def run_routing_pass(documents: list[Any], house_id: str, output_dir: Path, llm_client: Any, logger: logging.Logger, dry_run: bool, routing_model: str | None = None) -> list[Any]:
    """Run the intermediate pass of the document pipeline: Routing.
    
    Args:
        documents (list[Any]): The list of grouped documents.
        house_id (str): The identifier for the house.
        output_dir (Path): The output directory.
        llm_client (Any): The LLMClient instance.
        logger (logging.Logger): The logger instance.
        dry_run (bool): Whether this is a dry run.
        routing_model (str | None): Optional routing LLM model identifier.
        
    Returns:
        list[Any]: The updated list of routed documents.
    """
    from src.pipeline.pipeline import Pipeline
    
    checkpoint_dir = output_dir / ".source_files"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    routing_checkpoint_path = checkpoint_dir / f"{house_id}_3_routed_and_finalized.json"
    
    logger.info("Starting Pass 2.5 — Routing")
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY"), routing_model=routing_model)
    pipeline.client = llm_client
    
    documents = pipeline._route_documents(documents, str(routing_checkpoint_path))
    return documents

def run_generation_pass(documents: list[Any], target_dir: Path, house_id: str, output_dir: Path, logger: logging.Logger, dry_run: bool, json_path: Path, yaml_data: dict[str, Any] | None = None, pdf_path: Path | None = None) -> None:
    """Run the final generation pass to produce categorized PDFs.
    
    Args:
        documents (list[Any]): The routed documents.
        target_dir (Path): The original target directory.
        house_id (str): The identifier for the house.
        output_dir (Path): The final output directory.
        logger (logging.Logger): The logger instance.
        dry_run (bool): Whether this is a dry run.
        json_path (Path): Path to the JSON report file.
        yaml_data (dict[str, Any] | None): Optional YAML tenant configuration data.
        pdf_path (Path | None): Optional path to the PDF to use. Defaults to finding matching PDF by page count.
        
    Returns:
        None
    """
    from src.timeline import FileOrganizer, run_reconciliation
    
    if pdf_path is None:
        with open(json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        expected_pages = len(report_data)
        found_pdf = None
        
        for pdf_file in target_dir.glob("*.pdf"):
            with fitz.open(str(pdf_file)) as doc:
                if doc.page_count == expected_pages:
                    found_pdf = pdf_file
                    break
                    
        if found_pdf is None:
            raise ValueError(f"No PDF in {target_dir} matches the expected page count ({expected_pages}) of {json_path.name}.")
            
        pdf_path = found_pdf
    
    organizer = FileOrganizer()
    per_page, full_house_id = organizer.organize(documents, str(pdf_path), house_id, output_dir, yaml_data=yaml_data, dry_run=dry_run)
    
    house_dir = output_dir / full_house_id
    if not dry_run and target_dir != house_dir and not pdf_path.exists():
        new_pdf_path = house_dir / pdf_path.name
        if new_pdf_path.exists():
            pdf_path = new_pdf_path

    with fitz.open(str(pdf_path)) as pdf_doc:
        total_input_pages = pdf_doc.page_count
    
    output_files = {p["output_file"] for p in per_page}
    summary = {
        "total_output_pages": len(per_page),
        "output_file_count": len(output_files)
    }
    
    logger.info("Running reconciliation...")
    run_reconciliation(summary, per_page, total_input_pages, house_id, output_dir, dry_run=dry_run)
    

    
    house_dir = output_dir / full_house_id
    original_target_dir = target_dir
    
    if not dry_run and target_dir != house_dir:
        import shutil
        new_pdf_path = house_dir / pdf_path.name
        # If the file hasn't been moved yet, move it now
        if pdf_path.exists() and not new_pdf_path.exists():
            shutil.move(str(pdf_path), str(new_pdf_path))
        elif not pdf_path.exists() and new_pdf_path.exists():
            # It was already moved/renamed by organizer
            pass
        pdf_path = new_pdf_path
        target_dir = house_dir
        
    if not dry_run:
        import shutil
        import os
        from src.pdf.compress import compress_pdf
        
        # 1. Create finalized PDF with TOC
        toc = []
        # Create unique bookmark entries (avoid duplicates if same target folder for consecutive pages, or just list all)
        # We will map each page exactly
        for entry in per_page:
            # per_page contains target_folder like 'Tenant/topic_folder'
            folder = entry.get("target_folder", "Unknown")
            bookmark_title = folder.replace("/", " - ").replace("\\", " - ")
            page_index = entry.get("page_index", 0)
            toc.append([1, bookmark_title, page_index + 1])
            
        finalized_path = house_dir / f"{house_id}_finalized.pdf"
        tmp_path = house_dir / f"{house_id}_finalized.tmp.pdf"
        
        logger.info(f"Generating TOC for {finalized_path.name}...")
        try:
            with fitz.open(str(pdf_path)) as pdf_doc:
                pdf_doc.set_toc(toc)
                pdf_doc.save(str(tmp_path))
                
            logger.info(f"Compressing finalized PDF to {finalized_path.name}...")
            compress_pdf(str(tmp_path), str(finalized_path))
            
            if tmp_path.exists():
                os.remove(str(tmp_path))
        except Exception as e:
            logger.error(f"Failed to create finalized PDF: {e}")
        
        source_files_dir = house_dir / ".source_files"
        source_files_dir.mkdir(parents=True, exist_ok=True)
        
        # Delete the original categorized PDF upon completion
        if pdf_path.exists() and not pdf_path.name.endswith("_finalized.pdf") and not pdf_path.name.endswith("_raw_append.pdf"):
            try:
                os.remove(str(pdf_path))
            except OSError as e:
                logger.warning(f"Failed to delete original PDF {pdf_path}: {e}")
                
        # Delete temporary routing state files upon completion
        routing_state_file = source_files_dir / f"{house_id}_3_routed_and_finalized_routing.json"
        routing_state_bak = source_files_dir / f"{house_id}_3_routed_and_finalized_routing.json.bak"
        for temp_file in (routing_state_file, routing_state_bak):
            if temp_file.exists():
                try:
                    os.remove(str(temp_file))
                except Exception:
                    pass
        

            
        # Move JSON and YAML files from original source directory to source_files_dir
        move_dir = original_target_dir if original_target_dir.exists() else target_dir
        for ext in ("*.json", "*.yaml", "*.yml"):
            for f in move_dir.glob(ext):
                shutil.move(str(f), str(source_files_dir / f.name))
        # Also move any JSON/YAML files from house_dir if different
        if move_dir != target_dir:
            for ext in ("*.json", "*.yaml", "*.yml"):
                for f in target_dir.glob(ext):
                    if not (source_files_dir / f.name).exists():
                        shutil.move(str(f), str(source_files_dir / f.name))
            

            
    if dry_run:
        from src.pipeline.visualizer import Visualizer
        logger.info("Invoking visualizer for dry run output...")
        visualizer = Visualizer()
        visualizer.print_summary(full_house_id, summary, per_page, documents)
        
    logger.info(f"Successfully generated {summary['output_file_count']} PDFs in {output_dir / full_house_id}")

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

