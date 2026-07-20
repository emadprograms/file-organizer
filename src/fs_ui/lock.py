import os
from pathlib import Path

class LockExistsError(Exception):
    """Raised when the lock is currently held by an active process."""
    pass

def acquire_lock(lock_path: Path) -> None:
    """Acquire a PID-based lock at lock_path."""
    if lock_path.exists():
        try:
            pid_str = lock_path.read_text().strip()
            if not pid_str:
                raise ValueError("Empty lockfile")
            pid = int(pid_str)
            
            # Check if alive
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass # Process is dead, can overwrite
            except PermissionError:
                # Process is alive but we can't signal it
                raise LockExistsError(f"Lock held by active PID: {pid}")
            else:
                # Process is alive
                raise LockExistsError(f"Lock held by active PID: {pid}")
            
        except ValueError:
            # ValueError: tampering/invalid PID
            pass # Overwrite stale lock

            
    # Write current PID
    lock_path.write_text(str(os.getpid()))

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
