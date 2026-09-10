"""Repository providing type-safe CRUD operations for the SQLite database."""

import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Generator, Optional, Sequence, Union

from src.db.models import Area, House, Tenant, Batch, Page, Document
from src.routing.config import FOLDER_PREFIXES


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


def list_areas(conn: sqlite3.Connection) -> list[Area]:
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


def list_houses_by_area(conn: sqlite3.Connection, area_id: str) -> list[House]:
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

    target_norm = " ".join((target_tenant.name or "").strip().split()).lower()
    if target_tenant.house_id and target_norm:
        cursor = conn.execute(
            "SELECT * FROM tenants WHERE house_id = ? ORDER BY id ASC",
            (str(target_tenant.house_id),),
        )
        for row in cursor.fetchall():
            row_dict = dict(row)
            row_norm = " ".join((row_dict.get("name") or "").strip().split()).lower()
            if row_norm == target_norm:
                return Tenant.model_validate(row_dict)

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


def list_tenants_by_house(conn: sqlite3.Connection, house_id: str) -> list[Tenant]:
    """List all tenants for a house ordered chronologically."""
    cursor = conn.execute(
        "SELECT * FROM tenants WHERE house_id = ? ORDER BY start_date ASC, id ASC",
        (house_id,),
    )
    return [Tenant.model_validate(dict(row)) for row in cursor.fetchall()]


def get_tenant(conn: sqlite3.Connection, tenant_id: int) -> Optional[Tenant]:
    """Retrieve tenant by ID."""
    cursor = conn.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
    row = cursor.fetchone()
    return Tenant.model_validate(dict(row)) if row else None


_UNSET = object()


def update_tenant(
    conn: sqlite3.Connection,
    tenant_id: int,
    name: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Any = _UNSET,
    autocommit: bool = True,
) -> Optional[Tenant]:
    """Update tenant information."""
    current = get_tenant(conn, tenant_id)
    if not current:
        return None

    new_name = name if name is not None else current.name
    new_start = str(start_date) if start_date is not None else str(current.start_date)
    if end_date is _UNSET:
        new_end = str(current.end_date) if current.end_date else None
    elif end_date is None:
        new_end = None
    else:
        new_end = str(end_date)

    cursor = conn.execute(
        "UPDATE tenants SET name = ?, start_date = ?, end_date = ? WHERE id = ? RETURNING *",
        (new_name, new_start, new_end, tenant_id),
    )
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return Tenant.model_validate(dict(row)) if row else None


def delete_tenant(
    conn: sqlite3.Connection,
    tenant_id: int,
    autocommit: bool = True,
) -> bool:
    """Delete a tenant. Reassigns orphaned documents/pages to another tenant if one exists."""
    target = get_tenant(conn, tenant_id)
    if not target:
        return False

    remaining = [t for t in list_tenants_by_house(conn, target.house_id) if t.id != tenant_id]
    if remaining:
        fallback_id = remaining[0].id
        conn.execute("UPDATE documents SET tenant_id = ? WHERE tenant_id = ?", (fallback_id, tenant_id))
        conn.execute("UPDATE pages SET tenant_id = ? WHERE tenant_id = ?", (fallback_id, tenant_id))

    cursor = conn.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
    deleted = cursor.rowcount > 0
    if autocommit:
        conn.commit()
    return deleted


