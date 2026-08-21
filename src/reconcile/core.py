import json
import os
import sys
import shutil
from pathlib import Path
import yaml
import fitz


from src.core.models import PageData, TenantTimeline
from src.timeline.phase import assign_pages_to_tenants
from src.timeline.core import FileOrganizer
from src.core.schemas import DocumentGroup
from src.utils.fs import atomic_write, create_shortcut
from src.core.utils import sanitize_filename, normalize_date
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
    if getattr(args, 'dry_run', False) and sys.platform == 'win32':
        if sys.stdout.encoding.lower() != 'utf-8':
            logger.warning("Terminal encoding is not UTF-8. Arabic characters may not render correctly.")
            logger.warning("Recommend setting environment variable: PYTHONIOENCODING=utf8")
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    target_dir = args.target_dir.resolve()
    house_id = None
        
    if not target_dir.exists():
        logger.error(f"Target directory does not exist: {target_dir}")
        return 1
        
    source_dir = target_dir / ".source_files"
    if not source_dir.exists():
        logger.error(f".source_files not found in {target_dir}")
        return 1
        
    # Phase 57: Preflight Lock Detection
    # Scan the target directory for any locked files before proceeding
    for root, dirs, files in os.walk(target_dir):
        if ".source_files" in dirs:
            dirs.remove(".source_files")
            
        for f in files:
            if f.startswith("."):
                continue
                
            fpath = Path(root) / f
            try:
                with open(fpath, 'a'):
                    pass
            except PermissionError:
                logger.error(f"ABORTED: The following file is currently locked by another process or user: {fpath}. Please ask the user to close it and try again.")
                return 1
                
    yaml_paths = [p for p in source_dir.glob("*_tenants.yaml") if p.is_file()]
    if not yaml_paths:
        logger.error(f"No _tenants.yaml found in {source_dir}")
        return 1
    yaml_path = yaml_paths[0]
    
    dumps = [p for p in source_dir.glob("*.raw_dump.json") if p.is_file()] + [p for p in source_dir.glob("*_report.json") if p.is_file()]
    if dumps:
        house_id = dumps[0].name.split(".raw_dump.json")[0].split("_report.json")[0]
    else:
        house_id = yaml_path.name.split("_")[0]
        
    from src.core.state import State
    state = State(house_id, source_dir)
    
    if not state.state_file.exists():
        logger.error(f"Missing required state file: {state.state_file.name}")
        return 1
            
    with open(yaml_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f) or []
        
    pages = [PageData(**p) for p in (state.data.get("cleaned_pages") or [])]
    groups = [DocumentGroup(**g) for g in (state.data.get("grouped_documents") or [])]
    routed_data = state.data.get("routed_documents") or {}
    if isinstance(routed_data, list):
        if len(routed_data) > 0 and "start_page" in routed_data[0]:
            logger.info("Skipping Pass 2.5 Routing (found in state). Loading routed documents.")
            groups = [DocumentGroup(**d) for d in routed_data]
            routed_data = {"per_page": []}
        elif len(routed_data) > 0 and "page_index" in routed_data[0]:
            routed_data = {"per_page": routed_data}
        else:
            routed_data = {"per_page": routed_data}
    # Dynamically infer vault_id for legacy groups that didn't get it during migration
    for g in groups:
        if not g.vault_id:
            for p in routed_data.get("per_page", []):
                if p.get("page_index") == g.start_page and "vault_id" in p:
                    g.vault_id = p["vault_id"]
                    break
    
    expected_len = len(routed_data.get("per_page", []))
        
    if len(pages) < expected_len:
        logger.warning(f"Padding missing PageData: cleaned_pages has {len(pages)} but per_page has {expected_len}")
        for i in range(len(pages), expected_len):
            p_dict = routed_data.get("per_page", [])[i]
            d = normalize_date(p_dict.get("date", "nodate"))
            pages.append(PageData(
                category="Unassigned",
                content_explanation="Padded missing page.",
                original_index=i,
                date=d,
                resolved_date=d if d != "nodate" else None,
                user_locked=p_dict.get("user_locked", False)
            ))
        
    report = {
        "ghost_adopted": 0,
        "ghost_pages_adopted": 0,
        "raw_pdf_ingested": 0,
        "raw_pdf_pages_ingested": 0,
        "user_deleted": 0,
        "orphans_trashed": 0,
        "renamed_moved": 0,
        "duplicates_adopted": 0,
        "file_moves_planned": 0,
        "shortcuts_repaired": 0,
        "verification_status": "Unknown"
    }
        
    # Phase 33 & 43: Scan physical shortcuts and raw PDFs (RECON-01, RECON-02, RECON-03, RECON-07)
    
    physical_lnk_files = []
    physical_pdf_files = []
    if target_dir.exists():
        for path in target_dir.rglob("*"):
            if ".source_files" in path.parts or "[Timeline View]" in path.parts:
                continue
            if path.suffix.lower() == ".lnk":
                physical_lnk_files.append(path)
            elif path.suffix.lower() == ".pdf":
                if "_categorized" in path.name or "_finalized" in path.name:
                    continue
                # Skip the original house PDF if it's in the root folder
                if path.parent == target_dir and path.name.lower() in [f"{house_id}.pdf".lower(), f"{target_dir.name}.pdf".lower()]:
                    logger.info(f"Skipping original house PDF from ingestion: {path.name}")
                    continue
                physical_pdf_files.append(path)
            
    # Phase 45: Duplicate & Renamed Shortcuts (REQ-04, REQ-05)
    vault_id_to_pages = {}
    for p in routed_data.get("per_page", []):
        if "vault_id" in p:
            vault_id_to_pages.setdefault(p["vault_id"], []).append(p)
            
    physical_lnk_by_vault = {}
    
    from src.utils.fs import batch_read_shortcut_targets
    str_lnk_paths = [str(lnk) for lnk in physical_lnk_files]
    target_results = batch_read_shortcut_targets(str_lnk_paths) if str_lnk_paths else {}
    
    expected_shortcut_paths = {}
    for p in routed_data.get("per_page", []):
        if "vault_id" in p and "output_file" in p:
            expected_parts = p["output_file"].split("/", 1)
            expected_rel = expected_parts[1] if len(expected_parts) > 1 else expected_parts[0]
            expected_shortcut_paths[expected_rel] = p["vault_id"]
            
    hijacked_lnks = {}
    
    for lnk_path in physical_lnk_files:
        target_str = target_results.get(os.path.abspath(str(lnk_path)))
        rel_path = lnk_path.relative_to(target_dir).as_posix()
        expected_vault_id = expected_shortcut_paths.get(rel_path)
        
        is_valid = False
        vault_id = None
        
        if target_str:
            try:
                target_path = Path(target_str).resolve()
                target_str_lower = str(target_path).lower()
                source_dir_lower = str(source_dir.resolve()).lower()
                if target_str_lower.startswith(source_dir_lower):
                    filename = os.path.basename(target_str.replace('\\', '/'))
                    if filename.startswith("doc_") and filename.endswith(".pdf"):
                        vault_id = filename[4:-4]
                        is_valid = True
                else:
                    logger.info(f"Ignoring external shortcut pointing outside source_dir: {lnk_path} -> {target_str}")
            except Exception as e:
                logger.warning(f"Error checking shortcut target path {target_str}: {e}")
                
        if expected_vault_id and (not is_valid or vault_id != expected_vault_id):
            hijacked_lnks[lnk_path] = expected_vault_id
            
        if is_valid:
            physical_lnk_by_vault.setdefault(vault_id, []).append(lnk_path)
            
    temp_organizer = FileOrganizer()
    valid_tenant_folders, _ = temp_organizer.compute_tenant_folders(groups, yaml_data)
    valid_folder_names_set = set(valid_tenant_folders.values())
    
    seen_vault_ids = set(physical_lnk_by_vault.keys())
    deleted_vault_ids = set()
    
    for vault_id, state_pages in vault_id_to_pages.items():
        if vault_id not in seen_vault_ids:
            repaired_lnks_for_vault = [lnk for lnk, ev_id in hijacked_lnks.items() if ev_id == vault_id]
            if repaired_lnks_for_vault:
                for lnk in repaired_lnks_for_vault:
                    logger.info("Auto-repairing hijacked shortcut...")
                    report["shortcuts_repaired"] += 1
                    physical_lnk_by_vault.setdefault(vault_id, []).append(lnk)
                    for other_vid, other_lnks in physical_lnk_by_vault.items():
                        if other_vid != vault_id and lnk in other_lnks:
                            other_lnks.remove(lnk)
            else:
                logger.warning(f"Shortcut for vault_id {vault_id} was completely deleted. Trashing vault PDF.")
                deleted_vault_ids.add(vault_id)
                report["user_deleted"] += 1
                continue
                
        else:
            repaired_lnks_for_vault = [lnk for lnk, ev_id in hijacked_lnks.items() if ev_id == vault_id]
            for lnk in repaired_lnks_for_vault:
                if lnk not in physical_lnk_by_vault[vault_id]:
                    logger.info("Auto-repairing hijacked shortcut...")
                    report["shortcuts_repaired"] += 1
                    physical_lnk_by_vault[vault_id].append(lnk)
                    for other_vid, other_lnks in physical_lnk_by_vault.items():
                        if other_vid != vault_id and lnk in other_lnks:
                            other_lnks.remove(lnk)
            
        lnks = physical_lnk_by_vault[vault_id]
        unmatched_lnks = []
        unmatched_pages = []
        matched_lnks = set()
        
        for p in state_pages:
            expected_parts = p["output_file"].split("/", 1)
            expected_rel = expected_parts[1] if len(expected_parts) > 1 else expected_parts[0]
            matched = False
            for lnk in lnks:
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
                
                # Phase 54: Only lock if it was moved to a canonical tenant folder.
                top_level_folder = Path(rel_path).parts[0] if Path(rel_path).parts else ""
                should_lock = top_level_folder in valid_folder_names_set
                
                if should_lock:
                    p["user_locked"] = True
                    inv_dict = {v: k for k, v in valid_tenant_folders.items()}
                    new_tenant = inv_dict.get(top_level_folder, "Unassigned")
                    p["canonical_tenant"] = new_tenant
                else:
                    p["user_locked"] = False
                    logger.info(f"Top-level folder '{top_level_folder}' is not canonical. Snapping back.")
                    
                p["brief_arabic_title"] = lnk.stem
                
                page_idx = p["page_index"]
                if page_idx < len(pages) and should_lock:
                    pages[page_idx].user_locked = True
                    pages[page_idx].canonical_tenant = new_tenant
                for g in groups:
                    if g.start_page <= page_idx <= g.end_page and should_lock:
                        g.user_locked = True
                        g.primary_tenant = new_tenant
                        break
            else:
                logger.info(f"Detected deletion of duplicate shortcut for vault_id {vault_id}.")
                p["_mark_deleted"] = True

        if len(unmatched_lnks) > len(unmatched_pages):
            report["duplicates_adopted"] += len(unmatched_lnks) - len(unmatched_pages)
            logger.info(f"Detected {len(unmatched_lnks) - len(unmatched_pages)} duplicate shortcuts for vault_id {vault_id}. Mapping them to the document group.")

        for g in groups:
            if g.vault_id == vault_id:
                g.shortcuts = [lnk.relative_to(target_dir).as_posix() for lnk in lnks]
                break

    # Adopt ghost shortcuts for vault_ids NOT in state.json
    for vault_id, lnks in physical_lnk_by_vault.items():
        if vault_id not in vault_id_to_pages:
            vault_pdf = source_dir / "vault" / f"doc_{vault_id}.pdf"
            if vault_pdf.exists():
                with fitz.open(str(vault_pdf)) as doc:
                    num_pages = doc.page_count
                    
                for lnk in lnks:
                    report["ghost_adopted"] += 1
                    report["ghost_pages_adopted"] += num_pages
                    logger.info(f"Adopting completely new ghost shortcut for vault_id {vault_id} from {lnk.name} ({num_pages} pages)")
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', lnk.name)
                    extracted_date = normalize_date(date_match.group(1)) if date_match else "nodate"
                    
                    new_page_idx = len(pages)
                    rel_path = lnk.relative_to(target_dir).as_posix()
                    new_target_folder = str(Path(rel_path).parent.as_posix())
                    if new_target_folder == ".":
                        new_target_folder = ""
                        
                    top_level_folder = Path(rel_path).parts[0] if Path(rel_path).parts else ""
                    should_lock = top_level_folder in valid_folder_names_set
                    if not should_lock:
                        logger.info(f"Top-level folder '{top_level_folder}' for ghost shortcut is not canonical. Snapping back.")
                    
                    inv_dict = {v: k for k, v in valid_tenant_folders.items()}
                    new_tenant = inv_dict.get(top_level_folder, "Unassigned") if should_lock else "Unassigned"
                        
                    for i in range(num_pages):
                        new_page = PageData(
                            category="Unassigned",
                            content_explanation=f"Adopted from ghost shortcut. (Page {i+1}/{num_pages})",
                            original_index=new_page_idx + i,
                            user_locked=should_lock,
                            date=extracted_date,
                            resolved_date=extracted_date if extracted_date != "nodate" else None,
                            canonical_tenant=new_tenant if should_lock else None
                        )
                        pages.append(new_page)
                        
                        new_p = {
                            "page_index": new_page_idx + i,
                            "vault_id": vault_id,
                            "output_file": f"{target_dir.name}/{rel_path}",
                            "target_folder": new_target_folder,
                            "dates": [extracted_date] if extracted_date != "nodate" else [],
                            "date": extracted_date,
                            "brief_arabic_title": lnk.stem,
                            "user_locked": should_lock,
                            "canonical_tenant": new_tenant if should_lock else None,
                            "category": "Unassigned"
                        }
                        routed_data.setdefault("per_page", []).append(new_p)
                        
                    new_group = DocumentGroup(
                        start_page=new_page_idx,
                        end_page=new_page_idx + num_pages - 1,
                        primary_tenant=new_tenant if should_lock else "Unassigned",
                        category="Unassigned",
                        dates=[extracted_date] if extracted_date != "nodate" else [],
                        brief_arabic_title=lnk.stem,
                        vault_id=vault_id,
                        user_locked=should_lock,
                        shortcuts=[rel_path]
                    )
                    groups.append(new_group)
                    
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
        
        # Keep groups that have at least one valid page. We will handle filtering below.
        
        # Re-index:
        idx_map = {}
        for del_idx in deleted_page_indices:
            idx_map[del_idx] = None
            
        for new_i, p_obj in enumerate(pages):
            idx_map[p_obj.original_index] = new_i
            p_obj.original_index = new_i
            
        new_groups = []
        for g_obj in groups:
            curr_start = g_obj.start_page
            while curr_start <= g_obj.end_page and idx_map.get(curr_start, curr_start) is None:
                curr_start += 1
                
            if curr_start > g_obj.end_page:
                continue  # Whole group deleted
                
            curr_end = g_obj.end_page
            while curr_end >= g_obj.start_page and idx_map.get(curr_end, curr_end) is None:
                curr_end -= 1
                
            g_obj.start_page = idx_map.get(curr_start, curr_start)
            g_obj.end_page = idx_map.get(curr_end, curr_end)
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
            if not pdf_file.is_file():
                continue
            vid = pdf_file.stem[4:] # doc_...
            if vid not in active_vault_ids:
                report["orphans_trashed"] += 1
                logger.info(f"Trashing orphan vault PDF: {pdf_file.name}")
                shutil.move(str(pdf_file), str(trash_dir / pdf_file.name))
            
    # Phase 43: Raw PDF Ingestion (REQ-03)
    vault_dir = source_dir / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    known_output_files = {Path(p["output_file"]).as_posix() for p in routed_data.get("per_page", [])}
    
    from src.pdf import extract_pdf_segment, compress_pdf
    
    for pdf_path in physical_pdf_files:
        rel_pdf = f"{target_dir.name}/{pdf_path.relative_to(target_dir).as_posix()}"
        if rel_pdf in known_output_files:
            continue
            
        if not getattr(args, 'dry_run', False):
            manifest_path = pdf_path.with_name(f"{pdf_path.stem}_ingest_manifest.json")
            manifest_data = None
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                    
            is_group_manifest = isinstance(manifest_data, dict) and "groups" in manifest_data
            
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', pdf_path.name)
            extracted_date = normalize_date(date_match.group(1)) if date_match else "nodate"
            
            if is_group_manifest:
                groups_data = manifest_data["groups"]
                logger.info(f"Ingesting raw PDF as group manifest: {pdf_path.name}")
                
                for idx, group in enumerate(groups_data):
                    new_vault_id = uuid.uuid4().hex
                    dest_vault_pdf = vault_dir / f"doc_{new_vault_id}.pdf"
                    
                    start_page = group["start_page"]
                    end_page = group["end_page"]
                    num_pages = end_page - start_page + 1
                    
                    extract_pdf_segment(str(pdf_path), start_page, end_page, str(dest_vault_pdf))
                    try:
                        compress_pdf(str(dest_vault_pdf), str(dest_vault_pdf) + ".tmp.pdf")
                        shutil.move(str(dest_vault_pdf) + ".tmp.pdf", str(dest_vault_pdf))
                    except Exception as e:
                        logger.error(f"Compression failed for {dest_vault_pdf}, keeping original: {e}")
                        if os.path.exists(str(dest_vault_pdf) + ".tmp.pdf"):
                            try:
                                os.remove(str(dest_vault_pdf) + ".tmp.pdf")
                            except OSError:
                                pass
                    
                    report["raw_pdf_ingested"] += 1
                    report["raw_pdf_pages_ingested"] += num_pages
                    
                    lnk_path = pdf_path.parent / f"{pdf_path.stem}_part_{idx + 1}.lnk"
                    create_shortcut(str(dest_vault_pdf.resolve()), str(lnk_path.resolve()))
                    
                    new_page_idx = len(pages)
                    rel_path = lnk_path.relative_to(target_dir).as_posix()
                    new_target_folder = str(Path(rel_path).parent.as_posix())
                    if new_target_folder == ".":
                        new_target_folder = ""
                        
                    top_level_folder = Path(rel_path).parts[0] if Path(rel_path).parts else ""
                    should_lock = top_level_folder in valid_folder_names_set
                    if not should_lock:
                        logger.info(f"Top-level folder '{top_level_folder}' for raw PDF is not canonical. Snapping back.")
                        
                    inv_dict = {v: k for k, v in valid_tenant_folders.items()}
                    new_tenant = inv_dict.get(top_level_folder, "Unassigned") if should_lock else "Unassigned"
                    
                    cat = group.get("category") or "Unassigned"
                    m_exp_tenant = group.get("expected_tenant_name")
                    final_tenant = new_tenant if should_lock else m_exp_tenant
                    
                    for i in range(num_pages):
                        exp = group.get("content_explanation", f"Extracted from {pdf_path.name} (Page {i+1}/{num_pages})")
                        new_page = PageData(
                            category=cat,
                            content_explanation=exp,
                            expected_tenant_name=m_exp_tenant,
                            original_index=new_page_idx + i,
                            user_locked=should_lock,
                            date=extracted_date,
                            resolved_date=extracted_date if extracted_date != "nodate" else None,
                            canonical_tenant=final_tenant
                        )
                        pages.append(new_page)
                        
                        new_p = {
                            "page_index": new_page_idx + i,
                            "vault_id": new_vault_id,
                            "output_file": f"{target_dir.name}/{rel_path}",
                            "target_folder": new_target_folder,
                            "dates": [extracted_date] if extracted_date != "nodate" else [],
                            "date": extracted_date,
                            "brief_arabic_title": lnk_path.stem,
                            "user_locked": should_lock,
                            "canonical_tenant": final_tenant,
                            "expected_tenant_name": m_exp_tenant,
                            "category": cat
                        }
                        routed_data.setdefault("per_page", []).append(new_p)
                        vault_id_to_pages.setdefault(new_vault_id, []).append(new_p)
                        
                    new_group = DocumentGroup(
                        start_page=new_page_idx,
                        end_page=new_page_idx + num_pages - 1,
                        primary_tenant=final_tenant if final_tenant else "Unassigned",
                        category=cat,
                        dates=[extracted_date] if extracted_date != "nodate" else [],
                        brief_arabic_title=lnk_path.stem,
                        vault_id=new_vault_id,
                        user_locked=should_lock,
                        shortcuts=[rel_path]
                    )
                    groups.append(new_group)
                    
                try:
                    os.remove(str(pdf_path))
                except OSError as e:
                    logger.warning(f"Failed to delete {pdf_path.name}: {e}")
                    dest = source_dir / pdf_path.name
                    if not dest.exists():
                        shutil.move(str(pdf_path), str(dest))
                if manifest_path.exists():
                    try:
                        os.remove(str(manifest_path))
                    except OSError as e:
                        logger.warning(f"Failed to delete {manifest_path.name}: {e}")
                        dest = source_dir / manifest_path.name
                        if not dest.exists():
                            shutil.move(str(manifest_path), str(dest))
                        
            else:
                new_vault_id = uuid.uuid4().hex
                dest_vault_pdf = vault_dir / f"doc_{new_vault_id}.pdf"
                report["raw_pdf_ingested"] += 1
                logger.info(f"Ingesting raw PDF: {pdf_path.name} -> vault_id {new_vault_id}")
                import shutil
                shutil.move(str(pdf_path), str(dest_vault_pdf))
                
                num_pages = 1
                try:
                    import fitz
                    with fitz.open(str(dest_vault_pdf)) as doc:
                        num_pages = doc.page_count
                except Exception as e:
                    report.setdefault("corrupt_vault_files", 0)
                    report["corrupt_vault_files"] += 1
                    logger.warning(f"Failed to read PDF {dest_vault_pdf.name} to get page count, defaulting to 1: {e}")
                    
                report["raw_pdf_pages_ingested"] += num_pages
                
                lnk_path = pdf_path.with_suffix('.lnk')
                create_shortcut(str(dest_vault_pdf.resolve()), str(lnk_path.resolve()))
                
                if manifest_path.exists():
                    try:
                        import os
                        os.remove(str(manifest_path))
                    except OSError:
                        pass
                        
                new_page_idx = len(pages)
                rel_path = lnk_path.relative_to(target_dir).as_posix()
                new_target_folder = str(Path(rel_path).parent.as_posix())
                if new_target_folder == ".":
                    new_target_folder = ""
                    
                top_level_folder = Path(rel_path).parts[0] if Path(rel_path).parts else ""
                should_lock = top_level_folder in valid_folder_names_set
                if not should_lock:
                    logger.info(f"Top-level folder '{top_level_folder}' for raw PDF is not canonical. Snapping back.")
                    
                inv_dict = {v: k for k, v in valid_tenant_folders.items()}
                new_tenant = inv_dict.get(top_level_folder, "Unassigned") if should_lock else "Unassigned"
                
                for i in range(num_pages):
                    m_data = manifest_data[i] if manifest_data and isinstance(manifest_data, list) and i < len(manifest_data) else {}
                    cat = m_data.get("category", "Unassigned")
                    exp = m_data.get("content_explanation", f"Ingested from raw PDF. (Page {i+1}/{num_pages})")
                    m_date = m_data.get("date", "nodate")
                    m_exp_tenant = m_data.get("expected_tenant_name")
                    
                    new_page = PageData(
                        category=cat,
                        content_explanation=exp,
                        expected_tenant_name=m_exp_tenant,
                        original_index=new_page_idx + i,
                        user_locked=should_lock,
                        date=m_date,
                        resolved_date=m_date if m_date != "nodate" else None,
                        status="success"
                    )
                    pages.append(new_page)
                    
                    new_p = {
                        "page_index": new_page_idx + i,
                        "vault_id": new_vault_id,
                        "output_file": f"{target_dir.name}/{rel_path}",
                        "target_folder": new_target_folder,
                    }
                    routed_data.setdefault("per_page", []).append(new_p)
                    vault_id_to_pages.setdefault(new_vault_id, []).append(new_p)
                    
                first_m = manifest_data[0] if manifest_data and isinstance(manifest_data, list) and len(manifest_data) > 0 else {}
                new_group = DocumentGroup(
                    start_page=new_page_idx,
                    end_page=new_page_idx + num_pages - 1,
                    primary_tenant=new_tenant if should_lock else first_m.get("expected_tenant_name", "Unassigned"),
                    category=first_m.get("category", "Unassigned"),
                    dates=[first_m.get("date", "nodate")] if first_m.get("date", "nodate") != "nodate" else [],
                    brief_arabic_title=lnk_path.stem,
                    vault_id=new_vault_id,
                    user_locked=should_lock,
                    shortcuts=[rel_path]
                )
                groups.append(new_group)
        else:
            logger.info(f"[DRY RUN] Would ingest raw PDF {pdf_path.name} into vault.")
    timelines = []
    for t in yaml_data:
        end_d = t["end_date"]
        max_d = "9999-12-31" if end_d == "present" else end_d
        timelines.append(TenantTimeline(
            canonical_name=t["name"],
            min_date=t["start_date"],
            max_date=max_d
        ))
        
    final_mapping = {t["name"]: t["name"] for t in yaml_data}
    
    # Reprocess the tenant assignment with updated timelines for unlocked pages
    unlocked_pages = [p for p in pages if not p.user_locked]
    assign_pages_to_tenants(unlocked_pages, timelines, final_mapping)
    
    for g in groups:
        if not g.user_locked:
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
    seen_outputs = set()
    
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
            old_filename = normalize_date(Path(p["output_file"]).name)
            if new_target_folder:
                new_output_file = f"{full_house_id}/{new_target_folder}/{old_filename}"
            else:
                new_output_file = f"{full_house_id}/{old_filename}"
        else:
            if new_target_folder:
                new_output_file = f"{full_house_id}/{new_target_folder}/{file_name}"
            else:
                new_output_file = f"{full_house_id}/{file_name}"
        
        base_output_file = new_output_file
        counter = 1
        while new_output_file in seen_outputs:
            path_obj = Path(base_output_file)
            new_output_file = f"{path_obj.parent.as_posix()}/{path_obj.stem}_{counter}{path_obj.suffix}"
            counter += 1
        seen_outputs.add(new_output_file)

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
        

    # Move all files and .source_files to the new house directory if it changed
    new_house_dir = output_base_dir / full_house_id
    if target_dir != new_house_dir and not getattr(args, 'dry_run', False):
        from src.utils.fs import merge_and_remove_dir
        logger.info(f"Merging house directory {target_dir.name} -> {new_house_dir.name}")
        merge_and_remove_dir(target_dir, new_house_dir)
        
        # Update paths so state JSONs are saved correctly to the new source_dir
        source_dir = new_house_dir / ".source_files"
        
    if not getattr(args, 'dry_run', False):
        # We must rewrite categorized shortcuts if their absolute target paths are broken
        # due to folder rename, parent folder moves, or manual user copying.
        logger.info("Verifying categorized shortcuts and rewriting if necessary...")
        shortcuts_to_rewrite = []
        new_vault_dir = source_dir / "vault"
        
        all_potential_links = []
        for p in new_per_page:
            if "vault_id" in p and "output_file" in p:
                lnk_path = output_base_dir / p["output_file"]
                all_potential_links.append(str(lnk_path.resolve()))
                
        from src.utils.fs import batch_read_shortcut_targets
        existing_targets = batch_read_shortcut_targets(all_potential_links) if all_potential_links else {}
        
        for p in new_per_page:
            if "vault_id" in p and "output_file" in p:
                vault_pdf = new_vault_dir / f"doc_{p['vault_id']}.pdf"
                lnk_path = output_base_dir / p["output_file"]
                if vault_pdf.exists():
                    str_lnk = str(lnk_path.resolve())
                    str_target = str(vault_pdf.resolve())
                    
                    existing_target = existing_targets.get(str_lnk)
                    needs_rewrite = True
                    if lnk_path.exists() and existing_target:
                        if existing_target.lower() == str_target.lower():
                            needs_rewrite = False
                            
                    if needs_rewrite:
                        lnk_path.parent.mkdir(parents=True, exist_ok=True)
                        shortcuts_to_rewrite.append({
                            "target": str_target,
                            "link": str_lnk
                        })
        if shortcuts_to_rewrite:
            logger.info(f"Rewriting {len(shortcuts_to_rewrite)} categorized shortcuts...")
            from src.utils.fs import batch_create_shortcuts
            batch_create_shortcuts(shortcuts_to_rewrite)
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
                
    # Recompute shortcuts from actual final physical state to ensure perfect idempotency
    if not getattr(args, 'dry_run', False):
        from collections import defaultdict
        from src.utils.fs import batch_read_shortcut_targets
        
        final_lnks = []
        for child in new_house_dir.rglob("*.lnk"):
            if not child.is_file():
                continue
            if "[Timeline View]" not in child.parts:
                final_lnks.append(child)
                
        if final_lnks:
            targets = batch_read_shortcut_targets([str(l) for l in final_lnks])
            vault_to_shortcuts = defaultdict(list)
            
            for lnk in final_lnks:
                t = targets.get(str(lnk))
                if t:
                    filename = Path(t).name
                    if filename.startswith("doc_") and filename.endswith(".pdf"):
                        vid = filename[4:-4]
                        rel_p = lnk.relative_to(new_house_dir).as_posix()
                        vault_to_shortcuts[vid].append(rel_p)
                        
            for g in groups:
                if g.vault_id in vault_to_shortcuts:
                    g.shortcuts = vault_to_shortcuts[g.vault_id]
                    
    # Phase 33: RECON-06 Regenerate [Timeline View]/
    # We update timeline links, avoiding rewrites if the existing link is perfectly matched
    if not getattr(args, 'dry_run', False):
        timeline_dir = new_house_dir / "[Timeline View]"
        try:
            timeline_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            import time
            time.sleep(1)
            timeline_dir.mkdir(parents=True, exist_ok=True)
            
        from src.utils.fs import batch_read_shortcut_targets
        existing_timeline_links = []
        if timeline_dir.exists():
            for child in timeline_dir.iterdir():
                if child.is_file() and child.suffix.lower() == ".lnk":
                    existing_timeline_links.append(str(child.resolve()))
                    
        existing_timeline_targets = batch_read_shortcut_targets(existing_timeline_links) if existing_timeline_links else {}
        expected_timeline_links = set()

        idx = 1
        processed_vault_ids = set()
        
        shortcuts_to_create = []
        
        # Sort groups by latest date first, then start_page
        for g in sorted(groups, key=lambda x: (x.dates[0] if x.dates and x.dates[0] != "NONE" else '', x.start_page), reverse=True):
            vid = g.vault_id
            if not vid:
                continue
                
            # If no shortcuts exist for this document group, skip
            if not g.shortcuts:
                continue
                
            # Location tag
            primary_shortcut = g.shortcuts[0]
            location = Path(primary_shortcut).parent.name
            
            unique_locations = {Path(s).parent.name for s in g.shortcuts}
            extra_count = len(unique_locations) - 1
            extra = f" (+ {extra_count} other locations)" if extra_count > 0 else ""
                
            doc_title = g.brief_arabic_title
            if not doc_title:
                filename = Path(primary_shortcut).name.replace('.lnk', '').replace('.pdf', '')
                if ' - ' in filename:
                    doc_title = filename.split(' - ', 1)[1]
                else:
                    doc_title = filename
            if not doc_title:
                doc_title = f"Doc_{g.start_page}"
                
            doc_title = re.sub(r'[\\/:*?"<>|]', '', doc_title)
            
            dates = g.dates
            date_str = normalize_date(dates[0]) if dates and len(dates) > 0 and dates[0] and dates[0] != "NONE" else "nodate"
            
            link_name = f"{idx:03d} - {date_str} - {doc_title} [{location}]{extra}.lnk"
            lnk_path = timeline_dir / link_name
            str_lnk = str(lnk_path.resolve())
            expected_timeline_links.add(str_lnk.lower())
            
            # The vault PDF path
            vault_pdf = new_house_dir / ".source_files" / "vault" / f"doc_{vid}.pdf"
            if vault_pdf.exists():
                str_target = str(vault_pdf.resolve())
                existing_target = existing_timeline_targets.get(str_lnk)
                needs_rewrite = True
                if lnk_path.exists() and existing_target:
                    if existing_target.lower() == str_target.lower():
                        needs_rewrite = False
                
                if needs_rewrite:
                    shortcuts_to_create.append({
                        "target": str_target,
                        "link": str_lnk
                    })
            idx += (g.end_page - g.start_page + 1)
            
        if shortcuts_to_create:
            logger.info(f"Creating/updating {len(shortcuts_to_create)} timeline shortcuts...")
            from src.utils.fs import batch_create_shortcuts
            batch_create_shortcuts(shortcuts_to_create)
            
        for existing_link in existing_timeline_links:
            if existing_link.lower() not in expected_timeline_links:
                try:
                    os.remove(existing_link)
                    logger.info(f"Removed orphaned timeline shortcut: {Path(existing_link).name}")
                except Exception as e:
                    logger.warning(f"Could not remove orphaned timeline shortcut {existing_link}: {e}")
            
    if not getattr(args, 'dry_run', False):
        state.state_dir = source_dir
        state.state_file = source_dir / f"{house_id}_state.json"
        if state.state_file.exists():
            state.load()
        
        
        state.data["cleaned_pages"] = [p.model_dump() for p in pages]
        state.data["grouped_documents"] = [g.model_dump() for g in groups]
        
        routed_data["per_page"] = new_per_page
        
        # Make sure to update summary file_count as well
        if "summary" in routed_data:
            routed_data["summary"]["output_file_count"] = len(set([p["output_file"] for p in new_per_page]))
            
        state.data["routed_documents"] = routed_data
        state.save()
                
        logger.info(f"Updated unified state JSON successfully in {source_dir}")
        
        # Generate {house_id}_report.json format for legacy verification
        legacy_report = []
        sorted_docs = sorted(groups, key=lambda x: x.start_page)
        for g in sorted_docs:
            d = g.model_dump(exclude_none=True)
            
            date_str = "nodate"
            if g.dates and len(g.dates) > 0 and g.dates[0] and g.dates[0] != "NONE":
                date_str = normalize_date(g.dates[0])
            d["date"] = date_str
            d["tenant"] = g.primary_tenant or "Unknown"
            
            if g.shortcuts:
                d["filename"] = Path(g.shortcuts[0]).name
            else:
                d["filename"] = f"doc_{g.vault_id}.pdf"
                
            legacy_report.append(d)
            
        report_out_path = source_dir / f"{house_id}_report.json"
        with atomic_write(str(report_out_path)) as tmp_path:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(legacy_report, f, indent=2, ensure_ascii=False)
        logger.info(f"Generated new timeline-view report at {report_out_path}")

        # Save Report
        with atomic_write(str(source_dir / "reconcile_report.json")) as tmp_path:
            with open(tmp_path, "w", encoding="utf-8") as rf:
                json.dump(report, rf, indent=2, ensure_ascii=False)
            
        logger.info("=== RECONCILIATION SUMMARY ===")
        logger.info(f"Raw PDFs Ingested:   {report['raw_pdf_ingested']} ({report.get('raw_pdf_pages_ingested', 0)} pages)")
        logger.info(f"Ghosts Adopted:      {report['ghost_adopted']} ({report.get('ghost_pages_adopted', 0)} pages)")
        logger.info(f"Duplicates Adopted:  {report['duplicates_adopted']}")
        logger.info(f"Renamed/Moved:       {report['renamed_moved']}")
        logger.info(f"User Deletions:      {report['user_deleted']}")
        logger.info(f"Orphans Trashed:     {report['orphans_trashed']}")
        logger.info(f"Auto-Moves Planned:  {report['file_moves_planned']}")
        logger.info(f"Shortcuts Repaired:  {report.get('shortcuts_repaired', 0)}")
        if report.get("corrupt_vault_files", 0) > 0:
            logger.info(f"Corrupt Vault Files Detected: {report['corrupt_vault_files']}")
        logger.info("==============================")
        
        # Phase 54: Cleanup orphaned/renamed legacy folders
        allowed_dirs = {".source_files", "[Timeline View]"}
        allowed_dirs.update(tenant_folder_names.values())
        
        for child in new_house_dir.iterdir():
            if child.is_dir() and child.name not in allowed_dirs:
                # Check if it contains only shortcuts or is empty
                contains_unmanaged_files = False
                for item in child.rglob("*"):
                    if item.is_file() and item.suffix.lower() != ".lnk":
                        contains_unmanaged_files = True
                        break
                if not contains_unmanaged_files:
                    logger.info(f"Deleted orphaned/renamed legacy folder: {child.name}")
                    shutil.rmtree(str(child), ignore_errors=True)

    else:
        from src.pipeline.visualizer import Visualizer
        vis = Visualizer()
        summary = {
            "total_output_pages": len(new_per_page),
            "output_file_count": len(set([p["output_file"] for p in new_per_page]))
        }
        vis.print_summary(full_house_id, summary, new_per_page, groups)
    
    if not getattr(args, 'dry_run', False):
        output_file_count = len(set([p["output_file"] for p in new_per_page]))
        logger.info(f"Successfully generated {output_file_count} PDFs in {new_house_dir}")

    return 0
