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

    def _group_and_route_documents(self, raw_pages: list[tuple[int, PageData]]) -> list[DocumentGroup]:
        """Group classified pages into cohesive document blocks using LLM boundary detection, then route them.
        
        Args:
            raw_pages (list[tuple[int, PageData]]): The sequence of classified pages.
            
        Returns:
            list[DocumentGroup]: The final grouped and routed documents.
        """
        from src.processing.grouping import process_with_shrink
        from src.processing.routing import route_document
        
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
        
        # 2. Process each run with LLM overlapping chunks
        for run in runs:
            groups = process_with_shrink(run, self.client)
            documents.extend(groups)
            
        # 3. Route each document
        for doc in documents:
            folder, is_direct = route_document(doc, self.client)
            doc.folder_path = folder
            doc.is_direct_routed = is_direct
            
        return documents
