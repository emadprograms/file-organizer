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
    import subprocess
    import base64
    import os
    
    # Strip \\?\ prefix if present, WScript.Shell does not support it
    clean_target = str(target_path).replace('/', '\\')
    if clean_target.startswith("\\\\?\\UNC\\"):
        clean_target = "\\" + clean_target[7:]
    elif clean_target.startswith("\\\\?\\"):
        clean_target = clean_target[4:]
        if clean_target.startswith("\\"):
            clean_target = clean_target[1:]
            
    if os.name != 'nt' and not clean_target.startswith("C:") and not clean_target.startswith(r"\\"):
        from pathlib import Path
        clean_target = "C:" + str(Path(clean_target).resolve()).replace('/', '\\')

    ps_script_path = os.path.join(os.path.dirname(__file__), "ps_shortcut.ps1")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script_path, "create", clean_target, link_path], 
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                   check=True)


def read_shortcut_target(link_path: str) -> str | None:
    """Reads a Windows .lnk shortcut and returns the target path.
    
    Args:
        link_path: Absolute path to the .lnk file.
        
    Returns:
        The target path as a string, or None if it cannot be parsed.
    """
    import os
    if not os.path.exists(link_path):
        return None
        
    results = batch_read_shortcut_targets([link_path])
    return results.get(os.path.abspath(link_path))

def batch_create_shortcuts(items: list[dict]) -> None:
    """Create multiple shortcuts in a single PowerShell execution.
    
    Args:
        items: List of dictionaries with 'target' and 'link' keys.
    """
    import subprocess
    if os.name != 'nt' or not items:
        return
        
    import json
    ps_script_path = os.path.join(os.path.dirname(__file__), "ps_shortcut.ps1")
    input_json = json.dumps(items, ensure_ascii=False)
    
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script_path, "batch-create"],
        input=input_json,
        text=True,
        encoding='utf-8',
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        check=True
    )

def batch_read_shortcut_targets(link_paths: list[str]) -> dict[str, str]:
    """Read multiple shortcut targets in a single PowerShell execution.
    
    Args:
        link_paths: List of string absolute paths to .lnk files.
        
    Returns:
        A dictionary mapping link paths to their target paths.
    """
    import subprocess
    if os.name != 'nt' or not link_paths:
        return {}
        
    import json
    ps_script_path = os.path.join(os.path.dirname(__file__), "ps_shortcut.ps1")
    
    # PowerShell ConvertFrom-Json can fail if the array is too large or chunked incorrectly over stdin, 
    # but for ~500 items it's fine.
    input_json = json.dumps([os.path.abspath(p) for p in link_paths], ensure_ascii=False)
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script_path, "batch-read"],
            input=input_json,
            capture_output=True,
            text=True,
            encoding='utf-8',
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        
        output = result.stdout.strip()
        if not output:
            return {}
            
        data = json.loads(output)
        return data
    except Exception as e:
        logger.error(f"Failed batch reading shortcuts: {e}")
        return {}
