"""Database connection management and context managers."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Union

DbPathType = Union[str, Path]


def get_db_connection(db_path: DbPathType = "file_organizer.db") -> sqlite3.Connection:
    """Create and configure a SQLite connection with WAL mode and foreign keys.
    
    Args:
        db_path: Path to SQLite database file or ':memory:'.
        
    Returns:
        Configured sqlite3.Connection instance.
    """
    path_str = str(db_path)
    conn = sqlite3.connect(path_str, timeout=30.0)
    conn.row_factory = sqlite3.Row

    # Always enforce foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")

    # If backed by a disk file (not in-memory), configure WAL and concurrency pragmas
    if path_str != ":memory:" and not path_str.startswith("file::memory:"):
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")

    return conn


@contextmanager
def get_db(db_path: DbPathType = "file_organizer.db") -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database transactions.
    
    Automatically commits on normal exit, rolls back on exception,
    and closes the connection.
    
    Args:
        db_path: Path to database file or ':memory:'.
        
    Yields:
        Configured sqlite3.Connection instance.
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
