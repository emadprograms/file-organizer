import os
import pytest
from pathlib import Path
import shutil

from src.main import get_parser, main
import sys
from unittest.mock import patch

@pytest.mark.skipif(not os.path.exists(r"D:\Areas"), reason=r"Live D:\Areas directory not available")
def test_live_migration_on_test_folder():
    """Test the migration script on a specific live test folder to ensure it works."""
    live_areas = Path(r"D:\Areas")
    
    # Find a test folder in Safra C
    safra = live_areas / "Safra C"
    if not safra.exists():
        pytest.skip("Safra C folder not found")
        
    test_folders = list(safra.glob("*[test]*"))
    if not test_folders:
        pytest.skip("No [test] folder found in Safra C")
        
    target_dir = test_folders[0]
    
    # We will test migration in dry_run mode first to ensure it doesn't break
    test_args = ["main.py", "migrate", str(target_dir), "--dry-run"]
    with patch.object(sys, 'argv', test_args):
        try:
            main()
        except Exception as e:
            pytest.fail(f"Live migration dry-run failed: {e}")

@pytest.mark.skipif(not os.path.exists(r"D:\Areas"), reason=r"Live D:\Areas directory not available")
def test_live_pipeline_on_test_folder():
    """Test the main pipeline on a specific live test folder."""
    live_areas = Path(r"D:\Areas")
    safra = live_areas / "Safra C"
    if not safra.exists():
        pytest.skip("Safra C folder not found")
        
    test_folders = list(safra.glob("*[test]*"))
    if not test_folders:
        pytest.skip("No [test] folder found in Safra C")
        
    target_dir = test_folders[0]
    
    # Run the pipeline with --skip-llm to avoid billing/time during tests
    test_args = ["main.py", "create", str(target_dir), "--skip-llm", "--dry-run"]
    with patch.object(sys, 'argv', test_args):
        try:
            main()
        except Exception as e:
            pytest.fail(f"Live pipeline dry-run failed: {e}")
