import os
from pathlib import Path

class LockExistsError(Exception):
    """Raised when the lock is currently held by an active process."""
    pass

def acquire_lock(lock_path: Path) -> None:
    """Acquire a PID-based lock at lock_path atomically."""
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, 'w') as f:
                f.write(str(os.getpid()))
            return
        except FileExistsError:
            # Lock file exists, check if stale
            try:
                pid_str = lock_path.read_text().strip()
                if not pid_str:
                    raise ValueError("Empty lockfile")
                pid = int(pid_str)
                
                os.kill(pid, 0)
                # If we get here, process is alive
                raise LockExistsError(f"Lock held by active PID: {pid}")
            except ProcessLookupError:
                pass # Stale lock, can overwrite
            except PermissionError:
                raise LockExistsError(f"Lock held by active PID: {pid}")
            except (ValueError, OSError):
                pass # Stale/invalid lock
                
            # If we reach here, lock is stale and should be removed to retry
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            continue

def release_lock(lock_path: Path) -> None:
    """Release the lock if it matches our PID."""
    if not lock_path.exists():
        return
        
    try:
        pid_str = lock_path.read_text().strip()
        if pid_str == str(os.getpid()):
            lock_path.unlink()
    except (ValueError, OSError):
        pass
