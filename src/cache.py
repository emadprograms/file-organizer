"""Local caching mechanisms to persist LLM classifications and avoid redundant API calls.

This module provides a simple file-backed JSON cache for storing structured responses.
"""
import json
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

class SimpleCache:
    """A thread-safe, simple JSON-backed cache.
    
    Handles loading and atomic saving of key-value pairs to disk.
    """
    def __init__(self, filename: str):
        """Initialize the cache.
        
        Args:
            filename (str): The path to the JSON cache file.
        """
        self.filename = filename
        self.data: dict[str, Any] = {}
        self.load()

    def load(self):
        """Load the cache data from the JSON file if it exists."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache {self.filename}: {e}")
                self.data = {}

    def set(self, key: str, value: Any):
        """Store a value in the cache and persist to disk.
        
        Args:
            key (str): The cache key.
            value (Any): The JSON-serializable value to store.
        """
        self.data[key] = value
        temp_file = f"{self.filename}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, self.filename)
        except Exception as e:
            logger.error(f"Error saving cache {self.filename}: {e}")

    def get(self, key: str) -> Any:
        """Retrieve a value from the cache.
        
        Args:
            key (str): The cache key.
            
        Returns:
            Any: The cached value, or None if the key is not found.
        """
        return self.data.get(key)

    def __getitem__(self, key: str):
        return self.data[key]

    def __contains__(self, key: str):
        return key in self.data

    def values(self):
        return self.data.values()
