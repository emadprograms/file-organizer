import sqlite3
import pytest
from src.db.connection import get_db_connection, get_db
from src.db.schema import init_db, SCHEMA_SQL, INDICES_SQL


def test_table_and_index_creation(tmp_path):
    db_file = tmp_path / "test.db"
    conn = get_db_connection(db_file)
    init_db(conn)

    cursor = conn.cursor()
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    expected_tables = {"areas", "houses", "tenants", "batches", "pages", "documents"}
    assert expected_tables.issubset(tables)

    # Check indices
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indices = {row[0] for row in cursor.fetchall()}
    expected_indices = {
        "idx_houses_area",
        "idx_tenants_house",
        "idx_batches_house",
        "idx_pages_batch",
        "idx_pages_house",
        "idx_documents_house",
        "idx_documents_tenant",
        "idx_documents_date",
    }
    assert expected_indices.issubset(indices)
    conn.close()


def test_foreign_key_enforcement(tmp_path):
    db_file = tmp_path / "test.db"
    conn = get_db_connection(db_file)
    init_db(conn)

    cursor = conn.cursor()
    # Inserting house with invalid area_id should fail
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO houses (id, area_id) VALUES (?, ?)", ("H01", "NON_EXISTENT_AREA"))
        conn.commit()

    conn.close()


def test_cascading_delete_batch_deletes_pages(tmp_path):
    db_file = tmp_path / "test.db"
    conn = get_db_connection(db_file)
    init_db(conn)
    cursor = conn.cursor()

    # Seed area, house, batch, pages
    cursor.execute("INSERT INTO areas (id, code) VALUES (?, ?)", ("AREA1", "A1"))
    cursor.execute("INSERT INTO houses (id, area_id) VALUES (?, ?)", ("HOUSE1", "AREA1"))
    cursor.execute(
        "INSERT INTO batches (id, house_id, filename, file_path, page_count) VALUES (?, ?, ?, ?, ?)",
        (1, "HOUSE1", "scan1.pdf", "/path/scan1.pdf", 3),
    )
    cursor.execute(
        "INSERT INTO pages (batch_id, page_number, house_id) VALUES (?, ?, ?)",
        (1, 1, "HOUSE1"),
    )
    cursor.execute(
        "INSERT INTO pages (batch_id, page_number, house_id) VALUES (?, ?, ?)",
        (1, 2, "HOUSE1"),
    )
    conn.commit()

    # Verify pages exist
    cursor.execute("SELECT COUNT(*) FROM pages WHERE batch_id = 1")
    assert cursor.fetchone()[0] == 2

    # Delete batch
    cursor.execute("DELETE FROM batches WHERE id = 1")
    conn.commit()

    # Verify pages were deleted by cascade
    cursor.execute("SELECT COUNT(*) FROM pages WHERE batch_id = 1")
    assert cursor.fetchone()[0] == 0

    conn.close()


def test_unique_constraint_batch_page_number(tmp_path):
    db_file = tmp_path / "test.db"
    conn = get_db_connection(db_file)
    init_db(conn)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO areas (id, code) VALUES (?, ?)", ("AREA1", "A1"))
    cursor.execute("INSERT INTO houses (id, area_id) VALUES (?, ?)", ("HOUSE1", "AREA1"))
    cursor.execute(
        "INSERT INTO batches (id, house_id, filename, file_path, page_count) VALUES (?, ?, ?, ?, ?)",
        (1, "HOUSE1", "scan1.pdf", "/path/scan1.pdf", 3),
    )
    cursor.execute(
        "INSERT INTO pages (batch_id, page_number, house_id) VALUES (?, ?, ?)",
        (1, 1, "HOUSE1"),
    )
    conn.commit()

    # Inserting same (batch_id, page_number) should fail
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO pages (batch_id, page_number, house_id) VALUES (?, ?, ?)",
            (1, 1, "HOUSE1"),
        )
        conn.commit()

    conn.close()


def test_connection_wal_and_pragmas(tmp_path):
    db_file = tmp_path / "test_wal.db"
    conn = get_db_connection(db_file)

    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys")
    fk = cursor.fetchone()[0]
    assert fk == 1

    cursor.execute("PRAGMA journal_mode")
    journal_mode = cursor.fetchone()[0]
    assert journal_mode.lower() == "wal"

    conn.close()


def test_get_db_context_manager(tmp_path):
    db_file = tmp_path / "test_cm.db"
    with get_db(db_file) as conn:
        init_db(conn)
        conn.execute("INSERT INTO areas (id, code) VALUES ('A1', 'CODE1')")

    # Re-open and verify committed
    with get_db(db_file) as conn:
        row = conn.execute("SELECT code FROM areas WHERE id = 'A1'").fetchone()
        assert row["code"] == "CODE1"

    # Test rollback on exception
    with pytest.raises(RuntimeError):
        with get_db(db_file) as conn:
            conn.execute("INSERT INTO areas (id, code) VALUES ('A2', 'CODE2')")
            raise RuntimeError("Forced error")

    with get_db(db_file) as conn:
        row = conn.execute("SELECT code FROM areas WHERE id = 'A2'").fetchone()
        assert row is None
