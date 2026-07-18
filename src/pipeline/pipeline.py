"""Orchestration pipeline for processing and categorizing document pages.

This module acts as the core orchestrator. It manages the two-pass architecture:
1. Pass 1: Local OCR and LLM-based classification of individual pages.
2. Pass 1.5: Date outlier detection, global interpolation, and semantic name clustering.
3. Pass 2: Grouping pages logically into cohesive document segments based on category, tenant, and date timelines.
"""
import logging
import hashlib
from types import SimpleNamespace
from pathlib import Path

from src.llm.llm import LLMClient
from src.core.schemas import DocumentGroup

logger = logging.getLogger(f"file_organizer.{__name__}")

from typing import Any

class PageData(SimpleNamespace):
    """Simple namespace object for storing page data."""
    def model_dump(self) -> dict[str, Any]:
        """Dump the PageData attributes as a dictionary."""
        return self.__dict__

class Pipeline:
    """Orchestrator for the document processing workflow."""
    
    def __init__(self, api_key: str, delay_between_pages: float = 1.0, routing_model: str | None = None) -> None:
        """Initialize the pipeline with necessary clients and extractors.
        
        Args:
            api_key (str): The primary API key for the LLM.
            delay_between_pages (float): Delay in seconds between processing pages.
            routing_model (str | None): The model to use for document routing. Defaults to config.ROUTING_MODEL.
            
        Returns:
            None
        """
        from src.core.config import ROUTING_MODEL
        self.client = LLMClient(api_key, delay_between_pages)
        self.routing_model = routing_model or ROUTING_MODEL

    def _clean_documents(self, json_path: Path, target_dir: Path, house_id: str) -> tuple[list[Any], dict[str, Any] | None]:
        """Load tenant configuration and process document cleaning phase.
        
        Args:
            json_path (Path): Path to the input JSON file.
            target_dir (Path): The target directory to write configuration or load from.
            house_id (str): The identifier for the current house.
            
        Returns:
            tuple[list[Any], dict[str, Any] | None]: A tuple containing the cleaned pages and optional YAML config data.
        """
        from src.tenant_config.yaml_loader import load_tenant_config
        from src.timeline.phase import process_cleaning_phase
        
        yaml_data = load_tenant_config(target_dir, house_id)
        return process_cleaning_phase(json_path, self.client, yaml_data)

    def _group_documents(self, raw_pages: list[tuple[int, PageData]], run_checkpoint_path: str | None = None) -> list[DocumentGroup]:
        """Group classified pages into cohesive document blocks using LLM boundary detection.
        
        Args:
            raw_pages (list[tuple[int, PageData]]): The sequence of classified pages.
            run_checkpoint_path (str | None): Optional path to save midway grouping progress.
            
        Returns:
            list[DocumentGroup]: The grouped documents.
        """
        from src.grouping import process_with_shrink
        from src.grouping.state import GroupingStateManager
        import json
        import os
        from src.utils.fs import atomic_write
        
        if not raw_pages:
            return []
            
        pages_only = [p for _, p in raw_pages]
        
        # 1. Category and Resident Pre-split
        runs = []
        if pages_only:
            current_run = [pages_only[0]]
            current_category = getattr(pages_only[0], "category", None)
            current_resident = getattr(pages_only[0], "canonical_tenant", None)
            
            for page in pages_only[1:]:
                cat = getattr(page, "category", None)
                resident = getattr(page, "canonical_tenant", None)
                
                if cat == current_category and resident == current_resident:
                    current_run.append(page)
                else:
                    runs.append(current_run)
                    current_run = [page]
                    current_category = cat
                    current_resident = resident
            if current_run:
                runs.append(current_run)
        
        documents: list[DocumentGroup] = []
        processed_run_indices = set()
        
        if run_checkpoint_path and os.path.exists(run_checkpoint_path):
            try:
                with open(run_checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    if isinstance(checkpoint_data, list):
                        docs_data = checkpoint_data
                        processed_run_indices = set(range(len(runs)))
                    else:
                        processed_run_indices = set(checkpoint_data.get('processed_run_indices', []))
                        docs_data = checkpoint_data.get('documents', [])
                    documents = [DocumentGroup(**d) for d in docs_data]
                logger.info(f"Resuming from run checkpoint. Skipping {len(processed_run_indices)} already processed runs.")
            except Exception as e:
                logger.warning(f"Failed to load run checkpoint: {e}")
        
        # 2. Process each run with LLM overlapping chunks
        for i, run in enumerate(runs):
            if i in processed_run_indices:
                continue
                
            chunk_state_path = None
            state_manager = None
            if run_checkpoint_path:
                chunk_state_path = run_checkpoint_path.replace('.json', f'_chunk_{i}.json')
                state_manager = GroupingStateManager(chunk_state_path)
                
            groups = process_with_shrink(run, self.client, state_manager=state_manager)
            documents.extend(groups)
            processed_run_indices.add(i)
            
            # Clean up chunk state since this run completed successfully
            if chunk_state_path and os.path.exists(chunk_state_path):
                try:
                    os.remove(chunk_state_path)
                except Exception as e:
                    logger.debug(f"Failed to remove chunk state checkpoint: {e}")
            if chunk_state_path and os.path.exists(chunk_state_path + ".bak"):
                try:
                    os.remove(chunk_state_path + ".bak")
                except OSError as e:
                    logger.warning(f"Failed to remove backup: {e}")
            
            # Save Midway Checkpoint
            if run_checkpoint_path:
                try:
                    os.makedirs(os.path.dirname(run_checkpoint_path), exist_ok=True)
                    with atomic_write(run_checkpoint_path) as tmp_path:
                        with open(tmp_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                'processed_run_indices': list(processed_run_indices),
                                'documents': [doc.model_dump() for doc in documents]
                            }, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"Failed to save run checkpoint: {e}")
                    
        return documents

    def _route_documents(self, documents: list[DocumentGroup], run_checkpoint_path: str | None = None) -> list[DocumentGroup]:
        """Route documents to folder paths with state persistence and resumption.
        
        Args:
            documents (list[DocumentGroup]): The documents to route.
            run_checkpoint_path (str | None): Base path for routing state persistence.
            
        Returns:
            list[DocumentGroup]: The routed documents.
        """
        from src.routing import route_document
        from src.routing.state import RoutingStateManager, RoutingState
        import os
        
        if not documents:
            return []

        # Compute grouping checksum for sanity check
        hasher = hashlib.sha256()
        for doc in documents:
            hasher.update(f"{doc.start_page}:{doc.end_page}:{doc.category}".encode("utf-8"))
        current_checksum = hasher.hexdigest()

        routing_state_manager = None
        state = RoutingState()

        if run_checkpoint_path:
            routing_checkpoint_path = run_checkpoint_path.replace('.json', '_routing.json')
            routing_state_manager = RoutingStateManager(routing_checkpoint_path)
            state = routing_state_manager.load_state()
            
            # PRE-ROUTE SANITY CHECK (D-04)
            if state.grouping_checksum and state.grouping_checksum != current_checksum:
                if state.results:
                    logger.warning("Grouping has changed since last routing checkpoint and results exist. Resetting routing results to avoid incorrect assignments.")
                    state.results = {}
                else:
                    logger.warning("Grouping has changed since last routing checkpoint. Restarting routing.")
        
        state.grouping_checksum = current_checksum

        for i, doc in enumerate(documents):
            # Use state.results for resumption and restore folder path (Fixes Skip-and-Forget bug)
            if i in state.results:
                doc.folder_path = state.results[i]
                continue
                
            folder, is_direct = route_document(doc, self.client, model=self.routing_model)
            doc.folder_path = folder
            doc.is_direct_routed = is_direct
            
            state.results[i] = folder
            if routing_state_manager:
                routing_state_manager.save_state(state)
            
        # We no longer delete checkpoints here. main.py will move them to source_files/

        return documents


