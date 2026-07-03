import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from fs_utils import sanitize_filename, atomic_write

def test_sanitize_filename():
    assert sanitize_filename("test") == "test"
    
    # Strip Windows reserved characters
    assert sanitize_filename('invalid<name>.txt') == 'invalidname.txt'
    assert sanitize_filename('test|name?.txt') == 'testname.txt'
    assert sanitize_filename('file/name\\with*chars:.txt') == 'filenamewithchars.txt'
    
    # Unicode NFC normalization and stripping invisible controls
    assert sanitize_filename("test\u200ename") == "testname"
    
    # Truncate to 200 chars
    long_name = "a" * 250
    assert len(sanitize_filename(long_name)) == 200
    
    # Truncate and strip
    assert len(sanitize_filename("a" * 250 + "\u200e")) == 200

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
