from __future__ import annotations
import os
import json
import shutil
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(f"file_organizer.{__name__}")

class RoutingState(BaseModel):
    """
    Represents the state of the routing process to allow resuming after interruption.
    Stores the actual routing results (index -> folder path) and the grouping checksum
    active when these results were computed.
    """
    results: dict[int, str] = Field(default_factory=dict, description="Mapping of document index to assigned folder path.")
    grouping_checksum: str | None = Field(default=None, description="Checksum of the grouping results to ensure they haven't changed since routing started.")

class RoutingStateManager:
    """
    Handles atomic persistence of RoutingState to disk.
    """
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.bak_file = f"{state_file}.bak"
        self.tmp_file = f"{state_file}.tmp"

    def save_state(self, state: RoutingState) -> None:
        """
        Saves the state atomically using a temporary file and os.replace.
        Maintains a backup of the last known good state.
        """
        try:
            # 1. Write to temporary file
            with open(self.tmp_file, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))

            # 2. Create backup of current state before replacing it
            if os.path.exists(self.state_file):
                shutil.copy2(self.state_file, self.bak_file)

            # 3. Atomic swap
            os.replace(self.tmp_file, self.state_file)
            logger.debug(f"Routing state saved atomically to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save routing state: {e}")
            if os.path.exists(self.tmp_file):
                os.remove(self.tmp_file)
            raise

    def load_state(self) -> RoutingState:
        """
        Loads the state from disk. Fallback to .bak if the main state file is corrupted or missing.
        Returns a default RoutingState if no state files exist.
        """
        for file_path in [self.state_file, self.bak_file]:
            if not os.path.exists(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Validate with Pydantic
                return RoutingState.model_validate(data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"State file {file_path} is corrupted: {e}. Trying next fallback...")
                continue

        return RoutingState()
