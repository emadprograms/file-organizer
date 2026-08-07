import os
import json
import logging
import shutil
from pathlib import Path
from typing import Any
import fitz

logger = logging.getLogger(f"file_organizer.{__name__}")


def run_cleaning_pass(json_path: Path, state: Any, llm_client: Any, logger: logging.Logger, dry_run: bool, house_id: str, target_dir: Path) -> tuple[list[Any], dict[str, Any] | None]:
    """Run the first pass of the document pipeline: Cleaning."""
    from src.core.models import PageData
    import yaml
    
    yaml_cache_path = state.state_dir / f"{house_id}_1_tenants.yaml"
    
    if state.data.get("cleaned_pages"):
        logger.info(f"Skipping Pass 1 (found in state). Loading cleaned data.")
        cleaned_pages = [PageData(**p) for p in state.data["cleaned_pages"]]
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
        state.data["cleaned_pages"] = [p.model_dump() for p in cleaned_pages]
        state.save()
        if yaml_data:
            from src.utils.fs import atomic_write
            with atomic_write(str(yaml_cache_path)) as tmp_path:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False)
        logger.info(f"Wrote cleaned data to state")
    else:
        logger.info(f"  [DRY RUN] Would write cleaned data to state")
        
    return cleaned_pages, yaml_data


def run_grouping_pass(cleaned_pages: list[Any], state: Any, house_id: str, output_dir: Path, llm_client: Any, logger: logging.Logger, dry_run: bool) -> list[Any]:
    """Run the second pass of the document pipeline: Grouping."""
    from src.pipeline.pipeline import Pipeline
    from src.core.schemas import DocumentGroup
    
    if state.data.get("grouped_documents"):
        logger.info(f"Skipping Pass 2 Grouping (found in state). Loading grouped documents.")
        return [DocumentGroup(**d) for d in state.data["grouped_documents"]]
            
    logger.info("Starting Pass 2 — Grouping")
    raw_pages = [(p.original_index, p) for p in cleaned_pages]
    
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY") or "dummy")
    pipeline.client = llm_client
    
    documents = pipeline._group_documents(raw_pages, None)
    
    if not dry_run:
        state.data["grouped_documents"] = [doc.model_dump() for doc in documents]
        state.save()
        logger.info(f"Wrote grouped documents to state")
    else:
        logger.info(f"  [DRY RUN] Would write grouped documents to state")
        
    return documents


def run_routing_pass(documents: list[Any], state: Any, house_id: str, output_dir: Path, llm_client: Any, logger: logging.Logger, dry_run: bool, routing_model: str | None = None) -> list[Any]:
    """Run the intermediate pass of the document pipeline: Routing."""
    from src.pipeline.pipeline import Pipeline
    from src.core.schemas import DocumentGroup
    
    if state.data.get("routed_documents"):
        logger.info(f"Skipping Pass 2.5 Routing (found in state). Loading routed documents.")
        return [DocumentGroup(**d) for d in state.data["routed_documents"]]
    
    logger.info("Starting Pass 2.5 — Routing")
    pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY") or "dummy", routing_model=routing_model)
    pipeline.client = llm_client
    
    documents = pipeline._route_documents(documents, None)
    
    if not dry_run:
        state.data["routed_documents"] = [doc.model_dump() for doc in documents]
        state.save()
        logger.info(f"Wrote routed documents to state")
    else:
        logger.info(f"  [DRY RUN] Would write routed documents to state")
        
    return documents


