import os
import json
import uuid
import shutil
import logging
from pathlib import Path

from src.utils.fs import batch_create_shortcuts

logger = logging.getLogger(f"file_organizer.{__name__}")

def migrate_to_v5(target_dir: Path, dry_run: bool = False) -> int:
    """Migrate a v4 house directory to the v5 vault architecture.
    
    Args:
        target_dir (Path): The house directory to migrate.
        dry_run (bool): If True, only log actions without modifying files.
        
    Returns:
        int: 0 on success, 1 on failure.
    """
    target_dir = target_dir.resolve()
    if not target_dir.exists():
        logger.error(f"Target directory does not exist: {target_dir}")
        return 1
        
    source_dir = target_dir / ".source_files"
    if not source_dir.exists():
        logger.error(f".source_files not found in {target_dir}")
        return 1
        
    vault_dir = source_dir / "vault"
    if not dry_run:
        vault_dir.mkdir(parents=True, exist_ok=True)
        
    house_id = target_dir.name.split(' - ')[0]
    
    # Load all legacy JSONs
    cleaned_json = source_dir / f"{house_id}_1_cleaned.json"
    grouped_json = source_dir / f"{house_id}_2_grouped.json"
    routed_json = source_dir / f"{house_id}_3_routed_and_finalized.json"
    if not routed_json.exists():
        # Try without finalized
        routed_json = source_dir / f"{house_id}_3_routed.json"
        
    if not routed_json.exists():
        logger.error(f"Could not find routed JSON in {source_dir}")
        return 1
        
    with open(routed_json, 'r', encoding='utf-8') as f:
        state_data = json.load(f)
        
    per_page = state_data.get("per_page", [])
    if not per_page and isinstance(state_data, list):
        # Legacy format
        per_page = state_data
        state_data = {"per_page": per_page}
        
    cleaned_data = []
    if cleaned_json.exists():
        with open(cleaned_json, 'r', encoding='utf-8') as f:
            cleaned_data = json.load(f)
            
    grouped_data = []
    if grouped_json.exists():
        with open(grouped_json, 'r', encoding='utf-8') as f:
            grouped_data = json.load(f)
        
    # Find all PDFs in the house directory (excluding .source_files and [Timeline View])
    pdfs = []
    for root, _, files in os.walk(target_dir):
        root_path = Path(root)
        if ".source_files" in root_path.parts or "[Timeline View]" in root_path.parts:
            continue
        for f in files:
            if f.lower().endswith(".pdf") and not f.endswith("_finalized.pdf") and not f.endswith("_raw_prepend.pdf") and not f.endswith("_raw_append.pdf"):
                pdfs.append(root_path / f)
                
    if not pdfs:
        logger.info(f"No PDFs found to migrate in {target_dir}")
        return 0
        
    logger.info(f"Found {len(pdfs)} PDFs to migrate to vault format.")
    
    updates_made = 0
    shortcuts_to_create = []
    
    for pdf_path in pdfs:
        vid = uuid.uuid4().hex
        vault_pdf = vault_dir / f"doc_{vid}.pdf"
        lnk_path = pdf_path.with_suffix('.lnk')
        
        # Match with JSON
        rel_pdf_path = pdf_path.relative_to(target_dir.parent).as_posix()
        matched = False
        for p in per_page:
            # Check if output_file matches (either exactly or ending with)
            out_f = p.get("output_file", "")
            if out_f == rel_pdf_path or out_f.endswith(pdf_path.name):
                # Update it
                p["vault_id"] = vid
                p["output_file"] = lnk_path.relative_to(target_dir.parent).as_posix()
                p["user_locked"] = True
                matched = True
                
        if not matched:
            logger.warning(f"PDF {pdf_path.name} was not found in state JSON. It will be migrated, but lacks metadata.")
            
        if not dry_run:
            shutil.move(str(pdf_path), str(vault_pdf))
            abs_vault_target = str(vault_pdf.resolve())
            shortcuts_to_create.append({"target": abs_vault_target, "link": str(lnk_path)})
            logger.info(f"Migrated: {pdf_path.name} -> vault/doc_{vid}.pdf + shortcut")
        else:
            logger.info(f"[DRY RUN] Would migrate {pdf_path.name} -> vault/doc_{vid}.pdf + shortcut")
            
        updates_made += 1
        
    if not dry_run and shortcuts_to_create:
        batch_create_shortcuts(shortcuts_to_create)
        
    # Rebuild [Timeline View]/
    timeline_dir = target_dir / "[Timeline View]"
    if not dry_run:
        if timeline_dir.exists():
            shutil.rmtree(str(timeline_dir))
        timeline_dir.mkdir(parents=True, exist_ok=True)
        
        # Pre-calculate page counts for each vault_id
        vid_page_counts = {}
        for p in per_page:
            vid = p.get("vault_id")
            if vid:
                vid_page_counts[vid] = vid_page_counts.get(vid, 0) + 1

        idx = 1
        timeline_shortcuts = []
        processed_vault_ids = set()
        for p in sorted(per_page, key=lambda x: (x.get('dates', [''])[0] if x.get('dates') else '', x.get('page_index', 0))):
            if "vault_id" not in p:
                continue
            
            vid = p["vault_id"]
            if vid in processed_vault_ids:
                continue
            processed_vault_ids.add(vid)
            
            doc_title = p.get('brief_arabic_title')
            if not doc_title and 'output_file' in p:
                filename = Path(p['output_file']).name.replace('.lnk', '').replace('.pdf', '')
                if ' - ' in filename:
                    doc_title = filename.split(' - ', 1)[1]
                else:
                    doc_title = filename
            if not doc_title:
                doc_title = f"Doc_{p.get('page_index', 0)}"
                
            import re
            doc_title = re.sub(r'[\\/:*?"<>|]', '', doc_title)
            dates = p.get('dates', [])
            if not dates and p.get('date'):
                dates = [p.get('date')]
            date_str = dates[0] if dates and len(dates) > 0 and dates[0] and dates[0] != "NONE" else "nodate"
            link_name = f"{idx:03d} - {date_str} - {doc_title}.lnk"
            lnk_path = timeline_dir / link_name
            
            vault_pdf = vault_dir / f"doc_{vid}.pdf"
            if vault_pdf.exists():
                abs_vault_target = str(vault_pdf.resolve())
                timeline_shortcuts.append({"target": abs_vault_target, "link": str(lnk_path)})
            idx += vid_page_counts.get(vid, 1)
            
        if timeline_shortcuts:
            batch_create_shortcuts(timeline_shortcuts)
            
        # Delete finalized PDF if it exists
        for root, _, files in os.walk(target_dir):
            for f in files:
                if f.endswith("_finalized.pdf"):
                    os.remove(os.path.join(root, f))
                    
        # Save unified state.json
        from src.core.state import State
        state = State(house_id, source_dir)
        state.data["cleaned_pages"] = cleaned_data
        state.data["grouped_documents"] = grouped_data
        state.data["manifest"] = state_data
        state.save()
        
        # Delete legacy JSONs
        routed_base_json = source_dir / f"{house_id}_3_routed.json"
        for p in [cleaned_json, grouped_json, source_dir / f"{house_id}_3_routed_and_finalized.json", routed_base_json]:
            if p.exists():
                os.remove(str(p))
                
    else:
        logger.info(f"[DRY RUN] Would rebuild [Timeline View]/ with {len(per_page)} entries.")
        logger.info(f"[DRY RUN] Would save updated state to {house_id}_state.json and delete legacy files.")
        
    logger.info(f"Migration completed successfully. Migrated {updates_made} documents.")
    return 0
