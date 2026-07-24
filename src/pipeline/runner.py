import os
import json
import logging
import shutil
from pathlib import Path
from typing import Any
import fitz

logger = logging.getLogger(f"file_organizer.{__name__}")


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
    from src.core.models import PageData
    import yaml
    
    yaml_cache_path = output_json_path.parent / f"{house_id}_1_tenants.yaml"
    
    if output_json_path.exists():
        logger.info(f"Skipping Pass 1 (found {output_json_path}). Loading cleaned data.")
        with open(output_json_path, 'r', encoding='utf-8') as f:
            cleaned_pages = [PageData(**p) for p in json.load(f)]
        yaml_data = None
        if yaml_cache_path.exists():
            with open(yaml_cache_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
        return cleaned_pages, yaml_data
            
    logger.info("Starting Pass 1 — Document Cleaning")
    from src.pipeline.pipeline import Pipeline
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY") or "dummy")
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
    
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY") or "dummy")
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
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY") or "dummy", routing_model=routing_model)
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
        from src.pdf.compress import compress_pdf
        
        # 1. Create finalized PDF with TOC
        toc = []
        # Create unique bookmark entries (avoid duplicates if same target folder for consecutive pages, or just list all)
        # We will map each page exactly
        for entry in per_page:
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
