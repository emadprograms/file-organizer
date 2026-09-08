"""Repository providing type-safe CRUD operations for the SQLite database."""

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Generator, List, Optional, Sequence, Union

from src.db.models import Area, House, Tenant, Batch, Page, Document


# ==========================================
# Area Operations
# ==========================================

def add_area(
    conn: sqlite3.Connection,
    area_id: Optional[Union[str, Area]] = None,
    code: Optional[str] = None,
    area: Optional[Area] = None,
    autocommit: bool = True,
) -> Area:
    """Insert a new area."""
    if isinstance(area_id, Area):
        target_area = area_id
    elif area is not None:
        target_area = area
    else:
        target_area = Area(id=area_id, code=code)  # type: ignore

    cursor = conn.execute(
        "INSERT INTO areas (id, code) VALUES (?, ?) RETURNING *",
        (target_area.id, target_area.code),
    )
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return Area.model_validate(dict(row))


def get_area(conn: sqlite3.Connection, area_id: str) -> Optional[Area]:
    """Retrieve an area by ID."""
    cursor = conn.execute("SELECT * FROM areas WHERE id = ?", (area_id,))
    row = cursor.fetchone()
    return Area.model_validate(dict(row)) if row else None


def list_areas(conn: sqlite3.Connection) -> List[Area]:
    """List all areas ordered by id."""
    cursor = conn.execute("SELECT * FROM areas ORDER BY id")
    return [Area.model_validate(dict(row)) for row in cursor.fetchall()]


# ==========================================
# House Operations
# ==========================================

def add_house(
    conn: sqlite3.Connection,
    house_id: Optional[Union[str, House]] = None,
    area_id: Optional[str] = None,
    house: Optional[House] = None,
    autocommit: bool = True,
) -> House:
    """Insert a new house."""
    if isinstance(house_id, House):
        target_house = house_id
    elif house is not None:
        target_house = house
    else:
        target_house = House(id=house_id, area_id=area_id)  # type: ignore

    cursor = conn.execute(
        "INSERT INTO houses (id, area_id) VALUES (?, ?) RETURNING *",
        (target_house.id, target_house.area_id),
    )
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return House.model_validate(dict(row))


def get_house(conn: sqlite3.Connection, house_id: str) -> Optional[House]:
    """Retrieve a house by ID."""
    cursor = conn.execute("SELECT * FROM houses WHERE id = ?", (house_id,))
    row = cursor.fetchone()
    return House.model_validate(dict(row)) if row else None


def list_houses_by_area(conn: sqlite3.Connection, area_id: str) -> List[House]:
    """List all houses within an area."""
    cursor = conn.execute("SELECT * FROM houses WHERE area_id = ? ORDER BY id", (area_id,))
    return [House.model_validate(dict(row)) for row in cursor.fetchall()]


# ==========================================
# Tenant Operations
# ==========================================

def add_tenant(
    conn: sqlite3.Connection,
    house_id: Optional[Union[str, Tenant]] = None,
    name: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None,
    tenant: Optional[Tenant] = None,
    autocommit: bool = True,
) -> Tenant:
    """Insert a new tenant."""
    if isinstance(house_id, Tenant):
        target_tenant = house_id
    elif tenant is not None:
        target_tenant = tenant
    else:
        target_tenant = Tenant(
            house_id=house_id,  # type: ignore
            name=name,  # type: ignore
            start_date=start_date,  # type: ignore
            end_date=end_date,
        )

    s_date = str(target_tenant.start_date)
    e_date = str(target_tenant.end_date) if target_tenant.end_date else None

    cursor = conn.execute(
        "INSERT INTO tenants (house_id, name, start_date, end_date) VALUES (?, ?, ?, ?) RETURNING *",
        (target_tenant.house_id, target_tenant.name, s_date, e_date),
    )
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return Tenant.model_validate(dict(row))


def get_active_tenant(
    conn: sqlite3.Connection,
    house_id: str,
    target_date: Optional[Union[str, date]] = None,
) -> Optional[Tenant]:
    """Retrieve active tenant for a house at the specified date (default today)."""
    if target_date is None:
        date_str = date.today().isoformat()
    elif isinstance(target_date, date):
        date_str = target_date.isoformat()
    else:
        date_str = str(target_date)

    query = """
    SELECT * FROM tenants
    WHERE house_id = ?
      AND start_date <= ?
      AND (end_date IS NULL OR end_date >= ?)
    ORDER BY start_date DESC
    LIMIT 1
    """
    cursor = conn.execute(query, (house_id, date_str, date_str))
    row = cursor.fetchone()
    return Tenant.model_validate(dict(row)) if row else None


