import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from fs_utils import sanitize_filename

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
