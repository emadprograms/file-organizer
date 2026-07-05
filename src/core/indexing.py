"""Indexing utilities for 0-based and 1-based alignment and bounds checking."""

def to_0_based(index: int) -> int:
    """Convert a 1-based index to 0-based. 
    If already 0-based (or less), returns 0.
    """
    return max(0, index - 1)

def to_1_based(index: int) -> int:
    """Convert a 0-based index to 1-based."""
    return max(1, index + 1)

def validate_bounds(index: int, max_len: int) -> int:
    """Validate that a 0-based index is within bounds [0, max_len - 1].
    
    Args:
        index: The 0-based index to check.
        max_len: The maximum length of the collection.
        
    Returns:
        The valid index.
        
    Raises:
        IndexError: If index is out of bounds.
    """
    if index < 0 or index >= max_len:
        raise IndexError(f"Index {index} out of bounds for length {max_len}")
    return index
