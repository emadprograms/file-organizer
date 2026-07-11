import logging
from .core import process_with_shrink

__all__ = ["process_with_shrink"]

logger = logging.getLogger(f"file_organizer.{__name__}")
