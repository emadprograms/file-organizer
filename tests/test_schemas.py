import pytest
from src.schemas import PageClassification, Category

def test_page_classification_valid():
    """Test valid PageClassification creation."""
    data = {
        "house_number": "123",
        "residents": ["Ahmed Ali", "Fatima Ali (Wife)"],
        "category": Category.BASIC_DETAILS,
        "date": "2023-01-01",
        "summary": "A test summary"
    }
    pc = PageClassification(**data, summary="test")
    assert pc.house_number == "123"
    assert pc.residents == ["AHMED ALI", "FATIMA ALI (WIFE)"]
    assert pc.category == Category.BASIC_DETAILS

def test_resident_normalization():
    """Test that residents are stripped and uppercased."""
    # Case 1: List of strings
    pc1 = PageClassification(
        house_number="1",
        residents=["  ahmed  ", "fatima (wife)  "],
        category=Category.BASIC_DETAILS,
        date="NONE",
        summary="test"
    )
    assert pc1.residents == ["AHMED", "FATIMA (WIFE)"]

    # Case 2: Single string (should be converted to list)
    pc2 = PageClassification(
        house_number="2",
        residents="  john doe  ",
        category=Category.BASIC_DETAILS,
        date="NONE",
        summary="test"
    )
    assert pc2.residents == ["JOHN DOE"]

    # Case 3: NONE string
    pc3 = PageClassification(
        house_number="3",
        residents=["  none  "],
        category=Category.BASIC_DETAILS,
        date="NONE",
        summary="test"
    )
    assert pc3.residents == ["NONE"]

def test_invalid_category():
    """Test that an invalid category raises a ValidationError."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PageClassification(
            house_number="1",
            residents=["NONE"],
            category="Invalid Category",
            date="NONE",
            summary="test"
        )
