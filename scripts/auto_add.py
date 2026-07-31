import argparse
import os
import sys
import shutil
from pathlib import Path
import logging
import json
import yaml
import tempfile
import fitz

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config import AppConfig
from src.llm.llm import LLMClient
from src.reconcile.core import run_reconcile_mode
from src.utils.logger import setup_logging
from dotenv import load_dotenv

class DummyArgs:
    pass

def main():
    parser = argparse.ArgumentParser(description="Auto Add Workflow: Reconcile -> Copy -> Pipeline -> Finalize")
    parser.add_argument("house_id", help="House ID (e.g. 502)")
    parser.add_argument("area", help="Area name (e.g. 'Safra D')")
    parser.add_argument("--additions-dir", type=Path, default=Path("D:/Safra D additions"), help="Path to additions folder")
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger("file_organizer.auto_add")
    
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    config_path = Path("config.yaml")
    if not config_path.exists():
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"
        
    config = AppConfig.load(config_path)
    areas_root = Path(config.areas_root_path)
    
    # 1. Find House Folder
    area_dir = areas_root / args.area
    if not area_dir.exists():
        logger.error(f"Area dir does not exist: {area_dir}")
        return 1
        
    matching_dirs = []
    for child in area_dir.iterdir():
        if child.is_dir() and (child.name == args.house_id or child.name.startswith(f"{args.house_id} - ")):
            matching_dirs.append(child)
            
    house_dir = None
    if matching_dirs:
        for d in matching_dirs:
            if (d / ".source_files").exists():
                house_dir = d
                break
        if not house_dir:
            house_dir = matching_dirs[0]
            
    if not house_dir:
        logger.error(f"Could not find house folder for {args.house_id} in {area_dir}")
        return 1
        
    logger.info(f"Found house directory: {house_dir}")
    
    # 2. Reconcile
    logger.info("Running reconciliation...")
    rec_args = DummyArgs()
    rec_args.target_dir = house_dir
    rec_args.dry_run = False
    rec_args.command = "reconcile"
    rec_args.tenants = True
    
    res = run_reconcile_mode(rec_args)
    if res != 0:
        logger.error("Reconciliation failed!")
        return res
    
    matching_dirs_after = []
    for child in area_dir.iterdir():
        if child.is_dir() and (child.name == args.house_id or child.name.startswith(f"{args.house_id} - ")):
            matching_dirs_after.append(child)
            
    # Sort matching dirs by length descending so we pick the fully resolved name instead of a truncated ghost dir
    matching_dirs_after.sort(key=lambda d: len(d.name), reverse=True)
    
    if matching_dirs_after:
        for d in matching_dirs_after:
            if (d / ".source_files").exists():
                house_dir = d
                break
        if not house_dir:
            house_dir = matching_dirs_after[0]
            
    if not house_dir:
        logger.error(f"Could not find house folder after reconciliation!")
        return 1
    
    # 3. Copy Addition PDF
    source_pdf = args.additions_dir / f"{args.house_id}.pdf"
    if not source_pdf.exists():
        logger.error(f"Source PDF does not exist: {source_pdf}")
        return 1
        
    inbox_dir = Path(config.inbox_path)
    inbox_dir.mkdir(parents=True, exist_ok=True)
    
    dest_pdf = inbox_dir / f"{args.house_id}.pdf"
    shutil.copy2(source_pdf, dest_pdf)
    logger.info(f"Copied {source_pdf} to {dest_pdf}")
    
    # 4. Pipeline Processing
    api_keys = []
    for k, v in os.environ.items():
        if k.startswith("GEMINI_API_KEY") and v:
            api_keys.append((k, v))
            
    if not api_keys:
        logger.error("No GEMINI_API_KEY found in environment!")
        return 1

    api_keys.sort(key=lambda x: x[0])
    current_key = api_keys[0][1]
    
    llm_client = LLMClient(api_key=current_key)
    from src.pipeline.pipeline import Pipeline
    pipeline = Pipeline(api_key=current_key)
    pipeline.client = llm_client
    
    source_files_dir = house_dir / ".source_files"
    report_path = source_files_dir / f"{args.house_id}_report.json"
    
    # We must generate a report for the addition PDF first
    import hashlib
    with open(dest_pdf, 'rb') as f:
        pdf_hash = hashlib.sha256(f.read()).hexdigest()
    
    # We can just use the pipeline's cleaning phase which internally creates the report!
    # Wait, pipeline._clean_documents uses json_path which is supposed to be the report.
    # So we must create the report first!
    from src.main import process_unclassified_pdf
    addition_report_path = inbox_dir / f"{args.house_id}_report.json"
    if addition_report_path.exists():
        os.remove(addition_report_path)
    
    process_unclassified_pdf(inbox_dir, llm_client, specific_pdf_path=dest_pdf, create_categorized_copy=False)
    
    with open(addition_report_path, 'r', encoding='utf-8') as f:
        addition_report_dicts = json.load(f)
        
    logger.info("Cleaning documents...")
    cleaned_pages, yaml_data = pipeline._clean_documents(addition_report_path, house_dir, args.house_id)
    
    logger.info("Grouping documents...")
    raw_pages = [(p.original_index, p) for p in cleaned_pages]
    documents = pipeline._group_documents(raw_pages)
    
    logger.info("Routing documents...")
    routed_docs = pipeline._route_documents(documents)
    
    # (Removed manual folder_path prefixing because FileOrganizer expects the raw Arabic topic)
    
    # 5. Extract PDFs and update tracking JSON
    from src.pipeline.runner import run_generation_pass
    # run_generation_pass will prepend to _3_routed_and_finalized.json
    run_generation_pass(
        routed_docs,
        target_dir=house_dir,
        house_id=args.house_id,
        output_dir=area_dir,
        logger=logger,
        dry_run=False,
        json_path=addition_report_path,
        yaml_data=yaml_data,
        pdf_path=dest_pdf,
        fixed_house_dir=house_dir,
        prepend_manifest=True
    )
    
    # 6. Prepend to _1_cleaned, _2_grouped, _report
    def prepend_json(path, new_data, shift_field=None, shift_by=0, is_grouped=False):
        if not path.exists():
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            sorted_keys = sorted(data.keys(), key=lambda k: int(k) if k.isdigit() else 0)
            data = [data[k] for k in sorted_keys]
        if isinstance(data, list):
            if shift_field and shift_by > 0:
                for item in data:
                    if shift_field in item:
                        item[shift_field] += shift_by
                    if is_grouped and "end_page" in item:
                        item["end_page"] += shift_by
            # Prepend new_data to data
            data = new_data + data
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    with open(report_path, 'r', encoding='utf-8') as f:
        existing_report = json.load(f)
    new_page_count = len(addition_report_dicts)
    
    prepend_json(report_path, addition_report_dicts)
    prepend_json(source_files_dir / f"{args.house_id}_1_cleaned.json", [p.model_dump() for p in cleaned_pages], "original_index", new_page_count)
    
    # Backfill legacy folder paths in _2_grouped.json using _3_routed_and_finalized.json
    grouped_path = source_files_dir / f"{args.house_id}_2_grouped.json"
    routed_path = source_files_dir / f"{args.house_id}_3_routed_and_finalized.json"
    page_to_folder = {}
    if routed_path.exists():
        with open(routed_path, 'r', encoding='utf-8') as f:
            routed_data = json.load(f)
        for p in routed_data.get("per_page", []):
            page_to_folder[p["page_index"]] = p.get("target_folder", "")
            
    if grouped_path.exists() and routed_path.exists():
        with open(grouped_path, 'r', encoding='utf-8') as f:
            grouped_data = json.load(f)
            
        changed = False
        if isinstance(grouped_data, list):
            for g in grouped_data:
                folder_val = str(g.get("folder_path", ""))
                if not folder_val or not __import__("re").match(r'^\d{2}_', folder_val):
                    start_p = g.get("start_page")
                    target = page_to_folder.get(start_p, "")
                    if target:
                        folder_name = target.split("/")[-1].split("\\")[-1]
                        g["folder_path"] = folder_name
                        changed = True
        if changed:
            with open(grouped_path, 'w', encoding='utf-8') as f:
                json.dump(grouped_data, f, ensure_ascii=False, indent=2)

    # Ensure routed_docs have correct prefix before prepending
    routed_dumps = []
    for d in routed_docs:
        dump = d.model_dump()
        folder_val = str(dump.get("folder_path", ""))
        if not folder_val or not __import__("re").match(r'^\d{2}_', folder_val):
            start_p = dump.get("start_page")
            target = page_to_folder.get(start_p, "")
            if target:
                dump["folder_path"] = target.split("/")[-1].split("\\")[-1]
        routed_dumps.append(dump)

    prepend_json(grouped_path, routed_dumps, "start_page", new_page_count, is_grouped=True)

        
    # 7. Prepend physically to _finalized.pdf
    finalized_path = house_dir / f"{args.house_id}_finalized.pdf"
    if finalized_path.exists():
        from src.pdf.compress import compress_pdf
        tmp_compressed = Path(tempfile.gettempdir()) / f"comp_{args.house_id}.pdf"
        compress_pdf(str(source_pdf), str(tmp_compressed))
        
        tmp_finalized = Path(tempfile.gettempdir()) / f"final_{args.house_id}.pdf"
        shutil.copy(str(finalized_path), str(tmp_finalized))
        
        # We want to PREPEND the new_pdf to the full_pdf.
        full_doc = fitz.open(str(tmp_finalized))
        new_doc = fitz.open(str(tmp_compressed))
        
        # To prepend, insert full_doc into new_doc at the end
        new_doc.insert_pdf(full_doc)
        
        # Regenerate TOC from the fully updated _3_routed_and_finalized.json
        if routed_path.exists():
            with open(routed_path, 'r', encoding='utf-8') as f:
                routed = json.load(f)
            toc = []
            for p in routed.get("per_page", []):
                folder = p.get("target_folder", "Unknown")
                bookmark_title = folder.replace("/", " - ").replace("\\", " - ")
                page_index = p.get("page_index", 0)
                toc.append([1, bookmark_title, page_index + 1])
            new_doc.set_toc(toc)
        
        # Save back to finalized path
        new_doc.save(str(finalized_path), garbage=4, deflate=True)
        
        full_doc.close()
        new_doc.close()
        if tmp_compressed.exists():
            os.remove(str(tmp_compressed))
        if tmp_finalized.exists():
            os.remove(str(tmp_finalized))
            
    if dest_pdf.exists():
        os.remove(str(dest_pdf))
    if addition_report_path.exists():
        os.remove(str(addition_report_path))
        
    logger.info("Workflow completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