def list_tenants_by_house(conn: sqlite3.Connection, house_id: str) -> List[Tenant]:
    """List all tenants for a house ordered chronologically."""
    cursor = conn.execute(
        "SELECT * FROM tenants WHERE house_id = ? ORDER BY start_date ASC, id ASC",
        (house_id,),
    )
    return [Tenant.model_validate(dict(row)) for row in cursor.fetchall()]


# ==========================================
# Batch Operations
# ==========================================

def create_batch(
    conn: sqlite3.Connection,
    house_id: Optional[Union[str, Batch]] = None,
    filename: Optional[str] = None,
    file_path: Optional[str] = None,
    page_count: Optional[int] = None,
    status: str = "completed",
    batch: Optional[Batch] = None,
    autocommit: bool = True,
) -> Batch:
    """Create a new batch record."""
    if isinstance(house_id, Batch):
        target_batch = house_id
    elif batch is not None:
        target_batch = batch
    else:
        target_batch = Batch(
            house_id=house_id,  # type: ignore
            filename=filename,  # type: ignore
            file_path=file_path,  # type: ignore
            page_count=page_count,  # type: ignore
            status=status,
        )

    cursor = conn.execute(
        """
        INSERT INTO batches (house_id, filename, file_path, page_count, status)
        VALUES (?, ?, ?, ?, ?)
        RETURNING *
        """,
        (
            target_batch.house_id,
            target_batch.filename,
            target_batch.file_path,
            target_batch.page_count,
            target_batch.status,
        ),
    )
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return Batch.model_validate(dict(row))


def get_batch(conn: sqlite3.Connection, batch_id: int) -> Optional[Batch]:
    """Retrieve a batch by ID."""
    cursor = conn.execute("SELECT * FROM batches WHERE id = ?", (batch_id,))
    row = cursor.fetchone()
    return Batch.model_validate(dict(row)) if row else None


def update_batch_status(
    conn: sqlite3.Connection,
    batch_id: int,
    status: str,
    autocommit: bool = True,
) -> Optional[Batch]:
    """Update status of a batch."""
    cursor = conn.execute(
        "UPDATE batches SET status = ? WHERE id = ? RETURNING *",
        (status, batch_id),
    )
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return Batch.model_validate(dict(row)) if row else None


def list_batches_by_house(conn: sqlite3.Connection, house_id: str) -> List[Batch]:
    """List all batches for a house."""
    cursor = conn.execute(
        "SELECT * FROM batches WHERE house_id = ? ORDER BY created_at ASC, id ASC",
        (house_id,),
    )
    return [Batch.model_validate(dict(row)) for row in cursor.fetchall()]


# ==========================================
# Page Operations
# ==========================================

ALLOWED_PAGE_FIELDS = {
    "category",
    "content_explanation",
    "expected_tenant_name",
    "expected_house_number",
    "raw_date",
    "sender",
    "receiver",
    "subject",
    "is_continuation",
    "tenant_id",
    "resolved_date",
    "fine_category",
    "fine_category_reason",
    "vault_id",
}


def add_pages_bulk(
    conn: sqlite3.Connection,
    pages: Sequence[Union[Page, dict]],
    autocommit: bool = True,
) -> List[Page]:
    """Bulk insert pages into the database."""
    created_pages: List[Page] = []
    insert_sql = """
    INSERT INTO pages (
        batch_id, page_number, house_id, category, content_explanation,
        expected_tenant_name, expected_house_number, raw_date, sender,
        receiver, subject, is_continuation, tenant_id, resolved_date,
        fine_category, fine_category_reason, vault_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    RETURNING *
    """

    for item in pages:
        if isinstance(item, dict):
            p = Page(**item)
        else:
            p = item

        params = (
            p.batch_id,
            p.page_number,
            p.house_id,
            p.category,
            p.content_explanation,
            p.expected_tenant_name,
            p.expected_house_number,
            p.raw_date,
            p.sender,
            p.receiver,
            p.subject,
            1 if p.is_continuation else 0,
            p.tenant_id,
            str(p.resolved_date) if p.resolved_date else None,
            p.fine_category,
            p.fine_category_reason,
            p.vault_id,
        )
        cursor = conn.execute(insert_sql, params)
        row = cursor.fetchone()
        created_pages.append(Page.model_validate(dict(row)))

    if autocommit:
        conn.commit()
    return created_pages


def get_pages_by_batch(conn: sqlite3.Connection, batch_id: int) -> List[Page]:
    """Retrieve all pages belonging to a batch ordered by page number."""
    cursor = conn.execute(
        "SELECT * FROM pages WHERE batch_id = ? ORDER BY page_number ASC",
        (batch_id,),
    )
    return [Page.model_validate(dict(row)) for row in cursor.fetchall()]


