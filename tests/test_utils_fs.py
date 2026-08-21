from typing import Any
import sys
import os
import pytest
from pypdf import PdfWriter
def make_valid_pdf(path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(path, "wb") as f:
        writer.write(f)

import logging
from pathlib import Path
from unittest.mock import patch

logger = logging.getLogger(f"file_organizer.{__name__}")

from src.utils.fs import atomic_write
from src.core.utils import sanitize_filename

def test_sanitize_filename() -> None:
    """
    Test sanitize filename.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
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

def test_atomic_write_success(tmp_path) -> None:
    """
    Test atomic write success.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    target_file = tmp_path / "output.txt"
    with atomic_write(str(target_file)) as tmp_file:
        assert tmp_file.endswith(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write("content")
            
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "content"
    assert not os.path.exists(str(target_file) + ".tmp")

def test_atomic_write_failure(tmp_path) -> None:
    """
    Test atomic write failure.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
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

def test_sanitize_filename_empty() -> None:
    """
    Test sanitize filename empty.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    assert sanitize_filename("") == ""

def test_merge_and_remove_dir_basic(tmp_path) -> None:
    """Test merging a directory into another."""
    from src.utils.fs import merge_and_remove_dir
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    
    src.mkdir()
    (src / "file1.txt").write_text("hello")
    (src / "sub").mkdir()
    (src / "sub" / "file2.txt").write_text("world")
    
    merge_and_remove_dir(src, dst)
    
    assert not src.exists()
    assert (dst / "file1.txt").exists()
    assert (dst / "sub" / "file2.txt").exists()
    assert (dst / "sub" / "file2.txt").read_text() == "world"

def test_merge_and_remove_dir_with_collisions(tmp_path) -> None:
    """Test merging when files already exist in dst."""
    from src.utils.fs import merge_and_remove_dir
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    
    src.mkdir()
    dst.mkdir()
    
    (src / "file1.txt").write_text("new content")
    (dst / "file1.txt").write_text("old content")
    
    merge_and_remove_dir(src, dst)
    
    assert not src.exists()
    assert (dst / "file1.txt").read_text() == "new content"

def test_shortcut_creation_and_reading(tmp_path) -> None:
    """Test creating and reading a single shortcut."""
    from src.utils.fs import create_shortcut, read_shortcut_target
    import os
    if os.name != 'nt':
        pytest.skip("Windows shortcuts only supported on Windows")
        
    target_file = tmp_path / "target.pdf"
    make_valid_pdf(target_file)
    link_file = tmp_path / "link.lnk"
    
    # Test create
    create_shortcut(str(target_file.resolve()), str(link_file.resolve()))
    assert link_file.exists()
    
    # Test read
    read_target = read_shortcut_target(str(link_file.resolve()))
    assert read_target is not None
    assert str(target_file.resolve()).lower() in read_target.lower()

def test_batch_shortcuts(tmp_path) -> None:
    """Test creating and reading multiple shortcuts in batch."""
    from src.utils.fs import batch_create_shortcuts, batch_read_shortcut_targets
    import os
    if os.name != 'nt':
        pytest.skip("Windows shortcuts only supported on Windows")
        
    target1 = tmp_path / "target1.txt"
    make_valid_pdf(target1)
    link1 = tmp_path / "link1.lnk"
    
    target2 = tmp_path / "علي مسعد.txt"
    make_valid_pdf(target2)
    link2 = tmp_path / "عبد الله.lnk"
    
    items = [
        {"target": str(target1.resolve()), "link": str(link1.resolve())},
        {"target": str(target2.resolve()), "link": str(link2.resolve())}
    ]
    
    batch_create_shortcuts(items)
    
    assert link1.exists()
    assert link2.exists()
    
    results = batch_read_shortcut_targets([str(link1.resolve()), str(link2.resolve())])
    
    # Path comparison might differ in case on Windows
    assert results[str(link1.resolve())].lower() == str(target1.resolve()).lower()
    assert results[str(link2.resolve())].lower() == str(target2.resolve()).lower()
