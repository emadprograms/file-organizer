import json
from pathlib import Path
from typing import Any
import logging
from src.utils.fs import atomic_write

logger = logging.getLogger(f"file_organizer.{__name__}")

class State:
    def __init__(self, house_id: str, state_dir: Path):
        self.house_id = house_id
        self.state_dir = state_dir
        self.state_file = state_dir / f"{house_id}_state.json"
        
        self.data: dict[str, Any] = {
            "house_id": house_id,
            "cleaned_pages": None,
            "grouped_documents": None,
            "routed_documents": None,
            "manifest": None
        }
        self.load()

    def load(self) -> None:
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    self.data.update(content)
            except Exception as e:
                logger.error(f"Failed to load state from {self.state_file}: {e}")
                
    def save(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            with atomic_write(str(self.state_file)) as tmp_path:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state to {self.state_file}: {e}")
            raise
