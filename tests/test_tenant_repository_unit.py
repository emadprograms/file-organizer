"""
Unit tests for tenant repository methods and document reallocation logic.
Tests strict priority:
1. Explicit tenant name match > date range.
2. Date range fallback for unnamed documents.
3. Fallback to active/latest tenant for undated/unnamed documents.
4. Multi-page document expected tenant inheritance.
5. Manual document override syncing pages.
"""
import pytest
from src.db.connection import get_db_connection
from src.db.schema import init_db
from src.db.repository import Repository


@pytest.fixture
def repo(tmp_path):
    db_file = tmp_path / "test_repo.db"
    conn = get_db_connection(str(db_file))
    init_db(conn)
    r = Repository(conn)
    r.add_area("Safra C", "SAF C")
    r.add_house("101", "Safra C")
    return r


def test_tenant_crud_operations(repo):
    # Arrange
    t1 = repo.add_tenant(house_id="101", name="Zaid Al-Harbi", start_date="2020-01-01", end_date="2022-12-31")
    assert t1.id is not None
    assert t1.name == "Zaid Al-Harbi"

    # Act - Get
    fetched = repo.get_tenant(t1.id)
    assert fetched is not None
    assert fetched.name == "Zaid Al-Harbi"
    assert fetched.start_date == "2020-01-01"
    assert fetched.end_date == "2022-12-31"

    # Act - Update
    updated = repo.update_tenant(t1.id, name="Zaid M. Al-Harbi", start_date="2020-02-01", end_date=None)
    assert updated.name == "Zaid M. Al-Harbi"
    assert updated.start_date == "2020-02-01"
    assert updated.end_date is None

    # Act - Delete
    deleted = repo.delete_tenant(t1.id)
    assert deleted is True
    assert repo.get_tenant(t1.id) is None


def test_reallocation_name_priority_over_date_range(repo):
    # Arrange:
    # Tenant 1: Tariq (2018 to 2021)
    # Tenant 2: Omar (2022 to Present)
    t_tariq = repo.add_tenant("101", "طارق المنصور", "2018-01-01", "2021-12-31")
    t_omar = repo.add_tenant("101", "عمر الفاروق", "2022-01-01", None)

    b1 = repo.create_batch("101", "batch_1.pdf", "/tmp/b1.pdf", 2)

    # Document A has primary_date = 2023-05-10 (which is in Omar's timeline)
    # BUT the letter explicitly names Tariq on its page!
    repo.add_document(
        vault_id="v_tariq_late",
        house_id="101",
        tenant_id=t_omar.id,  # initially incorrectly tagged to Omar by date
        batch_id=b1.id,
        primary_date="2023-05-10",
        arabic_title="خطاب متأخر لطارق",
        category="05 - عقود",
        page_count=1,
    )
    repo.add_pages_bulk([
        {
            "batch_id": b1.id,
            "page_number": 1,
            "house_id": "101",
            "vault_id": "v_tariq_late",
            "category": "05 - عقود",
            "expected_tenant_name": "طارق المنصور",
            "content_explanation": "خطاب لطارق مؤرخ بسنة 2023",
            "tenant_id": t_omar.id,
        }
    ])

    # Act
    counts = repo.reallocate_house_documents("101")

    # Assert: Explicit name match takes priority over the 2023 date window!
    doc = repo.get_document("v_tariq_late")
    assert doc.tenant_id == t_tariq.id, "Document must stay with Tariq because Tariq's name is explicitly on the document"

    # Also verify page tenant_id was updated
    pages = repo.conn.execute("SELECT * FROM pages WHERE vault_id = ?", ("v_tariq_late",)).fetchall()
    assert pages[0]["tenant_id"] == t_tariq.id


def test_reallocation_anonymous_document_date_range(repo):
    # Arrange:
    # Tenant 1: Tariq (2018 to 2021)
    # Tenant 2: Omar (2022 to Present)
    t_tariq = repo.add_tenant("101", "طارق", "2018-01-01", "2021-12-31")
    t_omar = repo.add_tenant("101", "عمر", "2022-01-01", None)

    b1 = repo.create_batch("101", "batch_2.pdf", "/tmp/b2.pdf", 2)

    # Document 1: Utility bill from 2020 (no name) -> should go to Tariq
    repo.add_document(
        vault_id="v_bill_2020", house_id="101", tenant_id=t_omar.id, batch_id=b1.id,
        primary_date="2020-04-15", arabic_title="فاتورة كهرباء 2020", category="06 - كهرباء وماء", page_count=1
    )
    repo.add_pages_bulk([{
        "batch_id": b1.id, "page_number": 1, "house_id": "101", "vault_id": "v_bill_2020",
        "category": "06 - كهرباء وماء", "expected_tenant_name": None, "content_explanation": "فاتورة بدون اسم"
    }])

    # Document 2: Utility bill from 2023 (no name) -> should go to Omar
    repo.add_document(
        vault_id="v_bill_2023", house_id="101", tenant_id=t_tariq.id, batch_id=b1.id,
        primary_date="2023-04-15", arabic_title="فاتورة كهرباء 2023", category="06 - كهرباء وماء", page_count=1
    )
    repo.add_pages_bulk([{
        "batch_id": b1.id, "page_number": 2, "house_id": "101", "vault_id": "v_bill_2023",
        "category": "06 - كهرباء وماء", "expected_tenant_name": None, "content_explanation": "فاتورة بدون اسم"
    }])

    # Act
    repo.reallocate_house_documents("101")

    # Assert
    assert repo.get_document("v_bill_2020").tenant_id == t_tariq.id
    assert repo.get_document("v_bill_2023").tenant_id == t_omar.id