def update_page_cleaning(
    conn: sqlite3.Connection,
    page_id: int,
    autocommit: bool = True,
    **fields: Any,
) -> Optional[Page]:
    """Update cleaning/classification fields on a page."""
    valid_updates = {k: v for k, v in fields.items() if k in ALLOWED_PAGE_FIELDS}
    if not valid_updates:
        cursor = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,))
        row = cursor.fetchone()
        return Page.model_validate(dict(row)) if row else None

    # Handle special formatting (dates, booleans)
    for k, v in valid_updates.items():
        if k == "is_continuation":
            valid_updates[k] = 1 if v else 0
        elif isinstance(v, (date, datetime)):
            valid_updates[k] = v.isoformat()

    set_clauses = [f"{col} = ?" for col in valid_updates.keys()]
    params = list(valid_updates.values())
    params.append(page_id)

    query = f"UPDATE pages SET {', '.join(set_clauses)} WHERE id = ? RETURNING *"
    cursor = conn.execute(query, params)
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return Page.model_validate(dict(row)) if row else None


def link_pages_to_document(
    conn: sqlite3.Connection,
    page_ids: Sequence[int],
    vault_id: str,
    autocommit: bool = True,
) -> int:
    """Link multiple pages to a vault document by ID."""
    if not page_ids:
        return 0

    placeholders = ",".join("?" for _ in page_ids)
    query = f"UPDATE pages SET vault_id = ? WHERE id IN ({placeholders})"
    cursor = conn.execute(query, [vault_id, *page_ids])
    if autocommit:
        conn.commit()
    return cursor.rowcount


# ==========================================
# Document Operations
# ==========================================

def add_document(
    conn: sqlite3.Connection,
    doc: Optional[Union[Document, dict, str]] = None,
    *,
    vault_id: Optional[str] = None,
    house_id: Optional[str] = None,
    tenant_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    primary_date: Optional[Union[str, date]] = None,
    arabic_title: Optional[str] = None,
    category: Optional[str] = None,
    page_count: int = 1,
    autocommit: bool = True,
) -> Document:
    """Insert a new document record into the vault."""
    if isinstance(doc, Document):
        d = doc
    elif isinstance(doc, dict):
        d = Document(**doc)
    elif isinstance(doc, str):
        d = Document(
            vault_id=doc,
            house_id=house_id,  # type: ignore
            tenant_id=tenant_id,  # type: ignore
            batch_id=batch_id,  # type: ignore
            primary_date=primary_date,
            arabic_title=arabic_title,
            category=category,
            page_count=page_count,
        )
    elif vault_id is not None:
        d = Document(
            vault_id=vault_id,
            house_id=house_id,  # type: ignore
            tenant_id=tenant_id,  # type: ignore
            batch_id=batch_id,  # type: ignore
            primary_date=primary_date,
            arabic_title=arabic_title,
            category=category,
            page_count=page_count,
        )
    else:
        raise ValueError("Invalid document specification")

    p_date = str(d.primary_date) if d.primary_date else None

    query = """
    INSERT INTO documents (
        vault_id, house_id, tenant_id, batch_id, primary_date,
        arabic_title, category, page_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    RETURNING *
    """
    cursor = conn.execute(
        query,
        (
            d.vault_id,
            d.house_id,
            d.tenant_id,
            d.batch_id,
            p_date,
            d.arabic_title,
            d.category,
            d.page_count,
        ),
    )
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return Document.model_validate(dict(row))


def get_document(conn: sqlite3.Connection, vault_id: str) -> Optional[Document]:
    """Retrieve a document by vault ID."""
    cursor = conn.execute("SELECT * FROM documents WHERE vault_id = ?", (vault_id,))
    row = cursor.fetchone()
    return Document.model_validate(dict(row)) if row else None


def list_documents_by_house(conn: sqlite3.Connection, house_id: str) -> List[Document]:
    """List all documents for a house."""
    query = "SELECT * FROM documents WHERE house_id = ? ORDER BY primary_date DESC, created_at DESC"
    cursor = conn.execute(query, (house_id,))
    return [Document.model_validate(dict(row)) for row in cursor.fetchall()]


def list_documents_by_category(
    conn: sqlite3.Connection,
    house_id: str,
    category: str,
) -> List[Document]:
    """List documents for a house filtered by category."""
    query = """
    SELECT * FROM documents
    WHERE house_id = ? AND category = ?
    ORDER BY primary_date DESC, created_at DESC
    """
    cursor = conn.execute(query, (house_id, category))
    return [Document.model_validate(dict(row)) for row in cursor.fetchall()]


# ==========================================
# Repository Wrapper Class
# ==========================================

