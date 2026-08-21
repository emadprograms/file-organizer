from src.core.utils import normalize_date

def test_normalize_arabic_numerals():
    # Eastern Arabic numerals
    assert normalize_date('٢٠٢٥-٠١-١٥') == '2025-01-15'
    assert normalize_date('٢٠٢٦-١٢-٣١') == '2026-12-31'
    
    # Standard English/Western numerals
    assert normalize_date('2025-01-15') == '2025-01-15'
    
    # Non-date strings
    assert normalize_date('nodate') == 'nodate'
    assert normalize_date('unknown - document.pdf') == 'unknown---document.pdf'
    
    # None handling
    assert normalize_date(None) == 'NONE'

def test_normalize_arabic_numerals_mixed():
    # Mixed strings
    assert normalize_date('Doc-٢٠٢٥-01') == 'Doc-2025-01'
