import json
import re
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import unicodedata
from rapidfuzz import fuzz
from src.llm_client import LLMClient
from google.genai import types

class PageData(BaseModel):
    category: str
    content_explanation: str
    expected_tenant_name: Optional[str]
    date: Optional[str]
    sender: str
    receiver: str
    subject: str

    canonical_tenant: Optional[str] = None
    resolved_date: Optional[str] = None
    original_index: int

class TenantTimeline(BaseModel):
    canonical_name: str
    min_date: str
    max_date: str

def parse_flexible_date(date_str: str) -> str:
    # Handle "May 2023"
    month_map = {
        "january": "01", "jan": "01",
        "february": "02", "feb": "02",
        "march": "03", "mar": "03",
        "april": "04", "apr": "04",
        "may": "05",
        "june": "06", "jun": "06",
        "july": "07", "jul": "07",
        "august": "08", "aug": "08",
        "september": "09", "sep": "09",
        "october": "10", "oct": "10",
        "november": "11", "nov": "11",
        "december": "12", "dec": "12"
    }
    
    date_str_lower = date_str.strip().lower()

    # match "May 2023" or "May-2023"
    m_month_word = re.match(r"^([a-z]+)[\s-]+(\d{4})$", date_str_lower)
    if m_month_word:
        month_word, year = m_month_word.groups()
        month = month_map.get(month_word)
        if month:
            return f"{year}-{month}-01"

    # match "YYYY-MM-DD"
    m_ymd = re.match(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$", date_str)
    if m_ymd:
        y, m, d = m_ymd.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # match "DD/MM/YYYY" or "DD-MM-YYYY"
    m_dmy = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", date_str)
    if m_dmy:
        d, m, y = m_dmy.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # match "YYYY-MM" or "MM-YYYY" or "YYYY/MM" or "MM/YYYY"
    m_ym = re.match(r"^(\d{4})[/-](\d{1,2})$", date_str)
    if m_ym:
        y, m = m_ym.groups()
        return f"{y}-{int(m):02d}-01"

    m_my = re.match(r"^(\d{1,2})[/-](\d{4})$", date_str)
    if m_my:
        m, y = m_my.groups()
        return f"{y}-{int(m):02d}-01"

    # match "YYYY"
    m_y = re.match(r"^(\d{4})$", date_str)
    if m_y:
        y = m_y.group(1)
        return f"{y}-01-01"

    raise ValueError(f"Could not parse date: {date_str}")

def load_and_parse_json(json_path: Path) -> list[PageData]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pages = []
    for i, item in enumerate(data):
        date_val = item.get("date")
        if date_val is not None:
            # normalize date
            date_val = parse_flexible_date(date_val)
            item["date"] = date_val
        
        item["original_index"] = i
        pages.append(PageData(**item))

    assert len(pages) == len(data), "Mismatch in parsed pages and source array length."
    return pages

def infer_missing_dates(pages: list[PageData]) -> None:
    # Get all indices with a valid date
    valid_dates = [(p.original_index, p.date) for p in pages if p.date is not None]
    
    for page in pages:
        if page.date is not None:
            page.resolved_date = page.date
        else:
            if not valid_dates:
                continue # No valid dates at all, can't infer
            
            # Find the closest date
            # Distance is abs(valid_idx - page.original_index)
            # Tie break is valid_idx < page.original_index
            closest = min(valid_dates, key=lambda x: (abs(x[0] - page.original_index), x[0]))
            page.resolved_date = closest[1]

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
    names_list = list(names)
    normalized_map = {n: normalize_arabic_text(n) for n in names_list}
    
    assigned_clusters = []
    for name in names_list:
        norm = normalized_map[name]
        found = False
        for cluster in assigned_clusters:
            rep_name = next(iter(cluster))
            rep_norm = normalized_map[rep_name]
            score = fuzz.ratio(norm, rep_norm)
            if score >= 85:
                cluster.add(name)
                found = True
                break
        if not found:
            assigned_clusters.append({name})
            
    mapping = {}
    for cluster in assigned_clusters:
        longest = max(cluster, key=len)
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
    
    response = llm_client.generate_content(
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0
        )
    )
    
    if not response or not response.text:
        raise RuntimeError("LLM returned empty response")
        
    result_map = json.loads(response.text)
    
    missing_keys = set(unresolved_names) - set(result_map.keys())
    assert not missing_keys, f"LLM dropped names from the mapping: {missing_keys}"
    
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
                assert min_date <= max_date, f"min_date {min_date} > max_date {max_date}"
                timelines.append(TenantTimeline(
                    canonical_name=name,
                    min_date=min_date,
                    max_date=max_date
                ))
                
    return timelines
