import re

def update_reconcile():
    with open("src/reconcile/core.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    old_block = """    vault_id_to_page = {}
    for p in routed_data.get("per_page", []):
        if "vault_id" in p:
            vault_id_to_page[p["vault_id"]] = p
            
    seen_vault_ids = set()
    
    for lnk_path in physical_lnk_files:
        target_str = read_shortcut_target(str(lnk_path))
        if not target_str:
            continue
            
        filename = os.path.basename(target_str.replace('\\\\', '/'))
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
                            
            else:
                # Phase 43: Ghost Shortcut Adoption (REQ-01)
                vault_pdf = source_dir / "vault" / f"doc_{vault_id}.pdf"
                if vault_pdf.exists():
                    logger.info(f"Adopting ghost shortcut for vault_id {vault_id} from {lnk_path.name}")
                    date_match = re.search(r'(\\d{4}-\\d{2}-\\d{2})', lnk_path.name)
                    extracted_date = date_match.group(1) if date_match else "nodate"
                    
                    new_page_idx = len(pages)
                    
                    rel_path = lnk_path.relative_to(target_dir).as_posix()
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
                        brief_arabic_title=lnk_path.stem,
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
                        "brief_arabic_title": lnk_path.stem,
                        "user_locked": True
                    }
                    routed_data.get("per_page", []).append(new_p)
                    vault_id_to_page[vault_id] = new_p
                            
    # Phase 44: Detect user deletions (REQ-02)
    deleted_vault_ids = set()
    for vault_id, p in list(vault_id_to_page.items()):
        if vault_id not in seen_vault_ids:
            logger.warning(f"Shortcut for vault_id {vault_id} was deleted. Trashing vault PDF.")
            deleted_vault_ids.add(vault_id)"""
            
    new_block = """    # Phase 45: Duplicate & Renamed Shortcuts (REQ-04, REQ-05)
    vault_id_to_pages = {}
    for p in routed_data.get("per_page", []):
        if "vault_id" in p:
            vault_id_to_pages.setdefault(p["vault_id"], []).append(p)
            
    physical_lnk_by_vault = {}
    for lnk_path in physical_lnk_files:
        target_str = read_shortcut_target(str(lnk_path))
        if not target_str:
            continue
        filename = os.path.basename(target_str.replace('\\\\', '/'))
        if filename.startswith("doc_") and filename.endswith(".pdf"):
            vault_id = filename[4:-4]
            physical_lnk_by_vault.setdefault(vault_id, []).append(lnk_path)
            
    deleted_vault_ids = set()
    seen_vault_ids = set(physical_lnk_by_vault.keys())
    
    for vault_id, state_pages in vault_id_to_pages.items():
        if vault_id not in seen_vault_ids:
            logger.warning(f"Shortcut for vault_id {vault_id} was completely deleted. Trashing vault PDF.")
            deleted_vault_ids.add(vault_id)
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
                logger.info(f"Adopting copied/ghost shortcut for vault_id {vault_id} from {lnk.name}")
                date_match = re.search(r'(\\d{4}-\\d{2}-\\d{2})', lnk.name)
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
                    logger.info(f"Adopting completely new ghost shortcut for vault_id {vault_id} from {lnk.name}")
                    date_match = re.search(r'(\\d{4}-\\d{2}-\\d{2})', lnk.name)
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
                    
    # Handle partial deletions (duplicate shortcuts removed)
    partial_deleted_page_indices = {p["page_index"] for p in routed_data.get("per_page", []) if p.get("_mark_deleted")}
    if partial_deleted_page_indices:
        deleted_page_indices = deleted_page_indices | partial_deleted_page_indices if 'deleted_page_indices' in locals() else partial_deleted_page_indices
    else:
        # Initialize if not present
        if 'deleted_page_indices' not in locals():
            deleted_page_indices = set()
            
    # Phase 44: Detect user deletions (REQ-02)
    # The actual trashing of completely deleted vault IDs is handled below
    """
    if old_block in content:
        print("Block found!")
        content = content.replace(old_block, new_block)
        with open("src/reconcile/core.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated core.py!")
    else:
        print("Block not found!")
        
if __name__ == "__main__":
    update_reconcile()
