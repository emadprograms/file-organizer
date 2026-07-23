import pytest
from src.inbox.parser import parse_filename_syntax
from pydantic import ValidationError

def test_parse_filename_syntax_valid():
    cmd = parse_filename_syntax("SAF 1234 Ali 1 2026-01-01 My Title.pdf")
    assert cmd.area == "SAF"
    assert cmd.house == "1234"
    assert cmd.tenant_hint == "Ali"
    assert cmd.group == "1"
    assert cmd.date == "2026-01-01"
    assert cmd.title == "My Title"

def test_parse_filename_syntax_valid_no_title():
    cmd = parse_filename_syntax("SAF 1234 Ali 05 2026-01-01.pdf")
    assert cmd.area == "SAF"
    assert cmd.house == "1234"
    assert cmd.tenant_hint == "Ali"
    assert cmd.group == "5"
    assert cmd.date == "2026-01-01"
    assert cmd.title == ""

def test_parse_filename_syntax_invalid():
    with pytest.raises(ValueError, match="Invalid Format"):
        parse_filename_syntax("SAF 1234.pdf")

def test_parse_filename_syntax_group_validation():
    with pytest.raises(ValueError, match="Invalid Format"):
        parse_filename_syntax("SAF 1234 Ali 14 2026-01-01.pdf")
        
    cmd = parse_filename_syntax("SAF 1234 Ali g 2026-01-01.pdf")
    assert cmd.group == "G"
    
    cmd = parse_filename_syntax("SAF 1234 Ali U 2026-01-01.pdf")
    assert cmd.group == "U"
