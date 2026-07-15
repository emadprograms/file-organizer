import pytest
import json
import logging
from unittest.mock import patch

logger = logging.getLogger(f"file_organizer.{__name__}")

from pathlib import Path
from src.core.models import PageData, TenantTimeline
from src.timeline.dates import parse_flexible_date
from src.tenant_config.tenants import (
    normalize_arabic_text,
    cluster_names_fuzzily,
    canonicalize_with_llm,
    build_tenant_timelines
)
from src.timeline.phase import (
    load_and_parse_json,
    infer_missing_dates,
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
    default_model = "test_model"
    def _route_llm_call(self, *args, **kwargs):
        return '{"احمد": "احمد", "محمد": "محمد"}'

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

def test_build_tenant_timelines_boundaries():
    """Verify thresholds: >=1 anchor AND >=5 pages, and must have dates."""
    
    # Case 1: Exactly 1 anchor, 5 pages -> PASS
    pages_pass = [
        PageData(category="contract", content_explanation="e", expected_tenant_name="T1", sender="s", receiver="r", subject="sub", original_index=0, resolved_date="2020-01-01", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T1", sender="s", receiver="r", subject="sub", original_index=1, resolved_date="2020-01-02", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T1", sender="s", receiver="r", subject="sub", original_index=2, resolved_date="2020-01-03", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T1", sender="s", receiver="r", subject="sub", original_index=3, resolved_date="2020-01-04", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T1", sender="s", receiver="r", subject="sub", original_index=4, resolved_date="2020-01-05", date=None),
    ]
    assert len(build_tenant_timelines(pages_pass, {})) == 1

    # Case 2: 0 anchors, 10 pages -> FAIL
    pages_no_anchor = [
        PageData(category="other", content_explanation="e", expected_tenant_name="T2", sender="s", receiver="r", subject="sub", original_index=i, resolved_date="2020-01-01", date=None)
        for i in range(10)
    ]
    assert len(build_tenant_timelines(pages_no_anchor, {})) == 0

    # Case 3: 1 anchor, 4 pages -> FAIL
    pages_too_few = [
        PageData(category="contract", content_explanation="e", expected_tenant_name="T3", sender="s", receiver="r", subject="sub", original_index=0, resolved_date="2020-01-01", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T3", sender="s", receiver="r", subject="sub", original_index=1, resolved_date="2020-01-02", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T3", sender="s", receiver="r", subject="sub", original_index=2, resolved_date="2020-01-03", date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T3", sender="s", receiver="r", subject="sub", original_index=3, resolved_date="2020-01-04", date=None),
    ]
    assert len(build_tenant_timelines(pages_too_few, {})) == 0

    # Case 4: 1 anchor, 5 pages, NO dates -> FAIL
    pages_no_dates = [
        PageData(category="contract", content_explanation="e", expected_tenant_name="T4", sender="s", receiver="r", subject="sub", original_index=0, resolved_date=None, date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T4", sender="s", receiver="r", subject="sub", original_index=1, resolved_date=None, date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T4", sender="s", receiver="r", subject="sub", original_index=2, resolved_date=None, date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T4", sender="s", receiver="r", subject="sub", original_index=3, resolved_date=None, date=None),
        PageData(category="other", content_explanation="e", expected_tenant_name="T4", sender="s", receiver="r", subject="sub", original_index=4, resolved_date=None, date=None),
    ]
    assert len(build_tenant_timelines(pages_no_dates, {})) == 0

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

def test_parse_flexible_date_edge_cases():
    """Original edge cases — preserved for regression."""
    assert parse_flexible_date("August 2023") == "2023-08-01"
    assert parse_flexible_date("2023/05/15") == "2023-05-15"
    assert parse_flexible_date("05-2023") == "2023-05-01"

def test_parse_english_dd_month_yyyy():
    """DD MonthName YYYY — full and abbreviated."""
    assert parse_flexible_date("29 February 2024") == "2024-02-29"
    assert parse_flexible_date("28 February 2024") == "2024-02-28"
    assert parse_flexible_date("25 September 2007") == "2007-09-25"
    assert parse_flexible_date("3 SEP 2007") == "2007-09-03"
    assert parse_flexible_date("1 Jan 2000") == "2000-01-01"
    assert parse_flexible_date("15 Dec 1999") == "1999-12-15"
    # "sept" abbreviation
    assert parse_flexible_date("5 Sept 2010") == "2010-09-05"

def test_parse_english_month_dd_yyyy():
    """MonthName DD, YYYY — with and without comma."""
    assert parse_flexible_date("July 11, 2010") == "2010-07-11"
    assert parse_flexible_date("April 18, 2006") == "2006-04-18"
    assert parse_flexible_date("July 11 2010") == "2010-07-11"
    assert parse_flexible_date("December 1, 2023") == "2023-12-01"
    assert parse_flexible_date("January 31, 1990") == "1990-01-31"

def test_parse_english_ordinal_suffixes():
    """Dates with ordinal suffixes: 1st, 2nd, 3rd, 4th, 11th, 21st, etc."""
    assert parse_flexible_date("1st January 2024") == "2024-01-01"
    assert parse_flexible_date("2nd March 2020") == "2020-03-02"
    assert parse_flexible_date("3rd April 2019") == "2019-04-03"
    assert parse_flexible_date("27th September 2007") == "2007-09-27"
    assert parse_flexible_date("11th November 2011") == "2011-11-11"
    assert parse_flexible_date("March 3rd, 2020") == "2020-03-03"
    assert parse_flexible_date("June 21st 2015") == "2015-06-21"

def test_parse_english_weekday_prefix():
    """Dates with weekday prefix — strip the weekday."""
    assert parse_flexible_date("Monday, 27 September 2007") == "2007-09-27"
    assert parse_flexible_date("Sunday, January 1, 2023") == "2023-01-01"
    assert parse_flexible_date("Thu 15 March 2018") == "2018-03-15"
    assert parse_flexible_date("Fri, 1 Jan 2000") == "2000-01-01"

def test_parse_arabic_gregorian_months():
    """Arabic Gregorian month names (the standard Arabic calendar used in Bahrain)."""
    assert parse_flexible_date("5 مارس 2024م") == "2024-03-05"
    assert parse_flexible_date("مارس 2024") == "2024-03-01"
    assert parse_flexible_date("15 يناير 2020") == "2020-01-15"
    assert parse_flexible_date("سبتمبر 2007") == "2007-09-01"
    assert parse_flexible_date("1 ديسمبر 2023") == "2023-12-01"
    assert parse_flexible_date("20 فبراير 2015") == "2015-02-20"
    assert parse_flexible_date("يوليو 2010") == "2010-07-01"
    assert parse_flexible_date("10 أكتوبر 2022") == "2022-10-10"

def test_parse_arabic_weekday_prefix():
    """Arabic dates with weekday prefix — strip the weekday."""
    assert parse_flexible_date("الأحد، 5 مارس 2024") == "2024-03-05"
    assert parse_flexible_date("الخميس 15 يناير 2020") == "2020-01-15"

def test_parse_dual_calendar_dates():
    """Gregorian + Hijri in parentheses or after slash — keep Gregorian only."""
    assert parse_flexible_date("September 27, 2007 (11 Sha'ban 1428 AH)") == "2007-09-27"
    assert parse_flexible_date("April 2010 / Rabi' al-Thani 1431 AH") == "2010-04-01"
    assert parse_flexible_date("15 March 2023 (22 Sha'ban 1444)") == "2023-03-15"
    assert parse_flexible_date("1 January 2000 (24 Ramadan 1420 AH)") == "2000-01-01"

def test_parse_pure_hijri_arabic():
    """Pure Hijri dates with Arabic month names → converted to Gregorian."""
    # 11 Sha'ban 1428 AH ≈ 2007-08-24 (approximate, exact depends on sighting)
    result = parse_flexible_date("11 شعبان 1428")
    assert result.startswith("2007-08")

    # 1 Ramadan 1444 ≈ 2023-03-23
    result = parse_flexible_date("1 رمضان 1444")
    assert result.startswith("2023-03")

    # Month only: Muharram 1446 ≈ 2024-07
    result = parse_flexible_date("محرم 1446")
    assert result.startswith("2024-07")

    # 1 Rajab 1445 ≈ 2024-01-13
    result = parse_flexible_date("1 رجب 1445")
    assert result.startswith("2024-01")

def test_parse_pure_hijri_english():
    """Pure Hijri dates with English transliteration → converted to Gregorian."""
    result = parse_flexible_date("11 Sha'ban 1428")
    assert result.startswith("2007-08")

    result = parse_flexible_date("1 Ramadan 1444")
    assert result.startswith("2023-03")

    result = parse_flexible_date("Rajab 1445")
    assert result.startswith("2024-01")

    result = parse_flexible_date("15 Shawwal 1443")
    assert result.startswith("2022-05")

def test_parse_hijri_numeric():
    """Numeric dates with Hijri year range (1300-1500) → converted to Gregorian."""
    # 1428/08/11 = 11 Sha'ban 1428
    result = parse_flexible_date("1428/08/11")
    assert result.startswith("2007-08")

    # Pure year
    result = parse_flexible_date("1445")
    assert result.startswith("2023-")

def test_parse_dot_separated():
    """European dot-separated format: DD.MM.YYYY."""
    assert parse_flexible_date("15.03.2023") == "2023-03-15"
    assert parse_flexible_date("1.1.2000") == "2000-01-01"
    assert parse_flexible_date("31.12.1999") == "1999-12-31"

def test_parse_trailing_era_markers():
    """Dates with trailing era markers: AH, A.H., AD, A.D., CE, م, هـ."""
    assert parse_flexible_date("15 March 2023 AD") == "2023-03-15"
    assert parse_flexible_date("15 March 2023 A.D.") == "2023-03-15"
    assert parse_flexible_date("January 2020 CE") == "2020-01-01"

    # Hijri with هـ marker
    result = parse_flexible_date("11 شعبان 1428 هـ")
    assert result.startswith("2007-08")

    # English Hijri with AH marker — after stripping AH, pure Hijri date remains
    result = parse_flexible_date("11 Sha'ban 1428 AH")
    assert result.startswith("2007-08")

def test_parse_whitespace_handling():
    """Extra whitespace, leading/trailing spaces."""
    assert parse_flexible_date("  15/03/2023  ") == "2023-03-15"
    assert parse_flexible_date("  May 2023  ") == "2023-05-01"
    assert parse_flexible_date(" 2023 ") == "2023-01-01"

def test_parse_still_raises_on_garbage():
    """Still raises ValueError on truly unparseable input."""
    with pytest.raises(ValueError):
        parse_flexible_date("garbage")
    with pytest.raises(ValueError):
        parse_flexible_date("not a date at all")
    with pytest.raises(ValueError):
        parse_flexible_date("")

def test_canonicalize_with_llm_empty():
    client = MockLLMClient()
    res = canonicalize_with_llm([], client)
    assert res == {}

def test_canonicalize_with_llm_missing_keys():
    class MissingKeyLLMClient:
        default_model = "test_model"
        def _route_llm_call(self, *args, **kwargs):
            return '{"احمد": "احمد"}'
    
    with pytest.raises(RuntimeError, match="LLM dropped names from the mapping"):
        canonicalize_with_llm(["احمد", "محمد"], MissingKeyLLMClient())

def test_process_cleaning_phase_integration(tmp_path):
    """Full integration test for the cleaning phase pipeline."""
    json_path = tmp_path / "integration_report.json"
    
    # Data for 2 tenants: 
    # T1: Qualifies (1 anchor, 5 pages, mixed dates)
    # T2: Fails (0 anchors, 10 pages)
    # T3: Fails (1 anchor, 3 pages)
    data = []
    # T1: Qualified
    for i in range(5):
        cat = "contract" if i == 0 else "other"
        data.append({
            "category": cat,
            "content_explanation": "T1 page",
            "expected_tenant_name": "Ahmed Mohamed",
            "date": "2023-01-01" if i == 0 else (None if i == 1 else "2023-01-05"),
            "sender": "S", "receiver": "R", "subject": "Sub"
        })
    # T2: Unqualified (No anchor)
    for i in range(10):
        data.append({
            "category": "other",
            "content_explanation": "T2 page",
            "expected_tenant_name": "Tenant Two",
            "date": "2023-02-01",
            "sender": "S", "receiver": "R", "subject": "Sub"
        })
    # T3: Unqualified (Too few pages)
    for i in range(3):
        data.append({
            "category": "contract",
            "content_explanation": "T3 page",
            "expected_tenant_name": "Tenant Three",
            "date": "2023-03-01",
            "sender": "S", "receiver": "R", "subject": "Sub"
        })
    
    json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    
    # Mock LLM to return identities as-is
    class IdentityMockLLM(MockLLMClient):
        def _route_llm_call(self, *args, **kwargs):
            # Extract names from prompt
            import re
            prompt = kwargs.get('contents', [''])[0]
            names = re.findall(r'"([^"]*)"', prompt)
            # Return a mapping of name -> name (mocking normalization)
            mapping = {n: n for n in names if n}
            return json.dumps(mapping, ensure_ascii=False)

    pages = process_cleaning_phase(json_path, IdentityMockLLM())
    
    # T1 should be mapped to a canonical tenant
    t1_pages = [p for p in pages if "Ahmed Mohamed" in p.expected_tenant_name]
    assert all(p.canonical_tenant == "Ahmed Mohamed" for p in t1_pages)
    
    # T2 and T3 should be unassigned
    t2_pages = [p for p in pages if "Tenant Two" in p.expected_tenant_name]
    assert all("Unassigned" in p.canonical_tenant for p in t2_pages)
    
    t3_pages = [p for p in pages if "Tenant Three" in p.expected_tenant_name]
    assert all("Unassigned" in p.canonical_tenant for p in t3_pages)