def run_generation_pass(documents: list[Any], target_dir: Path, house_id: str, output_dir: Path, logger: logging.Logger, dry_run: bool, json_path: Path, yaml_data: dict[str, Any] | None = None, pdf_path: Path | None = None, fixed_house_dir: Path | None = None, prepend_manifest: bool = False, state: Any = None) -> None:
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
        fixed_house_dir (Path | None): Optional fixed house directory to use in append mode.
        prepend_manifest (bool): Optional flag to prepend rather than append to the manifest in append mode.
        
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
            if not pdf_file.is_file():
                continue
            with fitz.open(str(pdf_file)) as doc:
                if doc.page_count == expected_pages:
                    found_pdf = pdf_file
                    break
                    
        if found_pdf is None:
            raise ValueError(f"No PDF in {target_dir} matches the expected page count ({expected_pages}) of {json_path.name}.")
            
        pdf_path = found_pdf
    
    organizer = FileOrganizer()
    if fixed_house_dir is not None:
        per_page, full_house_id = organizer.organize(
            documents, str(pdf_path), house_id, output_dir, yaml_data=yaml_data, dry_run=dry_run, prepend_mode=True
        )
        house_dir = fixed_house_dir
    else:
        per_page, full_house_id = organizer.organize(
            documents, str(pdf_path), house_id, output_dir, yaml_data=yaml_data, dry_run=dry_run, prepend_mode=False
        )
        house_dir = output_dir / full_house_id
    
    if not dry_run and target_dir != house_dir and not pdf_path.exists():
        new_pdf_path = house_dir / pdf_path.name
        if new_pdf_path.exists():
            pdf_path = new_pdf_path

    try:
        with fitz.open(str(pdf_path)) as pdf_doc:
            total_input_pages = pdf_doc.page_count
    except Exception as e:
        logger.warning(f"Failed to open PDF {pdf_path}: {e}")
        total_input_pages = 1
    
    output_files = {p["output_file"] for p in per_page}
    summary = {
        "total_output_pages": len(per_page),
        "output_file_count": len(output_files)
    }
    
    logger.info("Running reconciliation...")
    house_dir = fixed_house_dir if fixed_house_dir is not None else output_dir / full_house_id
    run_reconciliation(summary, per_page, total_input_pages, house_id, house_dir, dry_run=dry_run, prepend=prepend_manifest)
    
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
        
        # Compress all individual generated PDFs in the vault
        vault_dir = house_dir / ".source_files" / "vault"
        vault_ids = {p.get("vault_id") for p in per_page if p.get("vault_id")}
        
        logger.info(f"Compressing {len(vault_ids)} vault PDFs...")
        for vid in vault_ids:
            abs_path = vault_dir / f"doc_{vid}.pdf"
            if abs_path.exists():
                tmp_path = abs_path.with_suffix('.tmp.pdf')
                try:
                    compress_pdf(str(abs_path), str(tmp_path))
                    if tmp_path.exists():
                        shutil.move(str(tmp_path), str(abs_path))
                except Exception as e:
                    logger.error(f"Failed to compress vault PDF {vid}: {e}")
                    if tmp_path.exists():
                        try:
                            os.remove(str(tmp_path))
                        except OSError:
                            pass
        
        if fixed_house_dir is None:
            pass
        
        source_files_dir = house_dir / ".source_files"
        source_files_dir.mkdir(parents=True, exist_ok=True)
        
        # Delete the original categorized PDF upon completion
        if pdf_path.exists() and not pdf_path.name.endswith("_finalized.pdf") and not pdf_path.name.endswith("_raw_prepend.pdf"):
            try:
                os.remove(str(pdf_path))
            except OSError as e:
                logger.warning(f"Failed to delete original PDF {pdf_path}: {e}")
                
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
        
    if state is not None and not dry_run:
        state.load()  # Reload to pick up manifest changes from run_reconciliation
        state.data["routed_documents"] = [doc.model_dump() for doc in documents]
        state.save()
        logger.info("Saved updated documents with vault_ids to state.")
        
    if not dry_run:
        sorted_docs = sorted(documents, key=lambda x: x.start_page)
        
        from src.core import utils
        report_payload = []
        for doc in sorted_docs:
            d = doc.model_dump(exclude_none=True)
            date_str = "nodate"
            if doc.dates and len(doc.dates) > 0 and doc.dates[0] and doc.dates[0] != "NONE":
                date_str = utils.normalize_date(doc.dates[0])
            d["date"] = date_str
            d["tenant"] = doc.primary_tenant or "Unknown"
            if doc.shortcuts:
                d["filename"] = Path(doc.shortcuts[0]).name
            else:
                d["filename"] = f"doc_{doc.vault_id}.pdf"
            report_payload.append(d)
            
        report_out_path = source_files_dir / f"{house_id}_report.json"
        
        from src.utils.fs import atomic_write
        with atomic_write(str(report_out_path)) as tmp_path:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(report_payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Generated new timeline-view report at {report_out_path}")
        
    logger.info(f"Successfully generated {summary['output_file_count']} PDFs in {output_dir / full_house_id}")