class Repository:
    """Type-safe repository providing clean object-oriented data access."""

    def __init__(self, conn: sqlite3.Connection, autocommit: bool = True):
        self.conn = conn
        self.autocommit = autocommit

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """Group operations in an atomic transaction."""
        prev = self.autocommit
        self.autocommit = False
        try:
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            self.autocommit = prev

    # Area operations
    def add_area(
        self,
        area_id: Optional[Union[str, Area]] = None,
        code: Optional[str] = None,
        area: Optional[Area] = None,
    ) -> Area:
        return add_area(self.conn, area_id=area_id, code=code, area=area, autocommit=self.autocommit)

    def get_area(self, area_id: str) -> Optional[Area]:
        return get_area(self.conn, area_id)

    def list_areas(self) -> List[Area]:
        return list_areas(self.conn)

    # House operations
    def add_house(
        self,
        house_id: Optional[Union[str, House]] = None,
        area_id: Optional[str] = None,
        house: Optional[House] = None,
    ) -> House:
        return add_house(self.conn, house_id=house_id, area_id=area_id, house=house, autocommit=self.autocommit)

    def get_house(self, house_id: str) -> Optional[House]:
        return get_house(self.conn, house_id)

    def list_houses_by_area(self, area_id: str) -> List[House]:
        return list_houses_by_area(self.conn, area_id)

    # Tenant operations
    def add_tenant(
        self,
        house_id: Optional[Union[str, Tenant]] = None,
        name: Optional[str] = None,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        tenant: Optional[Tenant] = None,
    ) -> Tenant:
        return add_tenant(
            self.conn,
            house_id=house_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            tenant=tenant,
            autocommit=self.autocommit,
        )

    def get_active_tenant(
        self,
        house_id: str,
        target_date: Optional[Union[str, date]] = None,
    ) -> Optional[Tenant]:
        return get_active_tenant(self.conn, house_id, target_date=target_date)

    def list_tenants_by_house(self, house_id: str) -> List[Tenant]:
        return list_tenants_by_house(self.conn, house_id)

    # Batch operations
    def create_batch(
        self,
        house_id: Optional[Union[str, Batch]] = None,
        filename: Optional[str] = None,
        file_path: Optional[str] = None,
        page_count: Optional[int] = None,
        status: str = "completed",
        batch: Optional[Batch] = None,
    ) -> Batch:
        return create_batch(
            self.conn,
            house_id=house_id,
            filename=filename,
            file_path=file_path,
            page_count=page_count,
            status=status,
            batch=batch,
            autocommit=self.autocommit,
        )

    def get_batch(self, batch_id: int) -> Optional[Batch]:
        return get_batch(self.conn, batch_id)

    def update_batch_status(self, batch_id: int, status: str) -> Optional[Batch]:
        return update_batch_status(self.conn, batch_id, status, autocommit=self.autocommit)

    def list_batches_by_house(self, house_id: str) -> List[Batch]:
        return list_batches_by_house(self.conn, house_id)

    # Page operations
    def add_pages_bulk(self, pages: Sequence[Union[Page, dict]]) -> List[Page]:
        return add_pages_bulk(self.conn, pages, autocommit=self.autocommit)

    def get_pages_by_batch(self, batch_id: int) -> List[Page]:
        return get_pages_by_batch(self.conn, batch_id)

    def update_page_cleaning(self, page_id: int, **fields: Any) -> Optional[Page]:
        return update_page_cleaning(self.conn, page_id, autocommit=self.autocommit, **fields)

    def link_pages_to_document(self, page_ids: Sequence[int], vault_id: str) -> int:
        return link_pages_to_document(self.conn, page_ids, vault_id, autocommit=self.autocommit)

    # Document operations
    def add_document(
        self,
        doc: Optional[Union[Document, dict, str]] = None,
        *,
        vault_id: Optional[str] = None,
        house_id: Optional[str] = None,
        tenant_id: Optional[int] = None,
        batch_id: Optional[int] = None,
        primary_date: Optional[Union[str, date]] = None,
        arabic_title: Optional[str] = None,
        category: Optional[str] = None,
        page_count: int = 1,
    ) -> Document:
        return add_document(
            self.conn,
            doc=doc,
            vault_id=vault_id,
            house_id=house_id,
            tenant_id=tenant_id,
            batch_id=batch_id,
            primary_date=primary_date,
            arabic_title=arabic_title,
            category=category,
            page_count=page_count,
            autocommit=self.autocommit,
        )

    def get_document(self, vault_id: str) -> Optional[Document]:
        return get_document(self.conn, vault_id)

    def list_documents_by_house(self, house_id: str) -> List[Document]:
        return list_documents_by_house(self.conn, house_id)

    def list_documents_by_category(self, house_id: str, category: str) -> List[Document]:
        return list_documents_by_category(self.conn, house_id, category)
