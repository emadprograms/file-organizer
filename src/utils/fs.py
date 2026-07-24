from typing import Generator
import os
from contextlib import contextmanager
import uuid
import logging
import time

logger = logging.getLogger(f"file_organizer.{__name__}")

@contextmanager
def atomic_write(filepath: str) -> Generator[str, None, None]:
    """Yields a temporary file path, and atomically renames it to filepath
    upon successful completion.
    
    Args:
        filepath (str): The final destination file path.
        
    Yields:
        str: The temporary file path to write to.
        
    Raises:
        PermissionError: If the file cannot be renamed after 10 attempts.
    """
    import tempfile
    tmp_filepath = os.path.join(tempfile.gettempdir(), f"{os.path.basename(filepath)}.{uuid.uuid4().hex}.tmp")
    try:
        yield tmp_filepath
        for _ in range(10):
            try:
                os.replace(tmp_filepath, filepath)
                break
            except PermissionError:
                time.sleep(0.1)
        else:
            raise PermissionError(
                f"Could not atomically write to {filepath} after 10 attempts. "
                "The file might be locked by another process (e.g., Antivirus, OneDrive)."
            )
    except Exception:
        if os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        raise
