import sys
import os
import pytest
import logging
from pathlib import Path
from unittest.mock import patch

logger = logging.getLogger(f"file_organizer.{__name__}")

from src.fs_utils import atomic_write
from src.core.utils import sanitize_filename

def test_sanitize_filename():
    assert sanitize_filename("test") == "test"
    
    # Replace illegal characters with underscore and collapse
    assert sanitize_filename('invalid<name>.txt') == 'invalid_name_.txt'
    assert sanitize_filename('test|name?.txt') == 'test_name_.txt'
    assert sanitize_filename('file/name\\with*chars:.txt') == 'file_name_with_chars_.txt'
    
    # Unicode NFC normalization and stripping invisible controls
    assert sanitize_filename("test\u200ename") == "testname"
    
    # Truncate to 200 chars while preserving extension
    long_name = "a" * 250 + ".txt"
    sanitized = sanitize_filename(long_name)
    assert len(sanitized) == 200
    assert sanitized.endswith(".txt")
    
    # Truncate and strip
    long_name2 = "a" * 250 + "\u200e.pdf"
    sanitized2 = sanitize_filename(long_name2)
    assert len(sanitized2) == 200
    assert sanitized2.endswith(".pdf")

def test_atomic_write_success(tmp_path):
    target_file = tmp_path / "output.txt"
    with atomic_write(str(target_file)) as tmp_file:
        assert tmp_file.endswith(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write("content")
            
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "content"
    assert not os.path.exists(str(target_file) + ".tmp")

def test_atomic_write_failure(tmp_path):
    target_file = tmp_path / "output.txt"
    try:
        with atomic_write(str(target_file)) as tmp_file:
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write("content")
            raise ValueError("Something went wrong")
    except ValueError:
        pass
        
    assert not target_file.exists()
    assert not os.path.exists(str(target_file) + ".tmp")

def test_sanitize_filename_empty():
    assert sanitize_filename("") == ""