def reallocate_house_documents(
    conn: sqlite3.Connection,
    house_id: str,
    autocommit: bool = True,
) -> dict[str, Any]:
    """Reallocate documents and pages of a house based on the tenant priority hierarchy:
    
    1. Explicit Name Match: If any page of the document explicitly names a known tenant,
       assign to that tenant (dates are ignored).
    2. Date Window Fallback: If no explicit name match, match document.primary_date against
       tenant [start_date, end_date]. If overlapping, pick the tenant with the latest start_date.
    3. Fallback: If no match, assign to active/latest tenant for the house.
    """
    tenants = list_tenants_by_house(conn, house_id)
    if not tenants:
        return {"reallocated_count": 0, "total_documents": 0, "tenants_count": 0}

    tenant_map: dict[str, Tenant] = {t.name.strip().lower(): t for t in tenants if t.id}

    # Fetch all documents for this house that are not manually locked (is_manual = 1)
    doc_rows = conn.execute(
        "SELECT vault_id, tenant_id, primary_date FROM documents WHERE house_id = ? AND (is_manual IS NULL OR is_manual = 0)",
        (house_id,),
    ).fetchall()

    total_cnt_row = conn.execute("SELECT COUNT(*) as cnt FROM documents WHERE house_id = ?", (house_id,)).fetchone()
    total_docs = total_cnt_row["cnt"] if total_cnt_row else len(doc_rows)

    if not doc_rows:
        return {"reallocated_count": 0, "total_documents": total_docs, "tenants_count": len(tenants)}

    # Fetch page-level expected_tenant_names for each document
    page_rows = conn.execute(
        "SELECT vault_id, expected_tenant_name FROM pages WHERE house_id = ? AND vault_id IS NOT NULL",
        (house_id,),
    ).fetchall()

    names_by_doc: dict[str, list[str]] = {}
    for r in page_rows:
        v_id = r["vault_id"]
        exp_name = r["expected_tenant_name"]
        if exp_name and exp_name.strip():
            names_by_doc.setdefault(v_id, []).append(exp_name.strip())

    reallocated_count = 0

    # Default fallback tenant: active tenant or latest tenant
    active_tenant = get_active_tenant(conn, house_id) or tenants[-1]

    for d in doc_rows:
        v_id = d["vault_id"]
        current_tid = d["tenant_id"]
        target_t: Optional[Tenant] = None

        # Priority 1: Explicit name match from pages
        doc_names = names_by_doc.get(v_id, [])
        for name in doc_names:
            clean_name = name.lower()
            if clean_name in tenant_map:
                target_t = tenant_map[clean_name]
                break
            # Substring match if name is meaningful length
            for t_k, t_obj in tenant_map.items():
                if len(t_k) >= 3 and (t_k in clean_name or clean_name in t_k):
                    target_t = t_obj
                    break
            if target_t:
                break

        # Priority 2: Date window fallback
        if not target_t and d["primary_date"]:
            d_date_str = str(d["primary_date"])[:10]
            matching_tenants = []
            for t in tenants:
                s_d = str(t.start_date)[:10] if t.start_date else "1900-01-01"
                e_d = str(t.end_date)[:10] if t.end_date else "9999-12-31"
                if s_d <= d_date_str <= e_d:
                    matching_tenants.append(t)

            if matching_tenants:
                # Pick latest start_date
                matching_tenants.sort(key=lambda x: str(x.start_date) if x.start_date else "", reverse=True)
                target_t = matching_tenants[0]

        # Priority 3: Fallback
        if not target_t:
            target_t = active_tenant

        # Apply update if changed
        if target_t and target_t.id != current_tid:
            conn.execute("UPDATE documents SET tenant_id = ? WHERE vault_id = ?", (target_t.id, v_id))
            conn.execute("UPDATE pages SET tenant_id = ? WHERE vault_id = ?", (target_t.id, v_id))
            reallocated_count += 1

    if autocommit:
        conn.commit()

    return {
        "reallocated_count": reallocated_count,
        "total_documents": total_docs,
        "tenants_count": len(tenants),
    }


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


def list_batches_by_house(conn: sqlite3.Connection, house_id: str) -> list[Batch]:
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
) -> list[Page]:
    """Bulk insert pages into the database."""
    created_pages: list[Page] = []
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


def get_pages_by_batch(conn: sqlite3.Connection, batch_id: int) -> list[Page]:
    """Retrieve all pages belonging to a batch ordered by page number."""
    cursor = conn.execute(
        "SELECT * FROM pages WHERE batch_id = ? ORDER BY page_number ASC",
        (batch_id,),
    )
    return [Page.model_validate(dict(row)) for row in cursor.fetchall()]


