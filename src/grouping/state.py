from __future__ import annotations
import os
import json
import shutil
import logging
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger(f"file_organizer.{__name__}")

class GroupingState(BaseModel):
    """
    Represents the state of the grouping process to allow resuming after interruption.
    """
    current_page_index: int = Field(default=0, description="The index of the first page in the current processing chunk.")
    chunk_size_index: int = Field(default=0, description="The index of the current chunk size being used from the available sizes list.")
    current_chunk_failure_count: int = Field(default=0, description="Number of consecutive failures at the current chunk size.")
    failure_count: int = Field(default=0, description="Total number of processing failures encountered so far.")
    processed_groups: list[dict[str, Any]] = Field(default_factory=list, description="List of groups already finalized and committed to the result set.")

class GroupingStateManager:
    """Handles atomic persistence of GroupingState to disk.
    
    Attributes:
        state_file (str): The main state file path.
        bak_file (str): The backup state file path.
        tmp_file (str): The temporary state file path.
    """
    def __init__(self, state_file: str) -> None:
        """Initialize the GroupingStateManager.
        
        Args:
            state_file (str): The path to the JSON state file.
        """
        self.state_file = state_file
        self.bak_file = f"{state_file}.bak"
        import tempfile
        import uuid
        import os
        self.tmp_file = os.path.join(tempfile.gettempdir(), f"grouping_state_{uuid.uuid4().hex}.tmp")

    def save_state(self, state: GroupingState) -> None:
        """Saves the state atomically using a temporary file and shutil.move.
        
        Maintains a backup of the last known good state.

        Args:
            state (GroupingState): The current grouping state to persist.
            
        Raises:
            Exception: If an error occurs during file writing or replacement.
        """
        try:
            # 1. Write to temporary file
            with open(self.tmp_file, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))

            # 2. Create backup of current state before replacing it
            if os.path.exists(self.state_file):
                shutil.copy2(self.state_file, self.bak_file)

            # 3. Atomic swap
            shutil.move(self.tmp_file, self.state_file)
            logger.debug(f"Grouping state saved atomically to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save grouping state: {e}")
            if os.path.exists(self.tmp_file):
                os.remove(self.tmp_file)
            raise

    def load_state(self) -> GroupingState:
        """Loads the state from disk.
        
        Fallbacks to .bak if the main state file is corrupted or missing.
        Returns a default GroupingState if no state files exist.

        Returns:
            GroupingState: The loaded or newly initialized grouping state.
        """
        for file_path in [self.state_file, self.bak_file]:
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Validate with Pydantic
                return GroupingState.model_validate(data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"State file {file_path} is corrupted: {e}. Trying next fallback...")
                continue
        
        logger.info("No valid grouping state found. Starting from scratch.")
        return GroupingState()

