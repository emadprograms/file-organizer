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
    
    # Reprocess the tenant assignment with updated timelines
    assign_pages_to_tenants(pages, timelines, final_mapping)
    
    for g in groups:
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
        
    # Clean up empty directories
    if not getattr(args, 'dry_run', False):
        # Also clean up the old house_dir if it is different
        old_full_house_id = None
        if old_per_page:
            first_old_file = old_per_page[0].get("output_file", "")
            if first_old_file:
                old_full_house_id = first_old_file.split("/")[0]
        
        dirs_to_clean = []
        if old_full_house_id and old_full_house_id != full_house_id:
            dirs_to_clean.append(output_base_dir / old_full_house_id)
        dirs_to_clean.append(output_base_dir / full_house_id)
        
        for house_dir in dirs_to_clean:
            if house_dir.exists():
                # Walk bottom-up to safely delete nested empty dirs
                for root, dirs, files in os.walk(str(house_dir), topdown=False):
                    if root == str(source_dir):
                        continue
                    is_empty = True
                    for f in os.listdir(root):
                        if not f.startswith("._") and f != ".DS_Store":
                            is_empty = False
                            break
                            
                    if is_empty:
                        try:
                            # Remove any leftover macOS ghost files first
                            for f in os.listdir(root):
                                junk_path = os.path.join(root, f)
                                try:
                                    os.remove(junk_path)
                                except Exception:
                                    pass
                            os.rmdir(root)
                            logger.info(f"Removed empty directory: {root}")
                        except Exception:
                            pass
        
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
