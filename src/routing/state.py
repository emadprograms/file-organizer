from __future__ import annotations
import os
import json
import shutil
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(f"file_organizer.{__name__}")

class RoutingState(BaseModel):
    """Represents the state of the routing process to allow resuming after interruption.
    
    Stores the actual routing results (index -> folder path) and the grouping checksum
    active when these results were computed.

    Attributes:
        results (dict[int, str]): Mapping of document index to assigned folder path.
        grouping_checksum (str | None): Checksum of the grouping results to ensure they haven't changed since routing started.
    """
    results: dict[int, str] = Field(default_factory=dict, description="Mapping of document index to assigned folder path.")
    grouping_checksum: str | None = Field(default=None, description="Checksum of the grouping results to ensure they haven't changed since routing started.")

class RoutingStateManager:
    """Handles atomic persistence of RoutingState to disk.
    
    Attributes:
        state_file (str): The main state file path.
        bak_file (str): The backup state file path.
        tmp_file (str): The temporary state file path.
    """
    def __init__(self, state_file: str) -> None:
        """Initialize the RoutingStateManager.
        
        Args:
            state_file (str): The path to the JSON state file.
        """
        self.state_file = state_file
        self.bak_file = f"{state_file}.bak"
        import tempfile
        import uuid
        import os
        self.tmp_file = os.path.join(tempfile.gettempdir(), f"routing_state_{uuid.uuid4().hex}.tmp")

    def save_state(self, state: RoutingState) -> None:
        """Saves the routing state atomically using a temporary file and shutil.move.
        
        Maintains a backup of the last known good state.

        Args:
            state (RoutingState): The current routing state to persist.
            
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
            logger.debug(f"Routing state saved atomically to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save routing state: {e}")
            if os.path.exists(self.tmp_file):
                os.remove(self.tmp_file)
            raise

    def load_state(self) -> RoutingState:
        """Loads the routing state from disk.
        
        Fallbacks to .bak if the main state file is corrupted or missing.
        Returns a default RoutingState if no state files exist.

        Returns:
            RoutingState: The loaded or newly initialized routing state.
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

