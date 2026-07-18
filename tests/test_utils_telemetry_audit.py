from typing import Any
import subprocess
import pytest
import os

def test_no_telemetry_prints() -> None:
    """
    Audit src/ to ensure no system telemetry print() statements remain.
    Allows 'console.print' and 'vprint'.
    """
    # Use grep to find all print( calls in src/
    # We exclude 'console.print' and 'vprint'
    # The regex looks for 'print(' but NOT preceded by 'console.' or 'v'
    
    # On Windows, we can use findstr or use a python script to check.
    # For portability and power, we'll use a python script.
    
    forbidden_prints = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        stripped = line.strip()
                        if "print(" in stripped:
                            # Check if it's one of the allowed ones
                            if not ("console.print" in stripped or "vprint" in stripped):
                                forbidden_prints.append(f"{path}:{i} - {stripped}")

    assert not forbidden_prints, f"Found forbidden print statements:\n" + "\n".join(forbidden_prints)
