"""Utility functions for filename sanitization and date parsing/normalization."""

import re
from typing import Optional

def sanitize_filename(name: str, max_length: int = 50) -> str:
    """Sanitize a string to be used as a valid filename.
    
    Replaces illegal characters with underscores, collapses multiple
    underscores, and truncates to a maximum length while preserving
    multi-byte UTF-8 characters.
    
    Args:
        name (str): The original filename to sanitize.
        max_length (int): The maximum allowed length for the filename. Defaults to 50.
        
    Returns:
        str: The sanitized filename.
    """
    # Replace illegal characters with underscore
    sanitized = re.sub(r'[/\\:*?"<>|]', '_', name)
    sanitized = sanitized.strip()
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Ensure truncation doesn't split a multi-byte UTF-8 character
    encoded = sanitized.encode('utf-8')
    if len(encoded) > max_length:
        # We truncate based on characters, not bytes to avoid splitting multi-byte characters
        sanitized = sanitized[:max_length]
        
    return sanitized

def parse_datetime_str(date_str: str) -> Optional[str]:
    """Parse a date string into a normalized YYYY-MM-DD format.
    
    Attempts to parse numeric formats and formats containing English,
    Arabic, or French month names. Also handles two-digit years.
    
    Args:
        date_str (str): The raw date string.
        
    Returns:
        Optional[str]: The normalized YYYY-MM-DD string, or None if parsing fails.
    """
    # Helper for 2-digit years
    def fix_year(y: int) -> int:
        if y < 100:
            return y + 2000 if y < 50 else y + 1900
        return y

    # 4. Numeric formats
    # YYYY/MM/DD, YYYY-MM-DD, YYYY.MM.DD, YYYY MM DD
    m = re.match(r'^(\d{4})[./\-\s]+(\d{1,2})[./\-\s]+(\d{1,2})$', date_str)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        
    # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD MM YYYY (and YY versions)
    m = re.match(r'^(\d{1,2})[./\-\s]+(\d{1,2})[./\-\s]+(\d{2,4})$', date_str)
    if m:
        y = fix_year(int(m.group(3)))
        return f"{y}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

    # 5. Month name formats
    months = {
        "jan": "01", "january": "01", "يناير": "01", "جانفي": "01",
        "feb": "02", "february": "02", "فبراير": "02", "فيفري": "02",
        "mar": "03", "march": "03", "مارس": "03",
        "apr": "04", "april": "04", "أبريل": "04", "ابريل": "04", "افريل": "04",
        "may": "05", "مايو": "05", "ماي": "05",
        "jun": "06", "june": "06", "يونيو": "06", "جوان": "06",
        "jul": "07", "july": "07", "يوليو": "07", "جويلية": "07",
        "aug": "08", "august": "08", "أغسطس": "08", "اغسطس": "08", "اوت": "08", "أوت": "08",
        "sep": "09", "september": "09", "sept": "09", "سبتمبر": "09",
        "oct": "10", "october": "10", "أكتوبر": "10", "اكتوبر": "10",
        "nov": "11", "november": "11", "نوفمبر": "11",
        "dec": "12", "december": "12", "ديسمبر": "12"
    }
    
    # DD [Month] YYYY or DD-[Month]-YYYY (e.g. 09 DEC 2006, 02-JUL-08)
    m = re.search(r'^(\d{1,2})[\s\-]+([A-Za-z\u0600-\u06FF]+)[\s\-]+(\d{2,4})$', date_str)
    if m:
        d = int(m.group(1))
        mon = m.group(2).lower()
        y = fix_year(int(m.group(3)))
        if mon in months:
            return f"{y}-{months[mon]}-{d:02d}"

    # YYYY [Month] DD (e.g. 2010 ابريل 7)
    m = re.search(r'^(\d{4})[\s\-]+([A-Za-z\u0600-\u06FF]+)[\s\-]+(\d{1,2})$', date_str)
    if m:
        y = int(m.group(1))
        mon = m.group(2).lower()
        d = int(m.group(3))
        if mon in months:
            return f"{y}-{months[mon]}-{d:02d}"
            
    # [Month] YYYY (e.g. نوفمبر 2009)
    m = re.search(r'^([A-Za-z\u0600-\u06FF]+)[\s\-]+(\d{4})$', date_str)
    if m:
        mon = m.group(1).lower()
        y = int(m.group(2))
        if mon in months:
            return f"{y}-{months[mon]}-01"
            
    return None

def normalize_date(date_str: str) -> str:
    """Normalize and format a date string.
    
    Converts Eastern Arabic numerals to Western, removes extraneous text
    (e.g., days of the week, Arabic year suffixes), and attempts to parse
    the string into a YYYY-MM-DD format.
    
    Args:
        date_str (str): The raw date string to normalize.
        
    Returns:
        str: The normalized date string, or a sanitized version of the input
             if parsing fails. Returns 'NONE' if the input is empty or 'NONE'.
    """
    if not date_str or date_str.upper() == "NONE":
        return "NONE"
        
    # 1. Convert Eastern Arabic numerals to Western
    eastern_to_western = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    for e, w in eastern_to_western.items():
        date_str = date_str.replace(e, w)
        
    # 2. Clean up string
    date_str = date_str.strip()
    # Remove 'م' or 'هـ' at the end (sometimes separated by space)
    date_str = re.sub(r'\s*[مهـ]\s*$', '', date_str)
    # Remove days of the week
    date_str = re.sub(r'(?i)^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)[, ]+', '', date_str)
    date_str = date_str.strip()
    
    # 3. Handle Already YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
        
    parsed = parse_datetime_str(date_str)
    if parsed:
        return parsed
        
    # Fallback sanitize
    return re.sub(r'[/\\:*?"<>|\s]', '-', date_str).strip('-')
