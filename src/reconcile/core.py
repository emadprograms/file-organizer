import json
import os
import shutil
from pathlib import Path
import yaml

from src.core.models import PageData, TenantTimeline
from src.timeline.phase import assign_pages_to_tenants
from src.timeline.core import FileOrganizer
from src.core.schemas import DocumentGroup
from src.utils.fs import atomic_write, create_shortcut
from src.core.utils import sanitize_filename
import logging
import uuid
import re

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
        
    from src.core.state import State
    state = State(house_id, source_dir)
    
    if not state.state_file.exists():
        logger.error(f"Missing required state file: {state.state_file.name}")
        return 1
            
    with open(yaml_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
        
    pages = [PageData(**p) for p in state.data.get("cleaned_pages", [])]
    groups = [DocumentGroup(**g) for g in state.data.get("grouped_documents", [])]
    routed_data = state.data.get("manifest", {})
        
    report = {
        "ghost_adopted": 0,
        "raw_pdf_ingested": 0,
        "user_deleted": 0,
        "orphans_trashed": 0,
        "renamed_moved": 0,
        "duplicates_adopted": 0,
        "file_moves_planned": 0,
        "verification_status": "Unknown"
    }
        
    # Phase 33 & 43: Scan physical shortcuts and raw PDFs (RECON-01, RECON-02, RECON-03, RECON-07)
    from src.utils.fs import read_shortcut_target
    
    physical_lnk_files = []
    physical_pdf_files = []
    if target_dir.exists():
        for path in target_dir.rglob("*"):
            if ".source_files" in path.parts or "[Timeline View]" in path.parts:
                continue
            if path.suffix.lower() == ".lnk":
                physical_lnk_files.append(path)
            elif path.suffix.lower() == ".pdf":
                physical_pdf_files.append(path)
            
    # Phase 45: Duplicate & Renamed Shortcuts (REQ-04, REQ-05)
    vault_id_to_pages = {}
    for p in routed_data.get("per_page", []):
        if "vault_id" in p:
            vault_id_to_pages.setdefault(p["vault_id"], []).append(p)
            
    physical_lnk_by_vault = {}
    for lnk_path in physical_lnk_files:
        target_str = read_shortcut_target(str(lnk_path))
        if not target_str:
            continue
        filename = os.path.basename(target_str.replace('\\', '/'))
        if filename.startswith("doc_") and filename.endswith(".pdf"):
            vault_id = filename[4:-4]
            physical_lnk_by_vault.setdefault(vault_id, []).append(lnk_path)
            
    deleted_vault_ids = set()
    seen_vault_ids = set(physical_lnk_by_vault.keys())
    
    for vault_id, state_pages in vault_id_to_pages.items():
        if vault_id not in seen_vault_ids:
            logger.warning(f"Shortcut for vault_id {vault_id} was completely deleted. Trashing vault PDF.")
            deleted_vault_ids.add(vault_id)
            report["user_deleted"] += 1
            continue
            
        lnks = physical_lnk_by_vault[vault_id]
        unmatched_lnks = []
        unmatched_pages = []
        matched_lnks = set()
        
        for p in state_pages:
            expected_parts = p["output_file"].split("/", 1)
            expected_rel = expected_parts[1] if len(expected_parts) > 1 else expected_parts[0]
            matched = False
            for lnk in lnks:
                if lnk in matched_lnks:
                    continue
                rel_path = lnk.relative_to(target_dir).as_posix()
                if rel_path == expected_rel:
                    matched = True
                    matched_lnks.add(lnk)
                    break
            if not matched:
                unmatched_pages.append(p)
                
        for lnk in lnks:
            if lnk not in matched_lnks:
                unmatched_lnks.append(lnk)
                
        for i, p in enumerate(unmatched_pages):
            if i < len(unmatched_lnks):
                lnk = unmatched_lnks[i]
                rel_path = lnk.relative_to(target_dir).as_posix()
                report["renamed_moved"] += 1
                logger.info(f"Detected manual move/rename for {vault_id}: -> {rel_path}")
                new_target_folder = str(Path(rel_path).parent.as_posix())
                if new_target_folder == ".":
                    new_target_folder = ""
                p["target_folder"] = new_target_folder
                p["output_file"] = f"{target_dir.name}/{rel_path}"
                p["user_locked"] = True
                p["brief_arabic_title"] = lnk.stem
                
                page_idx = p["page_index"]
                if page_idx < len(pages):
                    pages[page_idx].user_locked = True
                for g in groups:
                    if g.start_page <= page_idx <= g.end_page:
                        g.user_locked = True
                        break
            else:
                # Deleted duplicate shortcut, mark page to be deleted? 
                # For now, we will add its vault_id to deleted if ALL are deleted, but if it's a partial delete (e.g. deleted 1 copy), we should remove just this per_page entry!
                logger.info(f"Detected deletion of duplicate shortcut for vault_id {vault_id}.")
                # To remove it properly, we can add a flag to `p` and filter it out below.
                p["_mark_deleted"] = True

        # If there are more unmatched physical shortcuts, they are copies/ghosts of this vault_id
        if len(unmatched_lnks) > len(unmatched_pages):
            for lnk in unmatched_lnks[len(unmatched_pages):]:
                report["duplicates_adopted"] += 1
                logger.info(f"Adopting copied/ghost shortcut for vault_id {vault_id} from {lnk.name}")
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', lnk.name)
                extracted_date = date_match.group(1) if date_match else "nodate"
                
                new_page_idx = len(pages)
                rel_path = lnk.relative_to(target_dir).as_posix()
                new_target_folder = str(Path(rel_path).parent.as_posix())
                if new_target_folder == ".":
                    new_target_folder = ""
                    
                new_page = PageData(
                    category="Unassigned",
                    content_explanation="Adopted from ghost/copied shortcut.",
                    original_index=new_page_idx,
                    user_locked=True,
                    date=extracted_date,
                    resolved_date=extracted_date if extracted_date != "nodate" else None
                )
                pages.append(new_page)
                
                new_group = DocumentGroup(
                    start_page=new_page_idx,
                    end_page=new_page_idx,
                    primary_tenant="Unassigned",
                    category="Unassigned",
                    dates=[extracted_date] if extracted_date != "nodate" else [],
                    brief_arabic_title=lnk.stem,
                    vault_id=vault_id,
                    user_locked=True
                )
                groups.append(new_group)
                
                new_p = {
                    "page_index": new_page_idx,
                    "vault_id": vault_id,
                    "output_file": f"{target_dir.name}/{rel_path}",
                    "target_folder": new_target_folder,
                    "dates": [extracted_date] if extracted_date != "nodate" else [],
                    "date": extracted_date,
                    "brief_arabic_title": lnk.stem,
                    "user_locked": True
                }
                routed_data.get("per_page", []).append(new_p)
                vault_id_to_pages[vault_id].append(new_p)

    # Adopt ghost shortcuts for vault_ids NOT in state.json
    for vault_id, lnks in physical_lnk_by_vault.items():
        if vault_id not in vault_id_to_pages:
            vault_pdf = source_dir / "vault" / f"doc_{vault_id}.pdf"
            if vault_pdf.exists():
                for lnk in lnks:
                    report["ghost_adopted"] += 1
                    logger.info(f"Adopting completely new ghost shortcut for vault_id {vault_id} from {lnk.name}")
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', lnk.name)
                    extracted_date = date_match.group(1) if date_match else "nodate"
                    
                    new_page_idx = len(pages)
                    rel_path = lnk.relative_to(target_dir).as_posix()
                    new_target_folder = str(Path(rel_path).parent.as_posix())
                    if new_target_folder == ".":
                        new_target_folder = ""
                        
                    new_page = PageData(
                        category="Unassigned",
                        content_explanation="Adopted from ghost shortcut.",
                        original_index=new_page_idx,
                        user_locked=True,
                        date=extracted_date,
                        resolved_date=extracted_date if extracted_date != "nodate" else None
                    )
                    pages.append(new_page)
                    
                    new_group = DocumentGroup(
                        start_page=new_page_idx,
                        end_page=new_page_idx,
                        primary_tenant="Unassigned",
                        category="Unassigned",
                        dates=[extracted_date] if extracted_date != "nodate" else [],
                        brief_arabic_title=lnk.stem,
                        vault_id=vault_id,
                        user_locked=True
                    )
                    groups.append(new_group)
                    
                    new_p = {
                        "page_index": new_page_idx,
                        "vault_id": vault_id,
                        "output_file": f"{target_dir.name}/{rel_path}",
                        "target_folder": new_target_folder,
                        "dates": [extracted_date] if extracted_date != "nodate" else [],
                        "date": extracted_date,
                        "brief_arabic_title": lnk.stem,
                        "user_locked": True
                    }
                    routed_data.get("per_page", []).append(new_p)
                    
    deleted_page_indices = {p["page_index"] for p in routed_data.get("per_page", []) if p.get("vault_id") in deleted_vault_ids}
    partial_deleted_page_indices = {p["page_index"] for p in routed_data.get("per_page", []) if p.get("_mark_deleted")}
    deleted_page_indices.update(partial_deleted_page_indices)
            
    if deleted_vault_ids and not getattr(args, 'dry_run', False):
        trash_dir = source_dir / ".trash"
        trash_dir.mkdir(parents=True, exist_ok=True)
        vault_dir = source_dir / "vault"
        
        for vid in deleted_vault_ids:
            vault_pdf = vault_dir / f"doc_{vid}.pdf"
            if vault_pdf.exists():
                shutil.move(str(vault_pdf), str(trash_dir / vault_pdf.name))
                
    if deleted_page_indices and not getattr(args, 'dry_run', False):
        # Remove from old_per_page
        old_per_page_filtered = [p for p in routed_data.get("per_page", []) if p["page_index"] not in deleted_page_indices]
        
        # Remove from pages and groups
        pages = [p for i, p in enumerate(pages) if i not in deleted_page_indices]
        
        # Keep groups that have at least one valid page.
        groups = [g for g in groups if g.start_page not in deleted_page_indices]
        
        # Re-index:
        idx_map = {}
        new_pages = []
        for i, p in enumerate(state.data.get("cleaned_pages", [])):
            if i not in deleted_page_indices:
                idx_map[i] = len(new_pages)
                p_obj = PageData(**p)
                p_obj.original_index = len(new_pages) # update
                new_pages.append(p_obj)
        pages = new_pages
        
        new_groups = []
        for g in state.data.get("grouped_documents", []):
            if g["start_page"] not in deleted_page_indices:
                g_obj = DocumentGroup(**g)
                g_obj.start_page = idx_map.get(g_obj.start_page, g_obj.start_page)
                g_obj.end_page = idx_map.get(g_obj.end_page, g_obj.end_page)
                new_groups.append(g_obj)
        groups = new_groups
        
        for p in old_per_page_filtered:
            p["page_index"] = idx_map.get(p["page_index"], p["page_index"])
            
        routed_data["per_page"] = old_per_page_filtered
        
    # Phase 44: Detect Orphan Vault PDFs on Disk (REQ-02)
    vault_dir = source_dir / "vault"
    if vault_dir.exists() and not getattr(args, 'dry_run', False):
        active_vault_ids = {p.get("vault_id") for p in routed_data.get("per_page", []) if p.get("vault_id")}
        trash_dir = source_dir / ".trash"
        trash_dir.mkdir(parents=True, exist_ok=True)
        for pdf_file in vault_dir.glob("doc_*.pdf"):
            vid = pdf_file.stem[4:] # doc_...
            if vid not in active_vault_ids:
                report["orphans_trashed"] += 1
                    logger.info(f"Trashing orphan vault PDF: {pdf_file.name}")
                shutil.move(str(pdf_file), str(trash_dir / pdf_file.name))
            
    # Phase 43: Raw PDF Ingestion (REQ-03)
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    known_output_files = {Path(p["output_file"]).as_posix() for p in routed_data.get("per_page", [])}
    
    for pdf_path in physical_pdf_files:
        rel_pdf = f"{target_dir.name}/{pdf_path.relative_to(target_dir).as_posix()}"
        if rel_pdf in known_output_files:
            continue
            
        if not getattr(args, 'dry_run', False):
            new_vault_id = uuid.uuid4().hex
            dest_vault_pdf = vault_dir / f"doc_{new_vault_id}.pdf"
            report["raw_pdf_ingested"] += 1
                logger.info(f"Ingesting raw PDF: {pdf_path.name} -> vault_id {new_vault_id}")
            shutil.move(str(pdf_path), str(dest_vault_pdf))
            
            lnk_path = pdf_path.with_suffix('.lnk')
            create_shortcut(str(dest_vault_pdf.resolve()), str(lnk_path.resolve()))
            
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', pdf_path.name)
            extracted_date = date_match.group(1) if date_match else "nodate"
            
            new_page_idx = len(pages)
            rel_path = lnk_path.relative_to(target_dir).as_posix()
            new_target_folder = str(Path(rel_path).parent.as_posix())
            if new_target_folder == ".":
                new_target_folder = ""
                
            new_page = PageData(
                category="Unassigned",
                content_explanation="Ingested from raw PDF.",
                original_index=new_page_idx,
                user_locked=True,
                date=extracted_date,
                resolved_date=extracted_date if extracted_date != "nodate" else None
            )
            pages.append(new_page)
            
            new_group = DocumentGroup(
                start_page=new_page_idx,
                end_page=new_page_idx,
                primary_tenant="Unassigned",
                category="Unassigned",
                dates=[extracted_date] if extracted_date != "nodate" else [],
                brief_arabic_title=lnk_path.stem,
                vault_id=new_vault_id,
                user_locked=True
            )
            groups.append(new_group)
            
            new_p = {
                "page_index": new_page_idx,
                "vault_id": new_vault_id,
                "output_file": f"{target_dir.name}/{rel_path}",
                "target_folder": new_target_folder,
                "dates": [extracted_date] if extracted_date != "nodate" else [],
                "date": extracted_date,
                "brief_arabic_title": lnk_path.stem,
                "user_locked": True
            }
            routed_data.setdefault("per_page", []).append(new_p)
            vault_id_to_pages.setdefault(new_vault_id, []).append(new_p)
        else:
            logger.info(f"[DRY RUN] Would ingest raw PDF {pdf_path.name} into vault.")
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
        report["file_moves_planned"] = len(moves)
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
        
        # Pre-calculate page counts for each vault_id
        vid_page_counts = {}
        for p in new_per_page:
            vid = p.get("vault_id")
            if vid:
                vid_page_counts[vid] = vid_page_counts.get(vid, 0) + 1
                
        for p in sorted(new_per_page, key=lambda x: (x.get('dates', [''])[0] if x.get('dates') else '', x.get('page_index', 0))):
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
                
            doc_title = re.sub(r'[\\/:*?"<>|]', '', doc_title)
            dates = p.get('dates', [])
            if not dates and p.get('date'):
                dates = [p.get('date')]
            date_str = dates[0] if dates and len(dates) > 0 and dates[0] and dates[0] != "NONE" else "nodate"
            link_name = f"{idx:03d} - {date_str} - {doc_title}.lnk"
            lnk_path = timeline_dir / link_name
            
            # The vault PDF path
            vault_pdf = target_dir / ".source_files" / "vault" / f"doc_{vid}.pdf"
            if vault_pdf.exists():
                create_shortcut(str(vault_pdf.resolve()), str(lnk_path))
            idx += vid_page_counts.get(vid, 1)
            
    # Move all files and .source_files to the new house directory if it changed
    new_house_dir = output_base_dir / full_house_id
    if target_dir != new_house_dir and not getattr(args, 'dry_run', False):
        from src.utils.fs import merge_and_remove_dir
        logger.info(f"Merging house directory {target_dir.name} -> {new_house_dir.name}")
        merge_and_remove_dir(target_dir, new_house_dir)
        
        # Update paths so state JSONs are saved correctly to the new source_dir
        source_dir = new_house_dir / ".source_files"

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
        state.state_dir = source_dir
        state.state_file = source_dir / f"{house_id}_state.json"
        
        state.data["cleaned_pages"] = [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in pages]
        state.data["grouped_documents"] = [g.model_dump() if hasattr(g, "model_dump") else g.dict() for g in groups]
        
        routed_data["per_page"] = new_per_page
        
        # Make sure to update summary file_count as well
        if "summary" in routed_data:
            routed_data["summary"]["output_file_count"] = len(set([p["output_file"] for p in new_per_page]))
            
        state.data["manifest"] = routed_data
        state.save()
                
        logger.info(f"Updated unified state JSON successfully in {source_dir}")
        
        # Save Report
        with open(source_dir / "reconcile_report.json", "w", encoding="utf-8") as rf:
            json.dump(report, rf, indent=2, ensure_ascii=False)
            
        logger.info("=== RECONCILIATION SUMMARY ===")
        logger.info(f"Raw PDFs Ingested:   {report['raw_pdf_ingested']}")
        logger.info(f"Ghosts Adopted:      {report['ghost_adopted']}")
        logger.info(f"Duplicates Adopted:  {report['duplicates_adopted']}")
        logger.info(f"Renamed/Moved:       {report['renamed_moved']}")
        logger.info(f"User Deletions:      {report['user_deleted']}")
        logger.info(f"Orphans Trashed:     {report['orphans_trashed']}")
        logger.info(f"Auto-Moves Planned:  {report['file_moves_planned']}")
        logger.info("==============================")
        
        # Auto-Verification (REQ-06)
        try:
            from src.reconcile.verify import run_verification
            # We need to pass args with the new_house_dir if it changed
            class VerifyArgs:
                target_dir = new_house_dir
            
            logger.info("Running auto-verification...")
            v_res = run_verification(VerifyArgs())
            report["verification_status"] = "Pass" if v_res == 0 else "Fail"
            
            if v_res != 0:
                logger.warning("Verification found issues after reconciliation.")
                
            # Re-save report with verification status
            with open(source_dir / "reconcile_report.json", "w", encoding="utf-8") as rf:
                json.dump(report, rf, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Auto-verification failed to run: {e}")
            report["verification_status"] = "Error"
    
    return 0
