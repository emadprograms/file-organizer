from src.reconcile.core import _normalize_arabic_numerals

def test_normalize_arabic_numerals():
    # Eastern Arabic numerals
    assert _normalize_arabic_numerals('٢٠٢٥-٠١-١٥') == '2025-01-15'
    assert _normalize_arabic_numerals('٢٠٢٦-١٢-٣١') == '2026-12-31'
    
    # Standard English/Western numerals
    assert _normalize_arabic_numerals('2025-01-15') == '2025-01-15'
    
    # Non-date strings
    assert _normalize_arabic_numerals('nodate') == 'nodate'
    assert _normalize_arabic_numerals('unknown - document.pdf') == 'unknown - document.pdf'
    
    # None handling
    assert _normalize_arabic_numerals(None) is None

def test_normalize_arabic_numerals_mixed():
    # Mixed strings
    assert _normalize_arabic_numerals('Doc-٢٠٢٥-01') == 'Doc-2025-01'
