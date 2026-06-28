import pytest
from src.schemas import PageClassification, Category
from pydantic import ValidationError

def test_normalize_category():
    # Test valid exact matching
    pc1 = PageClassification(residents=["Mohamed"], category="Allocation Order", date="2020-01-01", summary="summary")
    assert pc1.category == Category.AMAR_TAKHSEES

    # Test lowercase with underscore (LLM style output)
    pc2 = PageClassification(residents=["Mohamed"], category="allocation_order", date="2020-01-01", summary="summary")
    assert pc2.category == Category.AMAR_TAKHSEES

    # Test lowercase with underscore for another category
    pc3 = PageClassification(residents=["Mohamed"], category="basic_details_form", date="2020-01-01", summary="summary")
    assert pc3.category == Category.BASIC_DETAILS

    # Test exact enum key matching
    pc4 = PageClassification(residents=["Mohamed"], category="AMAR_TAKHSEES", date="2020-01-01", summary="summary")
    assert pc4.category == Category.AMAR_TAKHSEES

    # Test invalid category
    with pytest.raises(ValidationError):
         PageClassification(residents=["Mohamed"], category="Invalid Category", date="2020-01-01", summary="summary")