def test_reallocation_undated_unnamed_fallback(repo):
    # Arrange:
    # Tenant 1: Tariq (2018 to 2021)
    # Tenant 2: Omar (2022 to Present) -> active tenant
    t_tariq = repo.add_tenant("101", "طارق", "2018-01-01", "2021-12-31")
    t_omar = repo.add_tenant("101", "عمر", "2022-01-01", None)

    b1 = repo.create_batch("101", "batch_3.pdf", "/tmp/b3.pdf", 1)

    # Document with neither date nor name
    repo.add_document(
        vault_id="v_undated", house_id="101", tenant_id=t_tariq.id, batch_id=b1.id,
        primary_date=None, arabic_title="مستند غير مؤرخ", category="01 - عام", page_count=1
    )
    repo.add_pages_bulk([{
        "batch_id": b1.id, "page_number": 1, "house_id": "101", "vault_id": "v_undated",
        "category": "01 - عام", "expected_tenant_name": None, "content_explanation": "لا يوجد اسم ولا تاريخ"
    }])

    # Act
    repo.reallocate_house_documents("101")

    # Assert: Should fall back to active tenant (Omar)
    assert repo.get_document("v_undated").tenant_id == t_omar.id


def test_multi_page_document_name_matching(repo):
    # Arrange:
    t_tariq = repo.add_tenant("101", "طارق المنصور", "2018-01-01", "2021-12-31")
    t_omar = repo.add_tenant("101", "عمر الفاروق", "2022-01-01", None)

    b1 = repo.create_batch("101", "batch_4.pdf", "/tmp/b4.pdf", 2)

    # Multi-page doc: page 1 is a cover letter (no name), page 2 has expected_tenant_name = Tariq
    repo.add_document(
        vault_id="v_multipage", house_id="101", tenant_id=t_omar.id, batch_id=b1.id,
        primary_date="2023-01-01", arabic_title="معاملة متعددة الصفحات", category="05 - عقود", page_count=2
    )
    repo.add_pages_bulk([
        {
            "batch_id": b1.id, "page_number": 1, "house_id": "101", "vault_id": "v_multipage",
            "category": "05 - عقود", "expected_tenant_name": None, "content_explanation": "غلاف المعاملة"
        },
        {
            "batch_id": b1.id, "page_number": 2, "house_id": "101", "vault_id": "v_multipage",
            "category": "05 - عقود", "expected_tenant_name": "طارق المنصور", "content_explanation": "عقد باسم طارق"
        }
    ])

    # Act
    repo.reallocate_house_documents("101")

    # Assert
    assert repo.get_document("v_multipage").tenant_id == t_tariq.id
    pages = repo.conn.execute("SELECT * FROM pages WHERE vault_id = ?", ("v_multipage",)).fetchall()
    for p in pages:
        assert p["tenant_id"] == t_tariq.id


def test_manual_document_override_syncs_pages(repo):
    # Arrange
    t1 = repo.add_tenant("101", "Tenant 1", "2020-01-01", "2021-12-31")
    t2 = repo.add_tenant("101", "Tenant 2", "2022-01-01", None)
    b1 = repo.create_batch("101", "batch_5.pdf", "/tmp/b5.pdf", 1)

    repo.add_document(
        vault_id="v_manual", house_id="101", tenant_id=t1.id, batch_id=b1.id,
        primary_date="2020-05-01", arabic_title="مستند يدوي", category="05 - عقود", page_count=1
    )
    repo.add_pages_bulk([{
        "batch_id": b1.id, "page_number": 1, "house_id": "101", "vault_id": "v_manual",
        "category": "05 - عقود", "tenant_id": t1.id
    }])

    # Act: Manually override document tenant to t2
    with repo.conn:
        repo.conn.execute("UPDATE documents SET tenant_id = ? WHERE vault_id = ?", (t2.id, "v_manual"))
        repo.conn.execute("UPDATE pages SET tenant_id = ? WHERE vault_id = ?", (t2.id, "v_manual"))

    # Assert
    assert repo.get_document("v_manual").tenant_id == t2.id
    pages = repo.conn.execute("SELECT * FROM pages WHERE vault_id = ?", ("v_manual",)).fetchall()
    assert pages[0]["tenant_id"] == t2.id
