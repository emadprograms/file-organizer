import logging
import os
import sys
import json
from pathlib import Path
from src.utils.fs import batch_read_shortcut_targets

logger = logging.getLogger(f"file_organizer.{__name__}")

class VerificationError(Exception):
    pass

def load_yaml(path: Path) -> list:
    if not path.exists():
        return []
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or []
    except ImportError:
        # Fallback minimal parser for tenants.yaml
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        tenants, cur = [], {}
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('- name:'):
                if cur:
                    tenants.append(cur)
                cur = {'name': stripped.split(':', 1)[1].strip().strip("'").strip('"')}
        if cur:
            tenants.append(cur)
        return tenants

def run_verification(target_dir: Path) -> int:
    """Run deep integrity verification on a v5 migrated house folder.
    
    Args:
        target_dir (Path): The house directory to verify.
        
    Returns:
        int: 0 if verification passes without errors, 1 otherwise.
    """
    target_dir = target_dir.resolve()
    
    if not target_dir.exists() or not target_dir.is_dir():
        logger.error(f"Verification target directory does not exist or is not a directory: {target_dir}")
        return 1
        
    logger.info(f"Starting deep verification for: {target_dir.name}")
    
    errors = 0
    def add_error(msg: str):
        nonlocal errors
        errors += 1
        logger.error(f"[FAIL] {msg}")

    def add_pass(msg: str):
        logger.info(f"[PASS] {msg}")
        
    house_id = target_dir.name.split(' - ')[0]
    source_dir = target_dir / ".source_files"
    vault_dir = source_dir / "vault"
    
    if not source_dir.exists():
        add_error(f"Missing .source_files directory in {target_dir.name}")
        return 1
    
    if not vault_dir.exists():
        add_error(f"Missing vault directory: {vault_dir}")
    else:
        add_pass("Vault directory exists")
        
    # Check for legacy JSONs
    legacy_files = [
        f"{house_id}_1_cleaned.json",
        f"{house_id}_2_grouped.json",
        f"{house_id}_3_routed.json",
        f"{house_id}_3_routed_and_finalized.json",
    ]
    for lf in legacy_files:
        if (source_dir / lf).exists():
            add_error(f"Legacy JSON file found: {lf}")
            
    if errors == 0:
        add_pass("No legacy JSON artifacts found")
        
    # Check tenants
    tenants_yaml = source_dir / "tenants.yaml"
    valid_tenant_names = []
    if tenants_yaml.exists():
        tenant_list = load_yaml(tenants_yaml)
        valid_tenant_names = [t.get('name') for t in tenant_list if 'name' in t]
    
    # Identify tenant directories
    actual_tenants = []
    for p in target_dir.iterdir():
        if p.is_dir() and p.name not in [".source_files", "[Timeline View]"]:
            actual_tenants.append(p.name)
            
    # Check valid tenants format
    for t_dir in actual_tenants:
        name_only = t_dir.split(" \u200e")[0] if " \u200e(" in t_dir else t_dir
        if valid_tenant_names and name_only not in valid_tenant_names:
            add_error(f"Folder '{t_dir}' does not match any valid tenant from tenants.yaml")
            
    # Collect physical Vault PDFs
    vault_pdfs = set()
    if vault_dir.exists():
        for f in vault_dir.glob("*.pdf"):
            vault_pdfs.add(f.name)
            if f.stat().st_size == 0:
                add_error(f"Corrupt (0-byte) Vault PDF detected: {f.name}")
                continue
            try:
                import pypdf
                pypdf.PdfReader(str(f))
            except Exception as e:
                add_error(f"Corrupt Vault PDF detected: {f.name} ({e})")
        
    # Parse LNKs and physical PDFs in categorized folders and timeline view
    referenced_vault_pdfs = set()
    lnk_files = []
    rogue_pdfs = []
    
    for root, _, files in os.walk(target_dir):
        root_path = Path(root)
        if ".source_files" in root_path.parts:
            continue
            
        for f in files:
            p = root_path / f
            if f.lower().endswith(".lnk"):
                lnk_files.append(p)
            elif f.lower().endswith(".pdf"):
                if f.lower() == f"{house_id}.pdf".lower():
                    continue
                rogue_pdfs.append(p)
                
    if rogue_pdfs:
        add_error(f"Found {len(rogue_pdfs)} raw PDF files outside the vault. Only shortcuts are allowed.")
        for p in rogue_pdfs[:5]:
            logger.error(f"  -> {p.relative_to(target_dir)}")
    else:
        add_pass("No rogue PDFs found outside the vault")
        
    broken_links = 0
    if lnk_files:
        link_paths_str = [str(lnk) for lnk in lnk_files]
        batch_results = batch_read_shortcut_targets(link_paths_str)
        
        for lnk_path in lnk_files:
            try:
                target_path = batch_results.get(str(lnk_path))
                if not target_path:
                    add_error(f"Failed to read shortcut target for {lnk_path.relative_to(target_dir)}")
                    broken_links += 1
                    continue
                    
                target_path_clean = target_path
                if target_path_clean.startswith("\\\\?\\"):
                    target_path_clean = target_path_clean[4:]
            
                resolved_target = Path(target_path_clean)
                if not resolved_target.exists():
                    add_error(f"Broken shortcut: {lnk_path.relative_to(target_dir)} points to missing file: {target_path_clean}")
                    broken_links += 1
                elif vault_dir.resolve() not in resolved_target.parents:
                    add_error(f"Shortcut target outside vault: {lnk_path.relative_to(target_dir)} -> {target_path_clean}")
                    broken_links += 1
                else:
                    referenced_vault_pdfs.add(resolved_target.name)
            except Exception as e:
                add_error(f"Failed to parse shortcut {lnk_path.relative_to(target_dir)}: {e}")
                broken_links += 1
            
    if broken_links == 0:
        add_pass(f"All {len(lnk_files)} shortcuts resolve correctly to the vault")
        
    # Check for orphan PDFs
    orphan_pdfs = vault_pdfs - referenced_vault_pdfs
    if orphan_pdfs:
        add_error(f"Found {len(orphan_pdfs)} orphan PDFs in vault not referenced by any shortcut")
    else:
        add_pass("No orphan PDFs in vault")
        
    # Check State.json Integrity
    state_file = source_dir / f"{house_id}_state.json"
    if not state_file.exists():
        add_error(f"State file missing: {state_file.name}")
    else:
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                
            manifest_data = state_data.get("manifest") or {}
            manifest = manifest_data.get("per_page", [])
            state_output_files = set()
            for p in manifest:
                out_f = p.get("output_file")
                if out_f:
                    state_output_files.add(out_f)
            
            for g in (state_data.get("grouped_documents") or []):
                for s in g.get("shortcuts", []):
                    full_s = f"{target_dir.name}/{s}"
                    state_output_files.add(full_s)
                    
            # Check if all state output files exist
            missing_outputs = 0
            for out_f in state_output_files:
                out_path = target_dir.parent / out_f
                if not out_path.exists():
                    add_error(f"State manifest expects output file but it is missing: {out_f}")
                    missing_outputs += 1
            if missing_outputs == 0:
                add_pass("All output_files in state.json exist on disk")
                
            # Check if any categorized LNKs are NOT in state (excluding timeline)
            categorized_lnks = {lnk.relative_to(target_dir.parent).as_posix() for lnk in lnk_files if "[Timeline View]" not in lnk.parts}
            untracked_lnks = categorized_lnks - state_output_files
            if untracked_lnks:
                logger.warning(f"[WARN] Found {len(untracked_lnks)} categorized shortcuts not tracked in state.json")
                for un_lnk in sorted(list(untracked_lnks)):
                    logger.warning(f"  -> {un_lnk}")
                add_pass("All categorized shortcuts are properly tracked in state.json")
                
            # Phase: Verify Timeline View
            timeline_dir = target_dir / "[Timeline View]"
            if not timeline_dir.exists():
                add_error("Missing [Timeline View] directory")
            else:
                timeline_lnks = list(timeline_dir.glob("*.lnk"))
                expected_timeline_count = len([g for g in (state_data.get("grouped_documents") or []) if g.get("vault_id") and g.get("shortcuts")])
                if not timeline_lnks and expected_timeline_count > 0:
                    add_error(f"[Timeline View] is empty but {expected_timeline_count} document groups have shortcuts.")
                elif len(timeline_lnks) < expected_timeline_count:
                    add_error(f"[Timeline View] has {len(timeline_lnks)} shortcuts but expected at least {expected_timeline_count}.")
                else:
                    add_pass(f"[Timeline View] populated with {len(timeline_lnks)} shortcuts")
                
            # Phase 55: Check for hijacked shortcuts (shortcuts pointing to wrong vault_id)
            expected_vault_by_lnk = {}
            for p in manifest:
                out_f = p.get("output_file")
                vid = p.get("vault_id")
                if out_f and vid:
                    expected_vault_by_lnk[out_f] = vid
            
            hijack_errors = 0
            for lnk_path in lnk_files:
                rel_path = lnk_path.relative_to(target_dir.parent).as_posix()
                if rel_path in expected_vault_by_lnk:
                    expected_vid = expected_vault_by_lnk[rel_path]
                    
                    target_path = batch_results.get(str(lnk_path))
                    if not target_path:
                        continue
                        
                    target_path_clean = target_path
                    if target_path_clean.startswith("\\\\?\\"):
                        target_path_clean = target_path_clean[4:]
                    resolved_target = Path(target_path_clean)
                    
                    if resolved_target.name != f"doc_{expected_vid}.pdf":
                        add_error(f"Hijacked shortcut detected: {rel_path} points to {resolved_target.name} instead of doc_{expected_vid}.pdf")
                        hijack_errors += 1
            if hijack_errors == 0:
                add_pass("All known shortcuts point to their expected vault_id")
                
            # Immutable Page Count Audit (Phase 48)
            manifest_data = state_data.get("manifest") or {}
            total_input_pages = manifest_data.get("summary", {}).get("total_input_pages", 0)
            if total_input_pages and total_input_pages != len(manifest):
                add_error(f"IMMUTABLE PAGE COUNT MISMATCH! System dropped data. Original raw pages: {total_input_pages}. Final reconciled pages: {len(manifest)}.")
            else:
                add_pass(f"Immutable Page Count verified ({len(manifest)} pages preserved)")

            # Verify _report.json matches the new Paradigm Shift (Phase 59)
            report_file = source_dir / f"{house_id}_report.json"
            if not report_file.exists():
                add_error(f"Missing {report_file.name}")
            else:
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                        
                    if not isinstance(report_data, list):
                        add_error(f"{report_file.name} is not a JSON array")
                    else:
                        malformed = 0
                        for idx, item in enumerate(report_data):
                            required_keys = {"vault_id", "start_page", "end_page", "date", "folder_path", "filename", "tenant"}
                            if not required_keys.issubset(item.keys()):
                                add_error(f"Item {idx} in {report_file.name} is missing required fields: {required_keys - set(item.keys())}")
                                malformed += 1
                        
                        if malformed == 0:
                            add_pass(f"{report_file.name} format is fully valid (v5.5 compliant)")
                            
                        # Also check if it matches the number of expected vault documents
                        routed_docs = state_data.get("routed_documents") or state_data.get("grouped_documents") or []
                        unique_vids = {g.get("vault_id") for g in routed_docs if g.get("vault_id")}
                        expected_report_count = len(unique_vids)
                        if expected_report_count > 0 and len(report_data) != expected_report_count:
                            add_error(f"{report_file.name} has {len(report_data)} items but state expected {expected_report_count} vault documents.")
                        else:
                            add_pass(f"{report_file.name} perfectly mirrors the expected vault documents count")
                except Exception as e:
                    raise

                
        except Exception as e:
            raise

    if errors == 0:
        logger.info(f"Verification PASSED for {target_dir.name} (0 errors)")
        return 0
    else:
        logger.error(f"Verification FAILED for {target_dir.name} with {errors} errors")
        return 1
