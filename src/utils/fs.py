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


def create_shortcut(target_path: str, link_path: str) -> None:
    """Creates a Windows .lnk shortcut pointing to target_path at link_path.
    
    Args:
        target_path: Absolute path to the target file.
        link_path: Absolute path where the .lnk file will be created.
    """
    import pylnk3
    from pylnk3 import ExtraData, ExtraData_EnvironmentVariableDataBlock
    
    # Strip \\?\ prefix if present for parsing into LinkTargetIDList properly
    clean_target = target_path
    if target_path.startswith(r"\\?\C:"):
        clean_target = target_path[4:]
        
    if os.name != 'nt' and not clean_target.startswith("C:") and not clean_target.startswith(r"\\"):
        # pylnk3 fails on posix paths. Convert to fake Windows path for testing on Mac
        from pathlib import Path
        clean_target = "C:" + str(Path(clean_target).resolve()).replace('/', '\\')
        
    lnk = pylnk3.for_file(clean_target)
    
    # Manually inject the long path prefix for the Environment Variable Block if it was passed
    if target_path.startswith(r"\\?\C:"):
        env_data_block = ExtraData_EnvironmentVariableDataBlock()
        env_data_block.target_ansi = target_path
        env_data_block.target_unicode = target_path
        lnk.extra_data = ExtraData(blocks=[env_data_block])
        lnk.link_flags.HasExpString = True
        
    lnk.save(link_path)


def read_shortcut_target(link_path: str) -> str | None:
    """Reads a Windows .lnk shortcut and returns the target path.
    
    Args:
        link_path: Absolute path to the .lnk file.
        
    Returns:
        The target path as a string, or None if it cannot be parsed.
    """
    import pylnk3
    try:
        with open(link_path, "rb") as f:
            lnk = pylnk3.parse(f)
            return lnk.path
    except Exception as e:
        logger.warning(f"Could not parse shortcut {link_path}: {e}")
        return None
