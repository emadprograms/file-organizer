import os
import re
import unicodedata
from contextlib import contextmanager
import uuid

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
    
    # Truncate to 200 characters preserving extension
    root, ext = os.path.splitext(filename)
    if len(filename) > 200:
        max_root_len = max(0, 200 - len(ext))
        if max_root_len > 0:
            return root[:max_root_len] + ext
        else:
            return filename[:200]
    return filename

@contextmanager
def atomic_write(filepath: str):
    """
    Yields a temporary file path, and atomically renames it to filepath
    upon successful completion.
    """
    tmp_filepath = filepath + f".{uuid.uuid4().hex}.tmp"
    try:
        yield tmp_filepath
        os.replace(tmp_filepath, filepath)
    except Exception:
        if os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        raise
