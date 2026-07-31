import shutil
from typing import Generator
import os
from contextlib import contextmanager
import uuid
import logging
import time
from pathlib import Path

logger = logging.getLogger(f"file_organizer.{__name__}")

@contextmanager
def atomic_write(filepath: str) -> Generator[str, None, None]:
    """Yields a temporary file path, and atomically renames it to filepath
    upon successful completion.
    """
    import tempfile
    tmp_filepath = os.path.join(tempfile.gettempdir(), f"{os.path.basename(filepath)}.{uuid.uuid4().hex}.tmp")
    try:
        yield tmp_filepath
        for _ in range(10):
            try:
                shutil.move(tmp_filepath, filepath)
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


def merge_and_remove_dir(src_dir: str | os.PathLike, dst_dir: str | os.PathLike) -> None:
    """Recursively moves all files and subdirectories from src_dir into dst_dir,
    overwriting existing files if necessary, and then deletes src_dir completely.
    """
    src = Path(src_dir).resolve()
    dst = Path(dst_dir).resolve()

    if not src.exists() or src == dst:
        return

    dst.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(str(src), topdown=False):
        rel_path = Path(root).relative_to(src)
        target_root = dst / rel_path
        target_root.mkdir(parents=True, exist_ok=True)

        for f in files:
            src_file = Path(root) / f
            dst_file = target_root / f
            if dst_file.exists():
                try:
                    os.remove(str(dst_file))
                except Exception as e:
                    logger.warning(f"Could not remove existing file {dst_file} prior to move: {e}")
            try:
                shutil.move(str(src_file), str(dst_file))
            except Exception as e:
                logger.warning(f"Failed to move file {src_file} -> {dst_file}: {e}")

        for d in dirs:
            src_sub = Path(root) / d
            if src_sub.exists():
                try:
                    src_sub.rmdir()
                except Exception:
                    pass

    if src.exists():
        shutil.rmtree(str(src), ignore_errors=True)
        logger.info(f"Merged and cleanly removed directory: {src.name} -> {dst.name}")
