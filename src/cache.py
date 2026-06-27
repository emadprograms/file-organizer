"""
This file handles saving data so we don't have to ask the AI the same questions twice.
It saves the AI's answers in a simple file on your computer. If we run the program 
again, it will just read the saved file instead of waiting for the AI.
"""
import json
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

class SimpleCache:
    """A simple tool to save data to a JSON file safely."""
    def __init__(self, filename: str):
        self.filename = filename
        self.data: dict[str, Any] = {}
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache {self.filename}: {e}")
                self.data = {}

    def set(self, key: str, value: Any):
        self.data[key] = value
        temp_file = f"{self.filename}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, self.filename)
        except Exception as e:
            logger.error(f"Error saving cache {self.filename}: {e}")

    def get(self, key: str):
        return self.data.get(key)

    def __getitem__(self, key: str):
        return self.data[key]

    def __contains__(self, key: str):
        return key in self.data

    def values(self):
        return self.data.values()
