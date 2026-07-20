import os
import time
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(f"file_organizer.{__name__}")

class FSUIOrchestrator:
    def __init__(self, config: Any, llm_client: Any):
        self.config = config
        self.llm_client = llm_client
        self.file_sizes: dict[str, int] = {}

    def process_inbox(self) -> None:
        pass

    def propose(self, filepath: Path) -> None:
        pass

    def finalize(self, filepath: Path) -> None:
        pass
