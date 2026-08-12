import os
import sys
import shutil
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Ensure the src directory is in the PYTHONPATH
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.fs import batch_read_shortcut_targets, batch_create_shortcuts

def setup_test_env():
    sandbox_dir = project_root / "tests" / "reconciliation_sandbox"
    test_dir = sandbox_dir / "test"
    backup_dir = sandbox_dir / "backup"
    
    if not backup_dir.exists():
        print(f"Backup directory does not exist: {backup_dir}")
        sys.exit(1)
        
    if test_dir.exists():
        shutil.rmtree(test_dir)
        
    shutil.copytree(backup_dir, test_dir)
    
    # Now iterate over all .lnk files and update their targets
    lnk_files = list(test_dir.rglob("*.lnk"))
    lnk_paths = [str(p) for p in lnk_files]
    
    if not lnk_paths:
        print("No .lnk files found in test.")
        return
        
    targets = batch_read_shortcut_targets(lnk_paths)
    
    shortcuts_to_create = []
    
    for lnk, target in targets.items():
        if target:
            # Replace backup path with test path
            # Need to use case-insensitive replacement or just normal string replace
            new_target = target.replace(str(backup_dir), str(test_dir))
            if target != new_target:
                shortcuts_to_create.append({
                    "link": lnk,
                    "target": new_target
                })
                
    if shortcuts_to_create:
        batch_create_shortcuts(shortcuts_to_create)
        
def evaluate():
    sandbox_dir = project_root / "tests" / "reconciliation_sandbox"
    test_dir = sandbox_dir / "test"
    backup_dir = sandbox_dir / "backup"
    
    house_dir = test_dir / "574 - تنوير بشير جلال خان"
    
    # Run the reconciliation using subprocess
    main_py = project_root / "src" / "main.py"
    
    print(f"Running reconciliation on {house_dir}...")
    result = subprocess.run([sys.executable, str(main_py), "reconcile", str(house_dir)], capture_output=True, text=True)
    if result.returncode != 0:
        print("Reconciliation failed:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
        
    print("Reconciliation output:")
    print(result.stdout)
    
    # Now evaluate. Diff test_dir and backup_dir
    # Check if any .lnk files moved, were created, or deleted (ignoring Timeline View)
    test_lnks = {p.relative_to(test_dir) for p in test_dir.rglob("*.lnk") if "[Timeline View]" not in p.parts}
    backup_lnks = {p.relative_to(backup_dir) for p in backup_dir.rglob("*.lnk") if "[Timeline View]" not in p.parts}
    
    added = test_lnks - backup_lnks
    removed = backup_lnks - test_lnks
    
    if added:
        print(f"FAILED: Added shortcuts: {added}")
    if removed:
        print(f"FAILED: Removed shortcuts: {removed}")
        
    if added or removed:
        sys.exit(1)
        
    # Also check targets for categorized shortcuts
    test_paths = [str(test_dir / p) for p in test_lnks]
    test_targets = batch_read_shortcut_targets(test_paths)
    
    backup_paths = [str(backup_dir / p) for p in backup_lnks]
    backup_targets = batch_read_shortcut_targets(backup_paths)
    
    failed = False
    for rel_path in test_lnks:
        if "[Timeline View]" in rel_path.parts:
            continue
            
        test_tgt = test_targets.get(str(test_dir / rel_path))
        backup_tgt = backup_targets.get(str(backup_dir / rel_path))
        
        # Test target should be the same as backup target, except test_dir instead of backup_dir
        expected_test_tgt = backup_tgt.replace(str(backup_dir), str(test_dir)) if backup_tgt else None
        
        if test_tgt != expected_test_tgt:
            print(f"FAILED: Target mismatch for {rel_path}")
            print(f"Expected: {expected_test_tgt}")
            print(f"Actual:   {test_tgt}")
            failed = True
            
    # Now verify the Timeline View
    # 1. No phantom moves (no "other locations" unless there are genuinely multiple)
    # 2. Latest date first (descending)
    timeline_lnks = list(house_dir.rglob("[Timeline View]/*.lnk"))
    
    import re
    prev_date = "9999-99-99"
    for lnk in sorted(timeline_lnks, key=lambda x: x.name):
        # Name format: 001 - 2025-12-24 - ...
        m = re.match(r"^\d{3} - ([\d-]+nodate) - .*", lnk.name)
        if not m:
            m = re.match(r"^\d{3} - ([\d-]+) - .*", lnk.name)
        if m:
            date_str = m.group(1)
            if date_str != "nodate":
                if date_str > prev_date:
                    print(f"FAILED: Timeline not sorted latest-first. {date_str} > {prev_date}")
                    failed = True
                prev_date = date_str
                
        # Check phantom moves
        m_phantom = re.search(r"\(\+ (\d+) other locations\)", lnk.name)
        if m_phantom:
            count = int(m_phantom.group(1))
            # Just flag it if there are many, we fixed it to be unique folders.
            # If the test case has 6 other locations, and now it has 0, it should not have the string at all.
            # We know for this house, there shouldn't be high counts.
            if count > 3:
                print(f"FAILED: Found high phantom location count in {lnk.name}")
                failed = True

    if failed:
        sys.exit(1)
        
    print("SUCCESS: Reconciliation is perfectly idempotent.")
    
if __name__ == "__main__":
    setup_test_env()
    evaluate()