def get_pages_by_vault_id(conn: sqlite3.Connection, vault_id: str) -> list[Page]:
    """Retrieve all pages belonging to a document ordered by page number."""
    cursor = conn.execute(
        "SELECT * FROM pages WHERE vault_id = ? ORDER BY page_number ASC",
        (vault_id,),
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
    is_manual: int = 0,
    notes: Optional[str] = None,
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
            is_manual=is_manual,
            notes=notes,
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
            is_manual=is_manual,
            notes=notes,
        )
    else:
        raise ValueError("Invalid document specification")

    p_date = str(d.primary_date) if d.primary_date else None
    manual_val = int(getattr(d, "is_manual", 0) or 0)

    query = """
    INSERT INTO documents (
        vault_id, house_id, tenant_id, batch_id, primary_date,
        arabic_title, category, page_count, is_manual, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            manual_val,
            d.notes,
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


def list_documents_by_house(conn: sqlite3.Connection, house_id: str) -> list[Document]:
    """List all documents for a house."""
    query = "SELECT * FROM documents WHERE house_id = ? ORDER BY primary_date DESC, created_at DESC"
    cursor = conn.execute(query, (house_id,))
    return [Document.model_validate(dict(row)) for row in cursor.fetchall()]


def list_documents_by_category(
    conn: sqlite3.Connection,
    house_id: str,
    category: str,
) -> list[Document]:
    """List documents for a house filtered by category."""
    query = """
    SELECT * FROM documents
    WHERE house_id = ? AND category = ?
    ORDER BY primary_date DESC, created_at DESC
    """
    cursor = conn.execute(query, (house_id, category))
    return [Document.model_validate(dict(row)) for row in cursor.fetchall()]


def search_documents(
    conn: sqlite3.Connection,
    query: str,
    house_id: Optional[str] = None,
) -> list[Document]:
    """Search documents by title, category, notes, or vault ID."""
    term = f"%{query.strip()}%"
    if house_id:
        sql = """
        SELECT * FROM documents
        WHERE house_id = ? AND (
            arabic_title LIKE ? OR category LIKE ? OR notes LIKE ? OR vault_id LIKE ?
        )
        ORDER BY primary_date DESC, created_at DESC
        """
        cursor = conn.execute(sql, (house_id, term, term, term, term))
    else:
        sql = """
        SELECT * FROM documents
        WHERE arabic_title LIKE ? OR category LIKE ? OR notes LIKE ? OR vault_id LIKE ?
        ORDER BY primary_date DESC, created_at DESC
        """
        cursor = conn.execute(sql, (term, term, term, term))
    return [Document.model_validate(dict(row)) for row in cursor.fetchall()]


def update_document(
    conn: sqlite3.Connection,
    vault_id: str,
    *,
    arabic_title: Optional[str] = None,
    category: Optional[str] = None,
    tenant_id: Optional[int] = None,
    primary_date: Optional[Union[str, date]] = None,
    is_manual: Optional[int] = 1,
    notes: Optional[str] = None,
    autocommit: bool = True,
) -> Optional[Document]:
    """Update editable document metadata and mark as manually locked."""
    existing = get_document(conn, vault_id)
    if not existing:
        return None

    updates = []
    params: list[Any] = []
    if arabic_title is not None:
        updates.append("arabic_title = ?")
        params.append(arabic_title.strip() if arabic_title else None)
    if category is not None:
        updates.append("category = ?")
        params.append(category.strip() if category else None)
    if tenant_id is not None:
        updates.append("tenant_id = ?")
        params.append(tenant_id)
    if primary_date is not None:
        updates.append("primary_date = ?")
        params.append(str(primary_date)[:10] if primary_date else None)
    if is_manual is not None:
        updates.append("is_manual = ?")
        params.append(int(is_manual))
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes.strip() if notes else None)

    if not updates:
        return existing

    params.append(vault_id)
    sql = f"UPDATE documents SET {', '.join(updates)} WHERE vault_id = ? RETURNING *"
    cursor = conn.execute(sql, params)
    row = cursor.fetchone()

    # Also keep pages in sync for tenant_id and fine_category
    if tenant_id is not None:
        conn.execute("UPDATE pages SET tenant_id = ? WHERE vault_id = ?", (tenant_id, vault_id))
    if category is not None:
        conn.execute("UPDATE pages SET fine_category = ? WHERE vault_id = ?", (category, vault_id))

    if autocommit:
        conn.commit()
    return Document.model_validate(dict(row)) if row else None


def update_document_notes(
    conn: sqlite3.Connection,
    vault_id: str,
    notes: str,
    autocommit: bool = True,
) -> Optional[Document]:
    """Update custom notes on a document."""
    existing = get_document(conn, vault_id)
    if not existing:
        return None
    cleaned_notes = notes.strip() if notes else None
    cursor = conn.execute(
        "UPDATE documents SET notes = ? WHERE vault_id = ? RETURNING *",
        (cleaned_notes, vault_id)
    )
    row = cursor.fetchone()
    if autocommit:
        conn.commit()
    return Document.model_validate(dict(row)) if row else None


def get_document_metadata(
    conn: sqlite3.Connection,
    vault_id: str,
) -> Optional[dict]:
    """Retrieve complete metadata for a document including tenant, batch, and page-level details."""
    query = """
    SELECT 
        d.vault_id, d.house_id, d.category, d.primary_date, d.arabic_title,
        d.page_count, d.is_manual, d.notes, d.created_at,
        t.id as tenant_id, t.name as tenant_name, t.start_date as tenant_start_date, t.end_date as tenant_end_date,
        b.filename as batch_filename
    FROM documents d
    LEFT JOIN tenants t ON d.tenant_id = t.id
    LEFT JOIN batches b ON d.batch_id = b.id
    WHERE d.vault_id = ?
    """
    row = conn.execute(query, (vault_id,)).fetchone()
    if not row:
        return None
    
    doc_dict = dict(row)
    pages_cursor = conn.execute(
        "SELECT page_number, subject, sender, receiver, content_explanation, raw_date, fine_category FROM pages WHERE vault_id = ? ORDER BY page_number ASC",
        (vault_id,)
    )
    doc_dict["pages"] = [dict(p) for p in pages_cursor.fetchall()]
    return doc_dict


def reset_document_manual_lock(
    conn: sqlite3.Connection,
    vault_id: str,
    autocommit: bool = True,
) -> bool:
    """Reset manual lock on a document so it can participate in automatic reallocations."""
    cursor = conn.execute("UPDATE documents SET is_manual = 0 WHERE vault_id = ?", (vault_id,))
    updated = cursor.rowcount > 0
    if autocommit:
        conn.commit()
    return updated


def copy_document(
    conn: sqlite3.Connection,
    vault_id: str,
    *,
    new_vault_id: str,
    target_category: Optional[str] = None,
    target_tenant_id: Optional[int] = None,
    target_title: Optional[str] = None,
    autocommit: bool = True,
) -> Optional[Document]:
    """Duplicate a document record under a new vault_id with is_manual = 1."""
    src = get_document(conn, vault_id)
    if not src:
        return None

    cat = target_category if target_category is not None else src.category
    t_id = target_tenant_id if target_tenant_id is not None else src.tenant_id
    title = target_title if target_title is not None else src.arabic_title

    new_doc = add_document(
        conn,
        vault_id=new_vault_id,
        house_id=src.house_id,
        tenant_id=t_id,
        batch_id=src.batch_id,
        primary_date=src.primary_date,
        arabic_title=title,
        category=cat,
        page_count=src.page_count,
        is_manual=1,
        autocommit=autocommit,
    )
    return new_doc


def delete_document(
    conn: sqlite3.Connection,
    vault_id: str,
    house_id: str,
    area_id: str,
    areas_root: Union[str, Path],
    *,
    autocommit: bool = True,
) -> bool:
    """Delete physical file and database records for a document."""
    doc = get_document(conn, vault_id)
    if not doc:
        return False

    pdf_root = Path(areas_root)
    pdf_candidates = [
        pdf_root / area_id / house_id / "vault" / f"doc_{vault_id}.pdf",
        pdf_root / area_id / house_id / "vault" / f"{vault_id}.pdf",
    ]
    if " - " in house_id:
        clean_house = house_id.split(" - ")[0].strip()
        pdf_candidates.append(pdf_root / area_id / clean_house / "vault" / f"doc_{vault_id}.pdf")
        pdf_candidates.append(pdf_root / area_id / clean_house / "vault" / f"{vault_id}.pdf")

    for cand in pdf_candidates:
        if cand.exists() and cand.is_file():
            try:
                cand.unlink()
            except OSError:
                pass

    conn.execute("DELETE FROM pages WHERE vault_id = ?", (vault_id,))
    conn.execute("DELETE FROM documents WHERE vault_id = ?", (vault_id,))
    if autocommit:
        conn.commit()
    return True


def get_or_create_numbered_folder(
    conn: sqlite3.Connection,
    house_id: str,
    folder_name: str,
) -> str:
    """Return appropriately numbered folder string, sequentially numbering custom folders from 14+."""
    name_clean = folder_name.strip()
    if not name_clean:
        return "13 - رسائل متنوعة"

    # If it is a standard folder name from FOLDER_PREFIXES
    if name_clean in FOLDER_PREFIXES:
        return f"{FOLDER_PREFIXES[name_clean]} - {name_clean}"

    # If it already starts with a number pattern e.g. "05 - عقود" or "14 - Custom"
    m = re.match(r"^(\d+)\s*-\s*(.+)$", name_clean)
    if m:
        prefix_num = int(m.group(1))
        suffix_name = m.group(2).strip()
        if suffix_name in FOLDER_PREFIXES:
            return f"{FOLDER_PREFIXES[suffix_name]} - {suffix_name}"
        return f"{prefix_num:02d} - {suffix_name}"

    # It's a custom un-numbered folder name.
    # Check if this custom folder already exists for this house in documents:
    cursor = conn.execute("SELECT DISTINCT category FROM documents WHERE house_id = ?", (house_id,))
    existing_cats = [r[0] for r in cursor.fetchall() if r[0]]
    max_num = 13
    for cat in existing_cats:
        m_cat = re.match(r"^(\d+)\s*-\s*(.+)$", cat.strip())
        if m_cat:
            num = int(m_cat.group(1))
            if num > max_num:
                max_num = num
            if m_cat.group(2).strip().lower() == name_clean.lower():
                # Already exists with a number! Reuse it
                return cat.strip()

    next_num = max_num + 1
    return f"{next_num:02d} - {name_clean}"


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

    def list_areas(self) -> list[Area]:
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

    def list_houses_by_area(self, area_id: str) -> list[House]:
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

    def list_tenants_by_house(self, house_id: str) -> list[Tenant]:
        return list_tenants_by_house(self.conn, house_id)

    def get_tenant(self, tenant_id: int) -> Optional[Tenant]:
        return get_tenant(self.conn, tenant_id)

    def update_tenant(
        self,
        tenant_id: int,
        name: Optional[str] = None,
        start_date: Optional[Union[str, date]] = None,
        end_date: Any = _UNSET,
    ) -> Optional[Tenant]:
        return update_tenant(
            self.conn,
            tenant_id=tenant_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            autocommit=self.autocommit,
        )

    def delete_tenant(self, tenant_id: int) -> bool:
        return delete_tenant(self.conn, tenant_id=tenant_id, autocommit=self.autocommit)

    def reallocate_house_documents(self, house_id: str) -> dict[str, Any]:
        return reallocate_house_documents(self.conn, house_id=house_id, autocommit=self.autocommit)

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

    def list_batches_by_house(self, house_id: str) -> list[Batch]:
        return list_batches_by_house(self.conn, house_id)

    # Page operations
    def add_pages_bulk(self, pages: Sequence[Union[Page, dict]]) -> list[Page]:
        return add_pages_bulk(self.conn, pages, autocommit=self.autocommit)

    def get_pages_by_batch(self, batch_id: int) -> list[Page]:
        return get_pages_by_batch(self.conn, batch_id)

    def get_pages_by_vault_id(self, vault_id: str) -> list[Page]:
        return get_pages_by_vault_id(self.conn, vault_id)

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
        is_manual: int = 0,
        notes: Optional[str] = None,
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
            is_manual=is_manual,
            notes=notes,
            autocommit=self.autocommit,
        )

    def get_document(self, vault_id: str) -> Optional[Document]:
        return get_document(self.conn, vault_id)

    def list_documents_by_house(self, house_id: str) -> list[Document]:
        return list_documents_by_house(self.conn, house_id)

    def list_documents_by_category(self, house_id: str, category: str) -> list[Document]:
        return list_documents_by_category(self.conn, house_id, category)

    def search_documents(self, query: str, house_id: Optional[str] = None) -> list[Document]:
        return search_documents(self.conn, query=query, house_id=house_id)

    def update_document(
        self,
        vault_id: str,
        *,
        arabic_title: Optional[str] = None,
        category: Optional[str] = None,
        tenant_id: Optional[int] = None,
        primary_date: Optional[Union[str, date]] = None,
        is_manual: Optional[int] = 1,
        notes: Optional[str] = None,
    ) -> Optional[Document]:
        return update_document(
            self.conn,
            vault_id,
            arabic_title=arabic_title,
            category=category,
            tenant_id=tenant_id,
            primary_date=primary_date,
            is_manual=is_manual,
            notes=notes,
            autocommit=self.autocommit,
        )

    def update_document_notes(
        self,
        vault_id: str,
        notes: str,
    ) -> Optional[Document]:
        return update_document_notes(self.conn, vault_id, notes, autocommit=self.autocommit)

    def get_document_metadata(
        self,
        vault_id: str,
    ) -> Optional[dict]:
        return get_document_metadata(self.conn, vault_id)

    def reset_document_manual_lock(self, vault_id: str) -> bool:
        return reset_document_manual_lock(self.conn, vault_id, autocommit=self.autocommit)

    def copy_document(
        self,
        vault_id: str,
        *,
        new_vault_id: str,
        target_category: Optional[str] = None,
        target_tenant_id: Optional[int] = None,
        target_title: Optional[str] = None,
    ) -> Optional[Document]:
        return copy_document(
            self.conn,
            vault_id,
            new_vault_id=new_vault_id,
            target_category=target_category,
            target_tenant_id=target_tenant_id,
            target_title=target_title,
            autocommit=self.autocommit,
        )

    def get_or_create_numbered_folder(self, house_id: str, folder_name: str) -> str:
        return get_or_create_numbered_folder(self.conn, house_id, folder_name)

    def delete_document(
        self,
        vault_id: str,
        house_id: str,
        area_id: str,
        areas_root: Union[str, Path],
    ) -> bool:
        return delete_document(
            self.conn,
            vault_id,
            house_id,
            area_id,
            areas_root,
            autocommit=self.autocommit,
        )

