import re

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
