import os
import json
import logging
from pathlib import Path
import argparse
import sys
from typing import Any

from src.core.state import State
from src.utils.fs import batch_read_shortcut_targets, atomic_write
from src.core import utils

logger = logging.getLogger(f"file_organizer.{__name__}")

def setup_logging():
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

def migrate_house(house_dir: Path, dry_run: bool = False) -> bool:
    source_dir = house_dir / ".source_files"
    if not source_dir.exists():
        return False
        
    house_id = house_dir.name.split(" - ")[0]
    state_file = source_dir / f"{house_id}_state.json"
    if not state_file.exists():
        return False
        
    logger.info(f"Processing house {house_dir.name}")
    
    try:
        state = State(house_id, source_dir)
    except Exception as e:
        logger.error(f"Failed to load state for {house_dir.name}: {e}")
        return False
        
    routed_docs = state.data.get("routed_documents")
    if not routed_docs:
        per_page = state.data.get("manifest", {}).get("per_page", [])
        if not per_page:
            logger.warning(f"No routed_documents and no manifest.per_page found in {state_file.name}. Skipping.")
            return False
            
        logger.info(f"Reconstructing routed_documents from manifest for {house_dir.name}")
        routed_docs = []
        current_vid = None
        current_group = None
        
        for p in per_page:
            vid = p.get("vault_id")
            if not vid:
                continue
            if vid != current_vid:
                if current_group is not None:
                    routed_docs.append(current_group)
                current_vid = vid
                
                # Extract info from the first page of the new group
                date_str = p.get("date", "nodate")
                folder = p.get("target_folder", "")
                output_file = p.get("output_file", "")
                filename = Path(output_file).name.replace(".lnk", ".pdf") if output_file else ""
                
                current_group = {
                    "vault_id": vid,
                    "start_page": p.get("page_index") + 1,
                    "end_page": p.get("page_index") + 1,
                    "date": date_str,
                    "folder_path": folder,
                    "filename": filename,
                    "tenant": p.get("tenant", "")
                }
            else:
                current_group["end_page"] = p.get("page_index") + 1
                
        if current_group is not None:
            routed_docs.append(current_group)
            
        # Optional: Save back the reconstructed routed docs so the state file is upgraded permanently
        state.data["routed_documents"] = routed_docs
        try:
            with atomic_write(state_file) as tmp_path:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(state.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save reconstructed routed_documents to state file: {e}")
        
    vault_id_to_doc = {}
    deduped_routed_docs = []
    for doc in routed_docs:
        vid = doc.get("vault_id")
        if vid and vid not in vault_id_to_doc:
            vault_id_to_doc[vid] = doc
            deduped_routed_docs.append(doc)
    routed_docs = deduped_routed_docs

            
    old_report = source_dir / f"{house_id}_report.json"
    if old_report.exists() and not dry_run:
        logger.info(f"Deleting old report {old_report.name}")
        try:
            old_report.unlink()
        except OSError as e:
            logger.error(f"Failed to delete {old_report.name}: {e}")
            
    timeline_dir = house_dir / "[Timeline View]"
    report_payload = []
    
    if not timeline_dir.exists():
        logger.warning(f"No [Timeline View] in {house_dir.name}. Falling back to start_page sorting.")
        sorted_docs = sorted(routed_docs, key=lambda x: x.get("start_page", 0))
        for doc in sorted_docs:
            d = dict(doc)
            date_str = "nodate"
            dates = d.get("dates", [])
            if dates and len(dates) > 0 and dates[0] and dates[0] != "NONE":
                date_str = utils.normalize_date(dates[0])
            d["date"] = date_str
            report_payload.append(d)
    else:
        lnk_files = list(timeline_dir.glob("*.lnk"))
        lnk_paths = [str(p.resolve()) for p in lnk_files]
        if lnk_paths:
            targets = batch_read_shortcut_targets(lnk_paths)
        else:
            targets = {}
            
        lnk_files.sort(key=lambda x: x.name)
        
        processed_vids = set()
        
        for lnk in lnk_files:
            target = targets.get(str(lnk.resolve()))
            if not target:
                continue
                
            target_path = Path(target)
            if target_path.name.startswith("doc_") and target_path.name.endswith(".pdf"):
                vid = target_path.name[4:-4]
                doc = vault_id_to_doc.get(vid)
                if doc:
                    if vid in processed_vids:
                        continue
                    processed_vids.add(vid)
                    d = dict(doc)
                    date_str = "nodate"
                    dates = d.get("dates", [])
                    if dates and len(dates) > 0 and dates[0] and dates[0] != "NONE":
                        date_str = utils.normalize_date(dates[0])
                    d["date"] = date_str
                    d["timeline_name"] = lnk.name
                    report_payload.append(d)
                else:
                    logger.warning(f"Could not find routed_document for vault_id {vid} linked from {lnk.name}")
                    
        # Add remaining
        remaining = [d for d in routed_docs if d.get("vault_id") and d.get("vault_id") not in processed_vids]
        if remaining:
            logger.info(f"Appending {len(remaining)} documents not found in timeline shortcuts.")
            for doc in sorted(remaining, key=lambda x: x.get("start_page", 0)):
                d = dict(doc)
                date_str = "nodate"
                dates = d.get("dates", [])
                if dates and len(dates) > 0 and dates[0] and dates[0] != "NONE":
                    date_str = utils.normalize_date(dates[0])
                d["date"] = date_str
                report_payload.append(d)

    if not dry_run:
        try:
            with atomic_write(str(old_report)) as tmp_path:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(report_payload, f, indent=2, ensure_ascii=False)
            logger.info(f"Generated new timeline-ordered report at {old_report.name}")
        except Exception as e:
            logger.error(f"Failed to save {old_report.name}: {e}")
            return False
    else:
        logger.info(f"[DRY RUN] Would generate new report at {old_report.name} with {len(report_payload)} entries.")
        
    return True

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Migrate old _report.json to timeline-ordered format")
    parser.add_argument("target", help="Target directory containing multiple house directories, or a single house directory")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify files")
    
    args = parser.parse_args()
    target_path = Path(args.target).resolve()
    
    if not target_path.exists():
        logger.error(f"Target path {target_path} does not exist.")
        sys.exit(1)
        
    if (target_path / ".source_files").exists():
        migrate_house(target_path, args.dry_run)
    else:
        for child in target_path.iterdir():
            if child.is_dir() and (child / ".source_files").exists():
                migrate_house(child, args.dry_run)

if __name__ == "__main__":
    main()
