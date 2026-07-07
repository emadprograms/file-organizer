import json
import re
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import unicodedata
from rapidfuzz import fuzz
import logging

from src.llm.llm import LLMClient
from google.genai import types

logger = logging.getLogger("file_organizer")

class PageData(BaseModel):
    category: str
    content_explanation: str
    expected_tenant_name: Optional[str] = None
    expected_house_number: Optional[str] = None
    date: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    subject: Optional[str] = None

    canonical_tenant: Optional[str] = None
    resolved_date: Optional[str] = None
    original_index: int

class TenantTimeline(BaseModel):
    canonical_name: str
    min_date: str
    max_date: str

# --- Date parsing constants (module-level to avoid re-creation per call) ---

# English month name -> month number (all lowercase)
_ENGLISH_MONTH_MAP: dict[str, str] = {
    "january": "01", "jan": "01",
    "february": "02", "feb": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09", "sept": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12",
}

# Arabic Gregorian month name -> month number
_ARABIC_GREGORIAN_MONTH_MAP: dict[str, str] = {
    "يناير": "01",
    "فبراير": "02",
    "مارس": "03",
    "أبريل": "04", "ابريل": "04",
    "مايو": "05",
    "يونيو": "06",
    "يوليو": "07",
    "أغسطس": "08", "اغسطس": "08",
    "سبتمبر": "09",
    "أكتوبر": "10", "اكتوبر": "10",
    "نوفمبر": "11",
    "ديسمبر": "12",
}

# Hijri month name -> Hijri month number (Arabic script)
_HIJRI_ARABIC_MONTH_MAP: dict[str, int] = {
    "محرم": 1,
    "صفر": 2,
    "ربيع الأول": 3, "ربيع الاول": 3,
    "ربيع الثاني": 4, "ربيع الآخر": 4, "ربيع الاخر": 4,
    "جمادى الأولى": 5, "جمادى الاولى": 5,
    "جمادى الثانية": 6, "جمادى الآخرة": 6, "جمادى الاخرة": 6,
    "رجب": 7,
    "شعبان": 8,
    "رمضان": 9,
    "شوال": 10,
    "ذو القعدة": 11, "ذوالقعدة": 11,
    "ذو الحجة": 12, "ذوالحجة": 12,
}

# Hijri month name -> Hijri month number (English transliteration)
_HIJRI_ENGLISH_MONTH_MAP: dict[str, int] = {
    "muharram": 1,
    "safar": 2,
    "rabi' al-awwal": 3, "rabi al-awwal": 3, "rabi ul awal": 3,
    "rabi' al-thani": 4, "rabi al-thani": 4, "rabi ul thani": 4,
    "jumada al-ula": 5, "jumada al-awwal": 5, "jumada al ula": 5,
    "jumada al-thani": 6, "jumada al-thaniyah": 6, "jumada al thani": 6,
    "rajab": 7,
    "sha'ban": 8, "shaban": 8, "shaaban": 8,
    "ramadan": 9, "ramadhan": 9,
    "shawwal": 10, "shawal": 10,
    "dhu al-qi'dah": 11, "dhu al-qidah": 11, "dhul qidah": 11, "dhul qi'dah": 11,
    "dhu al-hijjah": 12, "dhu al-hijja": 12, "dhul hijjah": 12, "dhul hijja": 12,
}

# English weekday names to strip
_WEEKDAY_PATTERN = re.compile(
    r'^(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday'
    r'|mon|tue|wed|thu|fri|sat|sun)[,.]?\s+',
    re.IGNORECASE
)

# Ordinal suffix pattern (1st, 2nd, 3rd, 4th, 11th, 21st, etc.)
_ORDINAL_SUFFIX = re.compile(r'(\d+)(?:st|nd|rd|th)\b', re.IGNORECASE)


def _hijri_to_gregorian(year: int, month: int, day: int) -> str:
    """Convert a Hijri date to Gregorian YYYY-MM-DD using hijridate."""
    from hijridate import Hijri
    g = Hijri(year, month, day).to_gregorian()
    return f"{g.year}-{g.month:02d}-{g.day:02d}"


