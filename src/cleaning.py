import json
import re
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

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
