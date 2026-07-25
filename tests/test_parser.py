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

def test_parse_omitted_trailing():
    # House only
    cmd = parse_filename_syntax("SAF 507.pdf")
    assert cmd.area == "SAF"
    assert cmd.house == "507"
    assert cmd.tenant_hint == "U"
    assert cmd.group == "U"
    assert cmd.date == "U"
    assert cmd.title == ""
    
    # House and Tenant
    cmd = parse_filename_syntax("SAF 507 abdul rehman.pdf")
    assert cmd.area == "SAF"
    assert cmd.house == "507"
    assert cmd.tenant_hint == "abdul rehman"
    assert cmd.group == "U"
    assert cmd.date == "U"
    assert cmd.title == ""

def test_parse_filename_syntax_group_validation():
    # '14' is not a valid group, so it gets lumped into tenant_hint and defaults apply
    cmd = parse_filename_syntax("SAF 1234 Ali 14 2026-01-01.pdf")
    assert cmd.tenant_hint == "Ali 14 2026-01-01"
    assert cmd.group == "U"
    assert cmd.date == "U"
    assert cmd.title == ""
        
    cmd = parse_filename_syntax("SAF 1234 Ali g 2026-01-01.pdf")
    assert cmd.group == "G"
    
    cmd = parse_filename_syntax("SAF 1234 Ali U 2026-01-01.pdf")
    assert cmd.group == "U"

def test_parse_filename_syntax_ambiguous_u():
    # When U is the tenant and there is another valid group token next to it
    cmd = parse_filename_syntax("SAFC 1273 U G 2026-06-25.pdf")
    assert cmd.tenant_hint == "U"
    assert cmd.group == "G"
    
    cmd = parse_filename_syntax("SAFC 1273 U 5 2026-06-25.pdf")
    assert cmd.tenant_hint == "U"
    assert cmd.group == "5"

    cmd = parse_filename_syntax("SAFC 1273 U U 2026-06-25.pdf")
    assert cmd.tenant_hint == "U"
    assert cmd.group == "U"

    # Testing the previous regression where lack of a valid date broke group parsing
    cmd = parse_filename_syntax("SAFC 1273 John Doe G title.pdf")
    assert cmd.tenant_hint == "John Doe"
    assert cmd.group == "G"
    assert cmd.date == "title"
