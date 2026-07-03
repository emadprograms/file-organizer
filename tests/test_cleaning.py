import pytest
from pathlib import Path
from src.cleaning import (
    PageData,
    TenantTimeline,
    parse_flexible_date,
    load_and_parse_json,
    infer_missing_dates,
    normalize_arabic_text,
    cluster_names_fuzzily,
    canonicalize_with_llm,
    build_tenant_timelines,
    assign_pages_to_tenants,
    process_cleaning_phase
)

def test_parse_flexible_date():
    assert parse_flexible_date("2023") == "2023-01-01"
    assert parse_flexible_date("2023-05") == "2023-05-01"
    assert parse_flexible_date("May 2023") == "2023-05-01"
    assert parse_flexible_date("2023-05-15") == "2023-05-15"
    assert parse_flexible_date("15/05/2023") == "2023-05-15"
    assert parse_flexible_date("05-2023") == "2023-05-01"
    with pytest.raises(ValueError):
        parse_flexible_date("garbage")

def test_load_and_parse_json(tmp_path):
    json_path = tmp_path / "test_report.json"
    json_path.write_text("""[
        {"category": "contract", "content_explanation": "test", "expected_tenant_name": "احمد", "date": "2023-05", "sender": "Ministry", "receiver": "Tenant", "subject": "Subj"},
        {"category": "forms", "content_explanation": "test2", "expected_tenant_name": null, "date": null, "sender": "Ministry", "receiver": "Tenant", "subject": "Subj2"}
    ]""", encoding="utf-8")
    
    pages = load_and_parse_json(json_path)
    assert len(pages) == 2
    assert pages[0].date == "2023-05-01"
    assert pages[0].original_index == 0
    assert pages[1].date is None
    assert pages[1].original_index == 1

def test_infer_missing_dates():
    pages = [
        PageData(category="c", content_explanation="e", sender="s", receiver="r", subject="sub", original_index=0, date="2020-01-01", expected_tenant_name=None),
        PageData(category="c", content_explanation="e", sender="s", receiver="r", subject="sub", original_index=1, date=None, expected_tenant_name=None),
        PageData(category="c", content_explanation="e", sender="s", receiver="r", subject="sub", original_index=2, date=None, expected_tenant_name=None),
        PageData(category="c", content_explanation="e", sender="s", receiver="r", subject="sub", original_index=3, date="2020-01-05", expected_tenant_name=None)
    ]
    infer_missing_dates(pages)
    assert pages[0].resolved_date == "2020-01-01"
    assert pages[1].resolved_date == "2020-01-01"
    assert pages[2].resolved_date == "2020-01-05"
    assert pages[3].resolved_date == "2020-01-05"

def test_normalize_arabic_text():
    assert normalize_arabic_text('أحمد') == 'احمد'
    assert normalize_arabic_text('مُحَمَّد') == 'محمد'
    assert normalize_arabic_text('فاطمة') == 'فاطمه'
    assert normalize_arabic_text('مستشفى') == 'مستشفي'

def test_cluster_names_fuzzily():
    names = {'محمد علي', 'محمد على', 'احمد', 'أحمد'}
    res = cluster_names_fuzzily(names)
    assert len(set(res.values())) == 2

class MockLLMClient:
    def generate_content(self, contents, config):
        class MockResponse:
            text = '{"احمد": "احمد", "محمد": "محمد"}'
        return MockResponse()

def test_canonicalize_with_llm():
    client = MockLLMClient()
    res = canonicalize_with_llm(["احمد", "محمد"], client)
    assert res == {"احمد": "احمد", "محمد": "محمد"}

def test_build_tenant_timelines():
    pages = [
        PageData(category="contract", content_explanation="e", expected_tenant_name="احمد", sender="s", receiver="r", subject="sub", original_index=0, resolved_date="2020-01-01", date=None),
        PageData(category="forms", content_explanation="e", expected_tenant_name="احمد", sender="s", receiver="r", subject="sub", original_index=1, resolved_date="2020-01-05", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="احمد", sender="s", receiver="r", subject="sub", original_index=2, resolved_date="2020-01-10", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="احمد", sender="s", receiver="r", subject="sub", original_index=3, resolved_date="2020-01-15", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="احمد", sender="s", receiver="r", subject="sub", original_index=4, resolved_date="2020-01-20", date=None),
    ]
    mapping = {"احمد": "احمد محمد"}
    timelines = build_tenant_timelines(pages, mapping)
    assert len(timelines) == 1
    assert timelines[0].canonical_name == "احمد محمد"
    assert timelines[0].min_date == "2020-01-01"
    assert timelines[0].max_date == "2020-01-20"

def test_assign_pages_to_tenants():
    pages = [
        PageData(category="contract", content_explanation="e", sender="s", receiver="r", subject="sub", original_index=0, resolved_date="2020-01-10", expected_tenant_name=None, date=None),
        PageData(category="contract", content_explanation="e", sender="s", receiver="r", subject="sub", original_index=1, resolved_date="2020-05-10", expected_tenant_name=None, date=None),
        PageData(category="contract", content_explanation="e", sender="s", receiver="r", subject="sub", original_index=2, resolved_date=None, expected_tenant_name=None, date=None)
    ]
    timelines = [
        TenantTimeline(canonical_name="احمد", min_date="2020-01-01", max_date="2020-02-01")
    ]
    assign_pages_to_tenants(pages, timelines)
    assert pages[0].canonical_tenant == "احمد"
    assert pages[1].canonical_tenant == "Unassigned (2020-05)"
    assert pages[2].canonical_tenant == "Unassigned (Unknown)"

def test_process_cleaning_phase(tmp_path):
    json_path = tmp_path / "test_report.json"
    json_path.write_text("""[
        {"category": "contract", "content_explanation": "test", "expected_tenant_name": "احمد", "date": "2023-05-01", "sender": "s", "receiver": "r", "subject": "Subj"},
        {"category": "forms", "content_explanation": "test2", "expected_tenant_name": "احمد", "date": "2023-05-02", "sender": "s", "receiver": "r", "subject": "Subj2"},
        {"category": "other", "content_explanation": "test3", "expected_tenant_name": "احمد", "date": "2023-05-03", "sender": "s", "receiver": "r", "subject": "Subj3"},
        {"category": "other", "content_explanation": "test4", "expected_tenant_name": "احمد", "date": "2023-05-04", "sender": "s", "receiver": "r", "subject": "Subj4"},
        {"category": "other", "content_explanation": "test5", "expected_tenant_name": "احمد", "date": "2023-05-05", "sender": "s", "receiver": "r", "subject": "Subj5"}
    ]""", encoding="utf-8")
    
    pages = process_cleaning_phase(json_path, MockLLMClient())
    assert len(pages) == 5
    assert pages[0].canonical_tenant == "احمد"
