import json
import os
import shutil
from pathlib import Path
import yaml

from src.core.models import PageData, TenantTimeline
from src.timeline.phase import assign_pages_to_tenants
from src.timeline.core import FileOrganizer
from src.core.schemas import DocumentGroup
from src.utils.fs import atomic_write
from src.core.utils import sanitize_filename
import logging

logger = logging.getLogger(f"file_organizer.{__name__}")

def run_reconcile_mode(args) -> int:
    """Run the reconcile mode to retroactively apply config updates.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        int: The exit status code.
    """
    target_dir = args.target_dir.resolve()
    house_id = None
    if target_dir.name and target_dir.name[0].isdigit():
        house_id = target_dir.name.split(" - ")[0]
        
    source_dir = target_dir / ".source_files"
    if not source_dir.exists():
        logger.error(f".source_files not found in {target_dir}")
        return 1
        
    yaml_paths = list(source_dir.glob("*_tenants.yaml"))
    if not yaml_paths:
        logger.error(f"No _tenants.yaml found in {source_dir}")
        return 1
    yaml_path = yaml_paths[0]
    
    if not house_id:
        house_id = yaml_path.name.split("_")[0]
        
    cleaned_path = source_dir / f"{house_id}_1_cleaned.json"
    grouped_path = source_dir / f"{house_id}_2_grouped.json"
    routed_path = source_dir / f"{house_id}_3_routed_and_finalized.json"
    
    for p in [cleaned_path, grouped_path, routed_path]:
        if not p.exists():
            logger.error(f"Missing required state file: {p.name}")
            return 1
            
    with open(yaml_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
        
    with open(cleaned_path, 'r', encoding='utf-8') as f:
        pages = [PageData(**p) for p in json.load(f)]
        
    with open(grouped_path, 'r', encoding='utf-8') as f:
        groups = [DocumentGroup(**g) for g in json.load(f)]
        
    with open(routed_path, 'r', encoding='utf-8') as f:
        routed_data = json.load(f)
        
    # Phase 33: Scan physical shortcuts (RECON-01, RECON-02, RECON-07)
    from src.utils.fs import read_shortcut_target
    
    physical_lnk_files = []
    if target_dir.exists():
        for lnk_path in target_dir.rglob("*.lnk"):
            # Skip files in .source_files or [Timeline View]
            if ".source_files" in lnk_path.parts or "[Timeline View]" in lnk_path.parts:
                continue
            physical_lnk_files.append(lnk_path)
            
    vault_id_to_page = {}
    for p in routed_data.get("per_page", []):
        if "vault_id" in p:
            vault_id_to_page[p["vault_id"]] = p
            
    seen_vault_ids = set()
    
    for lnk_path in physical_lnk_files:
        target_str = read_shortcut_target(str(lnk_path))
        if not target_str:
            continue
            
        filename = os.path.basename(target_str.replace('\\', '/'))
        if filename.startswith("doc_") and filename.endswith(".pdf"):
            vault_id = filename[4:-4]
            seen_vault_ids.add(vault_id)
            
            if vault_id in vault_id_to_page:
                p = vault_id_to_page[vault_id]
                rel_path = lnk_path.relative_to(target_dir).as_posix()
                
                expected_parts = p["output_file"].split("/", 1)
                expected_rel = expected_parts[1] if len(expected_parts) > 1 else expected_parts[0]
                
                if rel_path != expected_rel:
                    logger.info(f"Detected manual move for {vault_id}: {expected_rel} -> {rel_path}")
                    new_target_folder = str(Path(rel_path).parent.as_posix())
                    if new_target_folder == ".":
                        new_target_folder = ""
                        
                    p["target_folder"] = new_target_folder
                    p["output_file"] = f"{target_dir.name}/{rel_path}"
                    p["user_locked"] = True
                    
                    page_idx = p["page_index"]
                    if page_idx < len(pages):
                        pages[page_idx].user_locked = True
                        
                    for g in groups:
                        if g.start_page <= page_idx <= g.end_page:
                            g.user_locked = True
                            break
                            
    for vault_id, p in vault_id_to_page.items():
        if vault_id not in seen_vault_ids:
            logger.warning(f"Shortcut for vault_id {vault_id} was deleted or missing.")
    timelines = []
    for t in yaml_data:
        end_d = t.get("end_date")
        max_d = "9999-12-31" if end_d == "present" else end_d
        timelines.append(TenantTimeline(
            canonical_name=t["name"],
            min_date=t["start_date"],
            max_date=max_d
        ))
        
    final_mapping = {t["name"]: t["name"] for t in yaml_data}
    
    # Reprocess the tenant assignment with updated timelines for unlocked pages
    unlocked_pages = [p for p in pages if not getattr(p, "user_locked", False)]
    assign_pages_to_tenants(unlocked_pages, timelines, final_mapping)
    
    for g in groups:
        if not getattr(g, "user_locked", False):
            # Re-assign primary_tenant using the first page's canonical tenant
            g.primary_tenant = pages[g.start_page].canonical_tenant
        
    organizer = FileOrganizer()
    tenant_folder_names, latest_tenant = organizer.compute_tenant_folders(groups, yaml_data)
    
    if latest_tenant:
        full_house_id = f"{house_id} - {latest_tenant}"
    else:
        full_house_id = house_id
        
    if target_dir.name.startswith(house_id):
        output_base_dir = target_dir.parent
    else:
        output_base_dir = target_dir
        
    old_per_page = routed_data.get("per_page", [])
    new_per_page = []
    
    moves = set()
    for p in old_per_page:
        page_idx = p["page_index"]
        old_output_file = p["output_file"]
        
        file_name = Path(old_output_file).name
        parts = p["target_folder"].split("/", 1)
        topic = parts[1] if len(parts) > 1 else ""
        
        new_tenant = pages[page_idx].canonical_tenant
        if new_tenant and not new_tenant.startswith("Unassigned") and not new_tenant.startswith("غير محدد"):
            new_tenant_folder = tenant_folder_names.get(new_tenant, sanitize_filename(new_tenant))
        else:
            new_tenant_folder = tenant_folder_names.get("Unassigned", "غير مخصص")
            
        new_target_folder = f"{new_tenant_folder}/{topic}" if topic else new_tenant_folder
        
        # If user_locked, retain manual placement
        if p.get("user_locked", False):
            new_target_folder = p["target_folder"]
            # Keep the old filename, but update the root folder to the new full_house_id
            old_filename = Path(p["output_file"]).name
            new_output_file = f"{full_house_id}/{new_target_folder}/{old_filename}"
        else:
            new_output_file = f"{full_house_id}/{new_target_folder}/{file_name}"
        
        if old_output_file != new_output_file:
            moves.add((old_output_file, new_output_file))
            
        new_p = dict(p)
        new_p["tenant"] = new_tenant
        new_p["target_folder"] = new_target_folder
        new_p["output_file"] = new_output_file
        new_per_page.append(new_p)
            
    if moves:
        logger.info(f"Reconciliation required. {len(moves)} distinct file moves planned.")
        for old_f, new_f in moves:
            old_path = output_base_dir / old_f
            new_path = output_base_dir / new_f
            if not getattr(args, 'dry_run', False):
                if old_path.exists():
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(old_path), str(new_path))
                    logger.info(f"Moved: {old_path.name} -> {new_path.parent.name}/{new_path.name}")
                else:
                    logger.warning(f"File not found for moving: {old_path}")
            else:
                logger.info(f"[DRY RUN] Would move: {old_path} -> {new_path}")
                
    else:
        logger.info("No file moves required based on the updated tenants.")
        
    # Phase 33: RECON-06 Regenerate [Timeline View]/
    # We always regenerate it from scratch for this house to ensure perfect sync
    if not getattr(args, 'dry_run', False):
        timeline_dir = target_dir / "[Timeline View]"
        if timeline_dir.exists():
            shutil.rmtree(str(timeline_dir))
        timeline_dir.mkdir(parents=True, exist_ok=True)
        # Create shortcuts
        idx = 1
        processed_vault_ids = set()
        for p in sorted(new_per_page, key=lambda x: (x.get('dates', [''])[0] if x.get('dates') else '', x.get('page_index', 0))):
            if "vault_id" not in p:
                continue
                
            vid = p["vault_id"]
            if vid in processed_vault_ids:
                continue
            processed_vault_ids.add(vid)

            doc_title = p.get('brief_arabic_title') or f"Doc_{p.get('page_index', 0)}"
            import re
            doc_title = re.sub(r'[\\/:*?"<>|]', '', doc_title)
            dates = p.get('dates', [])
            date_str = dates[0] if dates and len(dates) > 0 and dates[0] and dates[0] != "NONE" else "nodate"
            link_name = f"{idx:03d} - {date_str} - {doc_title}.lnk"
            lnk_path = timeline_dir / link_name
            
            # The vault PDF path
            vault_pdf = target_dir / ".source_files" / "vault" / f"doc_{vid}.pdf"
            if vault_pdf.exists():
                from src.utils.fs import create_shortcut
                create_shortcut(str(vault_pdf.resolve()), str(lnk_path))
            idx += 1
            
    # Move all files and .source_files to the new house directory if it changed
    new_house_dir = output_base_dir / full_house_id
    if target_dir != new_house_dir and not getattr(args, 'dry_run', False):
        from src.utils.fs import merge_and_remove_dir
        logger.info(f"Merging house directory {target_dir.name} -> {new_house_dir.name}")
        merge_and_remove_dir(target_dir, new_house_dir)
        
        # Update paths so state JSONs are saved correctly to the new source_dir
        source_dir = new_house_dir / ".source_files"
        cleaned_path = source_dir / cleaned_path.name
        grouped_path = source_dir / grouped_path.name
        routed_path = source_dir / routed_path.name

    # Clean up any leftover empty directories matching house_id
    if not getattr(args, 'dry_run', False):
        old_full_house_id = None
        if old_per_page:
            first_old_file = old_per_page[0].get("output_file", "")
            if first_old_file:
                old_full_house_id = first_old_file.split("/")[0]
        
        candidates = [d for d in output_base_dir.iterdir() if d.is_dir() and (d.name == house_id or d.name.startswith(f"{house_id} - "))]
        for candidate in candidates:
            if candidate != new_house_dir:
                from src.utils.fs import merge_and_remove_dir
                logger.info(f"Cleaning up ghost directory: {candidate.name} -> {new_house_dir.name}")
                merge_and_remove_dir(candidate, new_house_dir)
        
    if not getattr(args, 'dry_run', False):
        with atomic_write(str(cleaned_path)) as tmp:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump([p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in pages], f, ensure_ascii=False, indent=2)
                
        with atomic_write(str(grouped_path)) as tmp:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump([g.model_dump() if hasattr(g, "model_dump") else g.dict() for g in groups], f, ensure_ascii=False, indent=2)
                
        routed_data["per_page"] = new_per_page
        
        # Make sure to update summary file_count as well
        if "summary" in routed_data:
            routed_data["summary"]["output_file_count"] = len(set([p["output_file"] for p in new_per_page]))
            
        with atomic_write(str(routed_path)) as tmp:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(routed_data, f, ensure_ascii=False, indent=2)
                
        logger.info(f"Updated state JSONs successfully in {source_dir}")
    
    return 0