def _is_hijri_year(year: int) -> bool:
    """Heuristic: Hijri years fall roughly in 1300-1500 range for modern dates."""
    return 1300 <= year <= 1500


def parse_flexible_date(date_str: str) -> str:
    """Parse a wide variety of date formats into Gregorian YYYY-MM-DD.

    Supports:
    - Numeric: YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY, YYYY-MM, MM-YYYY, YYYY
    - English month names (full and abbreviated): "29 February 2024",
      "July 11, 2010", "3 SEP 2007", "May 2023"
    - English with ordinal suffixes: "1st January 2024", "March 3rd, 2020"
    - English with weekday prefixes: "Monday, 27 September 2007"
    - Arabic Gregorian month names: "5 مارس 2024م", "يناير 2020"
    - Dual-calendar dates: strips Hijri parentheticals and slash-separated
      Hijri calendar suffixes, keeps the Gregorian portion
    - Pure Hijri dates (Arabic or English transliteration):
      "11 شعبان 1428 هـ" or "11 Sha'ban 1428 AH" → converted to Gregorian
    - Hijri numeric dates where the year is in the 1300-1500 range:
      "1428/08/11" → converted to Gregorian
    """
    date_str_clean = date_str.strip()

    # --- Pre-processing: strip noise before attempting patterns ---

    # Remove Hijri parenthetical suffix, e.g. "(11 Sha'ban 1428 AH)"
    date_str_clean = re.sub(r'\s*\([^)]*\)\s*$', '', date_str_clean).strip()

    # Remove slash-separated Hijri calendar suffix, e.g. "/ Rabi' al-Thani 1431 AH"
    # Only strip if what follows the slash contains non-digit text (to avoid stripping DD/MM/YYYY)
    date_str_clean = re.sub(r'\s*/\s*[A-Za-z].*$', '', date_str_clean).strip()

    # Remove Arabic year marker "م" (miim) and Hijri marker "هـ" / "ه"
    date_str_clean = re.sub(r'(?:م|هـ|ه)\s*$', '', date_str_clean).strip()

    # Remove trailing "AH" or "A.H." (Anno Hegirae in English)
    date_str_clean = re.sub(r'\s*A\.?H\.?\s*$', '', date_str_clean, flags=re.IGNORECASE).strip()

    # Remove trailing "AD" or "A.D." or "CE"
    date_str_clean = re.sub(r'\s*(?:A\.?D\.?|CE)\s*$', '', date_str_clean, flags=re.IGNORECASE).strip()

    # Strip weekday prefix, e.g. "Monday, 27 September 2007" -> "27 September 2007"
    date_str_clean = _WEEKDAY_PATTERN.sub('', date_str_clean).strip()

    # Strip Arabic weekday prefix (الأحد، الاثنين، الثلاثاء، الأربعاء، الخميس، الجمعة، السبت)
    date_str_clean = re.sub(
        r'^(?:الأحد|الاحد|الاثنين|الإثنين|الثلاثاء|الأربعاء|الاربعاء|الخميس|الجمعة|السبت)[،,]?\s+',
        '', date_str_clean
    ).strip()

    # Replace ordinal suffixes: "1st" -> "1", "3rd" -> "3", "27th" -> "27"
    date_str_clean = _ORDINAL_SUFFIX.sub(r'\1', date_str_clean)

    # Normalize dots as separators to slashes for numeric dates (DD.MM.YYYY -> DD/MM/YYYY)
    # Only if it looks like a numeric-dot date (not "Dr." or abbreviations)
    if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', date_str_clean):
        date_str_clean = date_str_clean.replace('.', '/')

    date_str_lower = date_str_clean.lower()

    # --- Pure Hijri dates (Arabic month names) ---
    # Must check BEFORE Arabic Gregorian months since patterns overlap

    # Match "DD HijriMonth YYYY" e.g. "11 شعبان 1428"
    # Hijri months can be multi-word (ربيع الأول) so we match greedily
    for hijri_name, hijri_month_num in _HIJRI_ARABIC_MONTH_MAP.items():
        pattern = re.compile(
            r'^(\d{1,2})\s+' + re.escape(hijri_name) + r'\s+(\d{4})$'
        )
        m = pattern.match(date_str_clean)
        if m:
            d, y = int(m.group(1)), int(m.group(2))
            if _is_hijri_year(y):
                return _hijri_to_gregorian(y, hijri_month_num, d)

    # Match "HijriMonth YYYY" (month only, no day)
    for hijri_name, hijri_month_num in _HIJRI_ARABIC_MONTH_MAP.items():
        pattern = re.compile(
            r'^' + re.escape(hijri_name) + r'\s+(\d{4})$'
        )
        m = pattern.match(date_str_clean)
        if m:
            y = int(m.group(1))
            if _is_hijri_year(y):
                return _hijri_to_gregorian(y, hijri_month_num, 1)

    # --- Pure Hijri dates (English transliteration) ---
    # Match "DD HijriMonth YYYY" e.g. "11 Sha'ban 1428"
    for hijri_name, hijri_month_num in _HIJRI_ENGLISH_MONTH_MAP.items():
        pattern = re.compile(
            r'^(\d{1,2})\s+' + re.escape(hijri_name) + r'\s+(\d{4})$',
            re.IGNORECASE
        )
        m = pattern.match(date_str_clean)
        if m:
            d, y = int(m.group(1)), int(m.group(2))
            if _is_hijri_year(y):
                return _hijri_to_gregorian(y, hijri_month_num, d)

    # Match "HijriMonth YYYY" (English transliteration, no day)
    for hijri_name, hijri_month_num in _HIJRI_ENGLISH_MONTH_MAP.items():
        pattern = re.compile(
            r'^' + re.escape(hijri_name) + r'\s+(\d{4})$',
            re.IGNORECASE
        )
        m = pattern.match(date_str_clean)
        if m:
            y = int(m.group(1))
            if _is_hijri_year(y):
                return _hijri_to_gregorian(y, hijri_month_num, 1)

    # --- Arabic Gregorian month names ---

    # Match "DD ArabicMonth YYYY" e.g. "5 مارس 2024"
    m_ar_dmy = re.match(r'^(\d{1,2})\s+(\S+)\s+(\d{4})$', date_str_clean)
    if m_ar_dmy:
        d, month_word, y = m_ar_dmy.groups()
        month = _ARABIC_GREGORIAN_MONTH_MAP.get(month_word)
        if month:
            return f"{y}-{month}-{int(d):02d}"

    # Match "ArabicMonth YYYY" e.g. "مارس 2024"
    m_ar_my = re.match(r'^(\S+)\s+(\d{4})$', date_str_clean)
    if m_ar_my:
        month_word, y = m_ar_my.groups()
        month = _ARABIC_GREGORIAN_MONTH_MAP.get(month_word)
        if month:
            return f"{y}-{month}-01"

    # --- English "DD MonthName YYYY" e.g. "29 February 2024", "3 SEP 2007" ---
    m_dmy_word = re.match(r'^(\d{1,2})\s+([a-z]+)\s+(\d{4})$', date_str_lower)
    if m_dmy_word:
        d, month_word, y = m_dmy_word.groups()
        month = _ENGLISH_MONTH_MAP.get(month_word)
        if month:
            return f"{y}-{month}-{int(d):02d}"

    # --- English "MonthName DD, YYYY" e.g. "July 11, 2010", "April 18, 2006" ---
    m_mdy_word = re.match(r'^([a-z]+)\s+(\d{1,2}),?\s+(\d{4})$', date_str_lower)
    if m_mdy_word:
        month_word, d, y = m_mdy_word.groups()
        month = _ENGLISH_MONTH_MAP.get(month_word)
        if month:
            return f"{y}-{month}-{int(d):02d}"

    # --- English "MonthName YYYY" or "MonthName-YYYY" e.g. "May 2023" ---
    m_month_word = re.match(r'^([a-z]+)[\s-]+(\d{4})$', date_str_lower)
    if m_month_word:
        month_word, year = m_month_word.groups()
        month = _ENGLISH_MONTH_MAP.get(month_word)
        if month:
            return f"{year}-{month}-01"

    # --- Numeric formats ---

    # match "YYYY-MM-DD" or "YYYY/MM/DD"
    m_ymd = re.match(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$', date_str_clean)
    if m_ymd:
        y, m, d = int(m_ymd.group(1)), int(m_ymd.group(2)), int(m_ymd.group(3))
        # If year looks Hijri, convert
        if _is_hijri_year(y):
            return _hijri_to_gregorian(y, m, d)
        return f"{y}-{m:02d}-{d:02d}"

    # match "DD/MM/YYYY" or "DD-MM-YYYY"
    m_dmy = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', date_str_clean)
    if m_dmy:
        d, m, y = int(m_dmy.group(1)), int(m_dmy.group(2)), int(m_dmy.group(3))
        # If year looks Hijri, convert
        if _is_hijri_year(y):
            return _hijri_to_gregorian(y, m, d)
        return f"{y}-{m:02d}-{d:02d}"

    # match "YYYY-MM" or "YYYY/MM"
    m_ym = re.match(r'^(\d{4})[/-](\d{1,2})$', date_str_clean)
    if m_ym:
        y, m = int(m_ym.group(1)), int(m_ym.group(2))
        if _is_hijri_year(y):
            return _hijri_to_gregorian(y, m, 1)
        return f"{y}-{m:02d}-01"

    # match "MM-YYYY" or "MM/YYYY"
    m_my = re.match(r'^(\d{1,2})[/-](\d{4})$', date_str_clean)
    if m_my:
        m, y = int(m_my.group(1)), int(m_my.group(2))
        if _is_hijri_year(y):
            return _hijri_to_gregorian(y, m, 1)
        return f"{y}-{m:02d}-01"

    # match "YYYY"
    m_y = re.match(r'^(\d{4})$', date_str_clean)
    if m_y:
        y = int(m_y.group(1))
        if _is_hijri_year(y):
            return _hijri_to_gregorian(y, 1, 1)
        return f"{y}-01-01"

    raise ValueError(f"Could not parse date: {date_str}")

def load_and_parse_json(json_path: Path) -> list[PageData]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = []
    # If data is a list, iterate normally. If it's a dict (like the categorized report), iterate over sorted keys.
    if isinstance(data, dict):
        items = [data[k] for k in sorted(data.keys(), key=int)]
    else:
        items = data

    for i, item in enumerate(items):
        date_val = item.get("date")
        if date_val is not None:
            # normalize date
            try:
                date_val = parse_flexible_date(date_val)
                item["date"] = date_val
            except ValueError:
                item["date"] = None
        
        item["original_index"] = i
        pages.append(PageData(**item))

    if len(pages) != len(data):
        raise RuntimeError("Mismatch in parsed pages and source array length.")
    return pages

def infer_missing_dates(pages: list[PageData]) -> None:
    # Get all indices with a valid date
    valid_dates = [(p.original_index, p.date) for p in pages if p.date is not None]
    logger.info(f"Found {len(valid_dates)} pages with valid dates out of {len(pages)} total pages.")
    
    inferred_count = 0
    for page in pages:
        if page.date is not None:
            page.resolved_date = page.date
        else:
            if not valid_dates:
                continue # No valid dates at all, can't infer
            
            # Find the closest date
            closest = min(valid_dates, key=lambda x: (abs(x[0] - page.original_index), x[0]))
            page.resolved_date = closest[1]
            inferred_count += 1
            
    if inferred_count > 0:
        logger.info(f"Successfully inferred {inferred_count} missing dates using closest proximity matching.")

def normalize_arabic_text(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    # Strip diacritics
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    # Normalize alef
    text = re.sub(r'[أإآ]', 'ا', text)
    # Normalize teh marbuta
    text = re.sub(r'ة', 'ه', text)
    # Normalize alef maksura / yeh
    text = re.sub(r'ى', 'ي', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def cluster_names_fuzzily(names: set[str]) -> dict[str, str]:
    names_list = sorted(list(names))
    normalized_map = {n: normalize_arabic_text(n) for n in names_list}
    
    assigned_clusters = []
    for name in names_list:
        norm = normalized_map[name]
        found = False
        for cluster in assigned_clusters:
            rep_name = cluster[0]
            rep_norm = normalized_map[rep_name]
            score = fuzz.ratio(norm, rep_norm)
            if score >= 85:
                cluster.append(name)
                found = True
                break
        if not found:
            assigned_clusters.append([name])
            
    mapping = {}
    for cluster in assigned_clusters:
        longest = sorted(cluster, key=lambda x: (-len(x), x))[0]
        for name in cluster:
            mapping[name] = longest
            
    return mapping

def canonicalize_with_llm(unresolved_names: list[str], llm_client: LLMClient) -> dict[str, str]:
    if not unresolved_names:
        return {}
        
    prompt = f"""
Please map the following raw tenant names to unified canonical identities.
Merge transliterations and OCR errors into a single canonical name.
IMPORTANT: Output all canonical identities strictly in Arabic.

Raw names:
{json.dumps(unresolved_names, ensure_ascii=False)}

Respond ONLY with a JSON dictionary where keys are the raw names and values are the canonical Arabic names.
"""
    
    response_text = llm_client._route_llm_call(
        model=llm_client.default_model,
        contents=[prompt],
        response_schema=None,
        log_prefix="CanonicalizeLLM"
    )
    
    if not response_text:
        raise RuntimeError("LLM returned empty response")
        
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:-3].strip()
    elif response_text.startswith("```"):
        response_text = response_text[3:-3].strip()
        
    try:
        result_map = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned malformed JSON: {e}\nResponse text: {response_text}") from e
        
    if not isinstance(result_map, dict):
        raise RuntimeError(f"LLM did not return a JSON object (got {type(result_map).__name__})")
    
    missing_keys = set(unresolved_names) - set(result_map.keys())
    if missing_keys:
        raise RuntimeError(f"LLM dropped names from the mapping: {missing_keys}")
    
    return result_map

def build_tenant_timelines(pages: list[PageData], canonical_mapping: dict[str, str]) -> list[TenantTimeline]:
    anchor_categories = {"contract", "forms", "id_cards"}
    
    tenant_stats = {}
    for page in pages:
        raw_name = page.expected_tenant_name
        if not raw_name:
            continue
            
        canonical_name = canonical_mapping.get(raw_name, raw_name)
        if canonical_name not in tenant_stats:
            tenant_stats[canonical_name] = {"anchor_count": 0, "total_count": 0, "dates": []}
            
        stats = tenant_stats[canonical_name]
        stats["total_count"] += 1
        
        if page.category in anchor_categories:
            stats["anchor_count"] += 1
            
        if page.resolved_date:
            stats["dates"].append(page.resolved_date)
            
    timelines = []
    for name, stats in tenant_stats.items():
        if stats["anchor_count"] >= 1 and stats["total_count"] >= 5:
            if stats["dates"]:
                min_date = min(stats["dates"])
                max_date = max(stats["dates"])
                if min_date > max_date:
                    raise RuntimeError(f"min_date {min_date} > max_date {max_date}")
                logger.info(f"Qualified Tenant '{name}': {stats['total_count']} pages, {stats['anchor_count']} anchors -> Timeline: {min_date} to {max_date}")
                timelines.append(TenantTimeline(
                    canonical_name=name,
                    min_date=min_date,
                    max_date=max_date
                ))
            else:
                logger.info(f"Rejected Tenant '{name}': Missing valid dates.")
        else:
            logger.info(f"Rejected Tenant '{name}': {stats['total_count']} pages, {stats['anchor_count']} anchors (Failed threshold of >=1 anchors, >=5 pages)")
                
    return timelines

def assign_pages_to_tenants(pages: list[PageData], timelines: list[TenantTimeline]) -> None:
    for page in pages:
        if not page.resolved_date:
            page.canonical_tenant = "Unassigned (Unknown)"
            continue
            
        covering = []
        for t in timelines:
            if t.min_date <= page.resolved_date <= t.max_date:
                covering.append(t)
                
        if covering:
            covering.sort(key=lambda t: t.min_date)
            page.canonical_tenant = covering[0].canonical_name
        else:
            month_str = page.resolved_date[:7]
            page.canonical_tenant = f"Unassigned ({month_str})"

def process_cleaning_phase(json_path: Path, llm_client: LLMClient) -> list[PageData]:
    logger.info("==================================================")
    logger.info(f"           PHASE 1: DOCUMENT CLEANING             ")
    logger.info("==================================================")
    
    pages = load_and_parse_json(json_path)
    logger.info(f"Loaded {len(pages)} pages from {json_path}")
    
    logger.info("\n>>> DATE CLEANING WORKFLOW")
    infer_missing_dates(pages)
    
    logger.info("\n>>> NAME CLEANING WORKFLOW")
    anchor_categories = {"contract", "forms", "id_cards"}
    unique_anchors_seen = set()
    
    for page in pages:
        if page.expected_tenant_name:
            if page.category in anchor_categories:
                if page.expected_tenant_name not in unique_anchors_seen:
                    logger.info(f"Identified anchor document (category: {page.category}). Extracted name: '{page.expected_tenant_name}'")
                    unique_anchors_seen.add(page.expected_tenant_name)

    unique_names = {p.expected_tenant_name for p in pages if p.expected_tenant_name}
    logger.info(f"Total unique raw names extracted across all pages: {len(unique_names)}")
    
    fuzzy_map = cluster_names_fuzzily(unique_names)
    representatives = list(set(fuzzy_map.values()))
    logger.info(f"Clustered down to {len(representatives)} representative names via Fuzzy Matching.")
    
    logger.debug(f"Sending representative names to LLM: {representatives}")
    llm_map = canonicalize_with_llm(representatives, llm_client)
    for rep, canon in llm_map.items():
        logger.info(f"LLM normalized representative: '{rep}' -> '{canon}'")
    
    final_mapping = {}
    for raw, rep in fuzzy_map.items():
        final_mapping[raw] = llm_map.get(rep, rep)
        
    logger.info("\n>>> TIMELINE BUILDING")
    timelines = build_tenant_timelines(pages, final_mapping)
    
    logger.info("\n>>> FINAL OUTPUT FOR EACH DOCUMENT")
    assign_pages_to_tenants(pages, timelines)
    
    logger.info("┌──────┬────────────┬────────────┬────────────────────────────────────────┐")
    logger.info("│ Page │ Date       │ Category   │ Tenant                                 │")
    logger.info("├──────┼────────────┼────────────┼────────────────────────────────────────┤")
    for page in pages:
        if page.canonical_tenant is None:
            raise RuntimeError("Page is missing canonical_tenant")
            
        date_str = page.resolved_date or "N/A"
        # We manually format the columns. The Tenant column gets 38 chars of space.
        logger.info(f"│ {page.original_index:02d}   │ {date_str:<10} │ {page.category:<10} │ {page.canonical_tenant:<38} │")
    logger.info("└──────┴────────────┴────────────┴────────────────────────────────────────┘")
    logger.info(f"Successfully mapped {len(pages)} pages to their respective canonical tenants.")
        
    logger.info("\n==================================================")
    logger.info("           CLEANING PHASE COMPLETE                ")
    logger.info("==================================================")
    return pages
