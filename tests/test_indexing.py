import pytest
import logging
from src.core.indexing import to_0_based, validate_bounds

logger = logging.getLogger(f"file_organizer.{__name__}")

def test_to_0_based():
    assert to_0_based(1) == 0
    assert to_0_based(2) == 1
    assert to_0_based(0) == 0  # safe fallback
    assert to_0_based(-5) == 0 # safe fallback


def test_validate_bounds_normal():
    assert validate_bounds(0, 10) == 0
    assert validate_bounds(9, 10) == 9

def test_validate_bounds_out_of_bounds():
    with pytest.raises(IndexError):
        validate_bounds(-1, 10)
    with pytest.raises(IndexError):
        validate_bounds(10, 10)
    with pytest.raises(IndexError):
        validate_bounds(15, 10)
        
def test_validate_bounds_edge_cases():
    with pytest.raises(IndexError):
        validate_bounds(0, 0)
