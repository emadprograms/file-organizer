"""Orchestration pipeline for processing and categorizing document pages.

This module acts as the core orchestrator. It manages the two-pass architecture:
1. Pass 1: Local OCR and LLM-based classification of individual pages.
2. Pass 1.5: Date outlier detection, global interpolation, and semantic name clustering.
3. Pass 2: Grouping pages logically into cohesive document segments based on category, tenant, and date timelines.
"""
from typing import Optional, Any
import logging
from concurrent.futures import ThreadPoolExecutor
from src.llm.llm import LLMClient, LLMFailureError
from src.core.schemas import DocumentGroup

logger = logging.getLogger(f"file_organizer.{__name__}")

from types import SimpleNamespace

class PageData(SimpleNamespace):
    def model_dump(self):
        return self.__dict__

class Pipeline:
    """Orchestrator for the document processing workflow."""
    
    def __init__(self, api_key: str, delay_between_pages: float = 1.0):
        """Initialize the pipeline with necessary clients and extractors.
        
        Args:
            api_key (str): The primary API key for the LLM.
            delay_between_pages (float): Delay in seconds between processing pages.
        """
        self.client = LLMClient(api_key, delay_between_pages)

    def _group_and_route_documents(self, raw_pages: list[tuple[int, PageData]], run_checkpoint_path: str | None = None) -> list[DocumentGroup]:
        """Group classified pages into cohesive document blocks using LLM boundary detection, then route them.
        
        Args:
            raw_pages (list[tuple[int, PageData]]): The sequence of classified pages.
            run_checkpoint_path (str | None): Optional path to save midway grouping progress.
            
        Returns:
            list[DocumentGroup]: The final grouped and routed documents.
        """
        from src.processing.grouping import process_with_shrink
        from src.processing.grouping.state import GroupingStateManager
        from src.processing.routing import route_document
        import json
        import os
        from src.fs_utils import atomic_write
        
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
        
        # Load Midway Checkpoint if it exists
        if run_checkpoint_path and os.path.exists(run_checkpoint_path):
            try:
                with open(run_checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
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
                except Exception as e:
                    pass
            
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
            
        # 3. Route each document
        # We only route documents that haven't been routed yet (just in case we ever checkpoint routing).
        # Currently, routing is fast enough to just re-run if it fails, but we'll apply it to all docs here.
        for doc in documents:
            if not hasattr(doc, 'folder_path') or not doc.folder_path:
                folder, is_direct = route_document(doc, self.client)
                doc.folder_path = folder
                doc.is_direct_routed = is_direct
            
        # Clean up run checkpoint since grouping and routing completed successfully
        if run_checkpoint_path and os.path.exists(run_checkpoint_path):
            try:
                os.remove(run_checkpoint_path)
            except Exception as e:
                logger.debug(f"Failed to remove run checkpoint: {e}")

        return documents
