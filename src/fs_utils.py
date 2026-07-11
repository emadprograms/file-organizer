import os
from contextlib import contextmanager
import uuid
import logging
import time

logger = logging.getLogger(f"file_organizer.{__name__}")

@contextmanager
def atomic_write(filepath: str):
    """
    Yields a temporary file path, and atomically renames it to filepath
    upon successful completion.
    """
    tmp_filepath = filepath + f".{uuid.uuid4().hex}.tmp"
    try:
        yield tmp_filepath
        for _ in range(10):
            try:
                os.replace(tmp_filepath, filepath)
                break
            except PermissionError:
                time.sleep(0.1)
        else:
            os.replace(tmp_filepath, filepath)
    except Exception:
        if os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        raise
