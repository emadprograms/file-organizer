import os
import re
import unicodedata
from contextlib import contextmanager

def sanitize_filename(filename: str) -> str:
    """
    Apply Unicode NFC normalization, strip Windows reserved characters,
    strip invisible Unicode control characters, and truncate the result to 200 characters.
    """
    # Unicode normalize NFC
    filename = unicodedata.normalize('NFC', filename)
    
    # Strip Windows reserved characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Strip invisible Unicode control characters (Cc and Cf)
    filename = ''.join(ch for ch in filename if unicodedata.category(ch) not in ('Cc', 'Cf'))
    
    # Truncate to 200 characters
    return filename[:200]

@contextmanager
def atomic_write(filepath: str):
    """
    Yields a temporary file path, and atomically renames it to filepath
    upon successful completion.
    """
    tmp_filepath = filepath + ".tmp"
    try:
        yield tmp_filepath
        os.replace(tmp_filepath, filepath)
    except Exception:
        if os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        raise
