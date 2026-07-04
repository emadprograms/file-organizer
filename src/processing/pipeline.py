"""Orchestration pipeline for processing and categorizing document pages.

This module acts as the core orchestrator. It manages the two-pass architecture:
1. Pass 1: Local OCR and LLM-based classification of individual pages.
2. Pass 1.5: Date outlier detection, global interpolation, and semantic name clustering.
3. Pass 2: Grouping pages logically into cohesive document segments based on category, tenant, and date timelines.
"""
from typing import Optional, Any
import os
import threading
import sys
import yaml
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.processing.ingest import PdfIngestor
from src.llm.llm import LLMClient, LLMFailureError, InvalidResponseError
from src.core.schemas import DocumentGroup

logger = logging.getLogger(__name__)

from src.core.cache import SimpleCache
from src.processing.extractors import VisionExtractor, CloudExtractor
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
        self.ingestor = PdfIngestor()
        self.client = LLMClient(api_key, delay_between_pages)

    def process_pdf(self, pdf_path: str, config_path: str = "sample-config.yaml") -> list[DocumentGroup]:
        """Process a PDF through the multi-pass categorization pipeline.
        
        Two-pass architecture:
        Pass 1: Vision extraction (category, resident, date) per page.
        Pass 1.5: Date interpolation and alias mapping for missing or noisy data.
        Pass 2: Python timeline logic to group consecutive pages by Category + Primary Tenant.
        
        Args:
            pdf_path (str): The file path to the source PDF.
            
        Returns:
            list[DocumentGroup]: A list of grouped documents representing logical segments.
            
        Raises:
            ValueError: If the PDF cannot be read or contains 0 pages.
            RuntimeError: If page loss is detected during processing.
        """
        logger.info(f"Starting Pass 1 (Vision Extraction) for {pdf_path}...")
        
        from src.core.schemas import UserConfig
        config_file = os.getenv("CONFIG_PATH", config_path)
        with open(config_file, "r", encoding="utf-8") as f:
            config = UserConfig(**yaml.safe_load(f))

        # Initialize Caches
        pages_cache = SimpleCache(f"{pdf_path}.cache.json")
        
        logger.info(f"Loaded {len(pages_cache.data)} pages from cache.")

        raw_pages = []
        pages_to_process = []
        
        for page_index, image_bytes in self.ingestor.extract_pages_as_images(pdf_path):
            str_index = str(page_index)
            if str_index in pages_cache:
                cache_data = pages_cache[str_index]
                if 'resident' in cache_data and 'residents' not in cache_data:
                    cache_data['residents'] = [cache_data.pop('resident')]
                if cache_data.get('category') == 'pictures':
                    cache_data['category'] = 'inspection_pictures'
                try:
                    result = PageData(**cache_data)
                    msg = f" Cached Page {page_index}: {result.category} | {result.residents} | {result.date} | Sum: {str(result.summary)}"
                    logger.info(msg)
                    raw_pages.append((page_index, result))
                except Exception as e:
                    logger.warning(f"Failed to load page {page_index} from cache due to validation error: {e}. Re-processing...")
                    pages_to_process.append((page_index, image_bytes))
            else:
                pages_to_process.append((page_index, image_bytes))
                
        total_expected_pages = len(raw_pages) + len(pages_to_process)
        if total_expected_pages == 0:
            raise ValueError(f"The file {pdf_path} could not be read or contains 0 extractable pages.")
                
        if pages_to_process:
            vision_extractor = VisionExtractor(pages_cache)
            cloud_extractor = CloudExtractor(pages_cache, self.client)
            
            for p_idx, i_bytes in pages_to_process:
                extracted_footer = vision_extractor.extract_footer(p_idx, i_bytes)
                res_dynamic = cloud_extractor.extract(p_idx, i_bytes, extracted_footer, config.extraction.prompt_template, config.extraction.fields)
                
                # Backwards compatibility for Pass 1.5
                res_dict = res_dynamic.model_dump()
                res = PageData(**res_dict)
                
                raw_pages.append((p_idx, res))
            
            raw_pages.sort(key=lambda x: x[0])
    
        if len(raw_pages) != total_expected_pages:
            raise RuntimeError(f"CRITICAL: Expected {total_expected_pages} pages, but only recovered {len(raw_pages)}. Aborting Pass 1.5 to prevent data loss.")

        logger.info(f"--- Starting Pass 1.5 Audit for {pdf_path} ---")
        self._run_cleaning_pass(raw_pages, config)
        logger.info(f"--- Pass 1.5 Completed for {pdf_path} ---")
        
        logger.info(f"\n--- Final Page State After Pass 1.5 for {pdf_path} ---")
        for p_idx, page in raw_pages:
            resolved_names = [r for r in page.residents if r not in ("NONE", "UNKNOWN", "")]
            names_str = ", ".join(resolved_names) if resolved_names else "NONE"
            logger.info(f"Page {p_idx} | Date: {page.date} | Category: {page.category} | Names: {names_str}")
        logger.info("-" * 50 + "\n")

        logger.info(f"Starting Pass 2 (Grouping & Routing) for {pdf_path}...")
        
        documents = self._group_and_route_documents(raw_pages, config)
        
        logger.info(f"Identified {len(documents)} document groups after boundary detection and routing.")
        return documents

    def _run_cleaning_pass(self, raw_pages: list[tuple[int, PageData]], config: 'UserConfig') -> dict[str, str]:
        """Dynamically run the cleaning pass based on user configuration.
        
        Args:
            raw_pages: The sequence of classified pages.
            config: User configuration containing cleaning strategy.
            
        Returns:
            dict[str, str]: Canonical mapping (empty by default for new architecture).
        """
        cleaning_cfg = config.cleaning
        if cleaning_cfg.strategy == "python":
            if not cleaning_cfg.script_path:
                raise ValueError("Python strategy requires a script_path in config.")
            
            from pathlib import Path
            script_path = Path(cleaning_cfg.script_path).resolve()
            if not script_path.is_relative_to(Path.cwd()):
                raise PermissionError(f"Script path {script_path} is outside the allowed directory.")

            import importlib.util
            spec = importlib.util.spec_from_file_location("cleaning_script", str(script_path))
            if spec and spec.loader:
                cleaning_script = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cleaning_script)
                if hasattr(cleaning_script, "clean_pages"):
                    return cleaning_script.clean_pages(raw_pages)
                else:
                    raise ValueError("Python cleaning script must define a 'clean_pages(raw_pages)' function.")
            else:
                raise ValueError(f"Could not load python script: {cleaning_cfg.script_path}")
        elif cleaning_cfg.strategy == "llm":
            if not cleaning_cfg.prompt_template:
                raise ValueError("LLM strategy requires a prompt_template in config.")
            
            # Send raw_pages to LLM
            pages_data = [{"page_index": idx, "data": p.model_dump()} for idx, p in raw_pages]
            import json
            user_prompt = f"Pages data:\n{json.dumps(pages_data, ensure_ascii=False, indent=2)}\n\nPlease return the cleaned pages in the same format."
            
            from pydantic import BaseModel
            class CleanedPage(BaseModel):
                page_index: int
                residents: list[str]
                category: str
                date: str
                summary: str
                
            class CleanedPagesResult(BaseModel):
                pages: list[CleanedPage]
                
            from src.core.config import GEMINI_MODEL
            result = self.client._route_llm_call(
                model=GEMINI_MODEL,
                contents=[cleaning_cfg.prompt_template, user_prompt],
                response_schema=CleanedPagesResult,
                log_prefix="CleaningPass"
            )
            
            # Update raw_pages in-place
            cleaned_map = {p.page_index: p for p in result.pages}
            for idx, p in raw_pages:
                if idx in cleaned_map:
                    cp = cleaned_map[idx]
                    p.residents = cp.residents
                    p.category = cp.category
                    p.date = cp.date
                    p.summary = cp.summary
            return {}
        elif cleaning_cfg.strategy == "hybrid":
            logger.info("Running hybrid (Python + LLM) timeline logic...")
            self._interpolate_dates(raw_pages, config)
            return self._map_aliases(raw_pages, config)
        else:
            raise ValueError(f"Unknown cleaning strategy: {cleaning_cfg.strategy}")

    def _interpolate_dates(self, raw_pages: list[tuple[int, PageData]], config: 'UserConfig'):
        """Interpolate missing dates and handle chronological outliers.
        
        Args:
            raw_pages (list[tuple[int, PageData]]): The list of classified pages.
            config (UserConfig): User configuration containing prompts.
        """
        from datetime import datetime

        # 1. LLM-Based Outlier Detection
        logger.info(f"  [Pass 1.5] Running LLM-based outlier detection for {len(raw_pages)} pages...")
        date_pairs = [(idx, page.date) for idx, page in raw_pages if page.date and page.date != "NONE"]
        
        if date_pairs:
            prompt = config.cleaning.prompts.get('date_outliers', '') if config.cleaning.prompts else ''
            outlier_indices = self.client.detect_date_outliers(date_pairs, prompt_template=prompt)
            
            for idx in outlier_indices:
                # Find the page object in our raw_pages list
                for p_idx, page in raw_pages:
                    if p_idx == idx:
                        old_date = page.date
                        page.date = "NONE"
                        logger.info(f"[Pass 1.5 Date] Page {idx}: {old_date} -> NONE (LLM detected as outlier)")
                        break

        # 2. Global Interpolation (Fill the holes)
        for i in range(len(raw_pages)):
            if raw_pages[i][1].date == "NONE":
                last_valid_date = None
                last_valid_idx = -1
                for j in range(i-1, -1, -1):
                    if raw_pages[j][1].date != "NONE":
                        last_valid_date = raw_pages[j][1].date
                        last_valid_idx = raw_pages[j][0]
                        break
                
                next_valid_date = None
                next_valid_idx = -1
                for j in range(i+1, len(raw_pages)):
                    if raw_pages[j][1].date != "NONE":
                        next_valid_date = raw_pages[j][1].date
                        next_valid_idx = raw_pages[j][0]
                        break
                        
                actual_page_idx = raw_pages[i][0]
                if last_valid_date and next_valid_date:
                    raw_pages[i][1].date = last_valid_date
                    logger.info(f"[Pass 1.5 Date] Page {actual_page_idx}: NONE -> {last_valid_date} (Interpolated from Page {last_valid_idx})")
                elif last_valid_date:
                    raw_pages[i][1].date = last_valid_date
                    logger.info(f"[Pass 1.5 Date] Page {actual_page_idx}: NONE -> {last_valid_date} (Interpolated from Page {last_valid_idx})")
                elif next_valid_date:
                    raw_pages[i][1].date = next_valid_date
                    logger.info(f"[Pass 1.5 Date] Page {actual_page_idx}: NONE -> {next_valid_date} (Interpolated from Page {next_valid_idx})")

    def _parse_date(self, d_str: str) -> Optional[Any]:
        """Parse a normalized date string into a datetime object.
        
        Args:
            d_str (str): The YYYY-MM-DD date string.
            
        Returns:
            Optional[Any]: A datetime object, or None if parsing fails.
        """
        if not d_str or d_str == "NONE":
            return None
        import re
        from datetime import datetime
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', d_str.strip())
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
        return None

    def _map_aliases(self, raw_pages: list[tuple[int, PageData]], config: 'UserConfig') -> dict[str, str]:
        """Map entity aliases and resolve primary tenants across the timeline.
        
        Args:
            raw_pages (list[tuple[int, PageData]]): The list of classified pages.
            config (UserConfig): User configuration containing prompts.
            
        Returns:
            dict[str, str]: A mapping of canonical names applied.
        """
        ANCHOR_CATEGORIES = {"Basic Details Form", "Housing Contract", "Rent Deduction Notice"}
        
        # 0. Semantic Name Clustering
        anchor_names = set()
        other_names = set()
        for _, page in raw_pages:
            for r in page.residents:
                clean_r = r.upper().strip()
                if clean_r and clean_r not in ("NONE", "UNKNOWN", ""):
                    if page.category in ANCHOR_CATEGORIES:
                        anchor_names.add(clean_r)
                    else:
                        other_names.add(clean_r)
                        
        logger.info(f"  [Pass 1.5] Clustering {len(other_names)} other names against {len(anchor_names)} anchor names using LLM...")
        if anchor_names and other_names:
            prompt = config.cleaning.prompts.get('entity_resolution', '') if config.cleaning.prompts else ''
            canonical_map = self.client.cluster_names(list(anchor_names), list(other_names), prompt_template=prompt)
            for p_idx, page in raw_pages:
                new_residents = []
                for r in page.residents:
                    clean_r = r.upper().strip()
                    if clean_r and clean_r not in ("NONE", "UNKNOWN", ""):
                        canonical = canonical_map.get(clean_r, clean_r)
                        if canonical not in new_residents:
                            new_residents.append(canonical)
                    else:
                        new_residents.append(r)
                if not new_residents:
                    new_residents = ["NONE"]
                page.residents = new_residents
        
        # 1. Collect Statistics
        name_page_appearances: dict[str, set[int]] = {}
        name_dates: dict[str, list[Any]] = {}
        names_in_anchors = set()
        
        for p_idx, page in raw_pages:
            mapped_residents = [r.upper().strip() for r in page.residents if r not in ("NONE", "UNKNOWN", "")]
            d_obj = self._parse_date(page.date)
            
            for r in mapped_residents:
                if r not in name_page_appearances:
                    name_page_appearances[r] = set()
                    name_dates[r] = []
                name_page_appearances[r].add(p_idx)
                if d_obj:
                    name_dates[r].append(d_obj)
                
                if page.category in ANCHOR_CATEGORIES:
                    names_in_anchors.add(r)

        # 2. Identify Primary Tenants (1 anchor + >= 5 pages)
        primary_tenants = []
        for r, pages in name_page_appearances.items():
            if r in names_in_anchors and len(pages) >= 5:
                primary_tenants.append(r)
                
        if not primary_tenants:
            return {}
            
        # 3. Construct Timelines
        primary_tenant_timelines = {}
        valid_pts = []
        
        pt_explicit_ranges = {}
        for pt in primary_tenants:
            dates = name_dates.get(pt, [])
            if dates:
                pt_explicit_ranges[pt] = (min(dates), max(dates))
                
        # Sort PTs by their first explicit date
        sorted_pts = sorted(pt_explicit_ranges.keys(), key=lambda k: pt_explicit_ranges[k][0])
        
        from datetime import timedelta, datetime
        for i, pt in enumerate(sorted_pts):
            start_date, end_date = pt_explicit_ranges[pt]
            # Backtrack start date slightly
            final_start = start_date - timedelta(days=180)
            
            # Stretch end date
            if i == len(sorted_pts) - 1:
                # Last / Current Resident stretches to infinity
                final_end = datetime.max
            else:
                # Older resident stretches until the next resident's start date
                next_pt = sorted_pts[i+1]
                next_start = pt_explicit_ranges[next_pt][0]
                final_end = next_start - timedelta(days=1)
                
            primary_tenant_timelines[pt] = (final_start, final_end)
            valid_pts.append(pt)
            
        logger.info(f"\n  [Pass 1.5] Calculated Timelines:")
        for pt in sorted_pts:
            start_str = primary_tenant_timelines[pt][0].strftime('%Y-%m-%d')
            end_str = primary_tenant_timelines[pt][1].strftime('%Y-%m-%d') if primary_tenant_timelines[pt][1] != datetime.max else "Present (الساكن الحالي)"
            logger.info(f"    - {pt}: {start_str} to {end_str}")
        
        # 4. Global Overwrite
        new_raw_pages = []
        for p_idx, page in raw_pages:
            mapped_residents = [r.upper().strip() for r in page.residents if r not in ("NONE", "UNKNOWN", "")]
            
            # Check if page natively contains a Primary Tenant
            native_pts = [pt for pt in mapped_residents if pt in primary_tenants]
            if native_pts:
                import copy
                for pt in native_pts:
                    page_copy = copy.deepcopy(page)
                    page_copy.residents = [pt]
                    new_raw_pages.append((p_idx, page_copy))
                    logger.info(f"[Pass 1.5 Name] Page {p_idx}: Native PT kept/duplicated -> {pt}")
                continue
                
            # No native Primary Tenant -> Use Timeline Overwrite
            d_obj = self._parse_date(page.date)
            if not d_obj:
                page.residents = ["NONE"]
                new_raw_pages.append((p_idx, page))
                logger.info(f"[Pass 1.5 Name] Page {p_idx}: Overwritten -> NONE (No valid date)")
                continue
                
            # Find overlapping PTs
            overlapping_pts = []
            for pt in valid_pts:
                start, end = primary_tenant_timelines[pt]
                if start <= d_obj <= end:
                    overlapping_pts.append(pt)
                    
            if len(overlapping_pts) == 1:
                chosen_pt = overlapping_pts[0]
                page.residents = [chosen_pt]
                new_raw_pages.append((p_idx, page))
                logger.info(f"[Pass 1.5 Name] Page {p_idx}: Timeline Overwrite -> {chosen_pt}")
            elif len(overlapping_pts) > 1:
                # Overlap! Previous tenant wins
                chosen_pt = overlapping_pts[0]
                page.residents = [chosen_pt]
                new_raw_pages.append((p_idx, page))
                logger.info(f"[Pass 1.5 Name] Page {p_idx}: Timeline Overlap Overwrite (Previous PT Wins) -> {chosen_pt}")
            else:
                # Orphaned
                page.residents = ["NONE"]
                new_raw_pages.append((p_idx, page))
                logger.info(f"[Pass 1.5 Name] Page {p_idx}: Overwritten -> NONE (Orphaned/Out of bounds)")
                
        # Since we modified the structure of raw_pages, we must clear and replace it
        raw_pages.clear()
        raw_pages.extend(new_raw_pages)
        return {}

    def _group_and_route_documents(self, raw_pages: list[tuple[int, PageData]], config: 'UserConfig') -> list[DocumentGroup]:
        """Group classified pages into cohesive document blocks using LLM boundary detection, then route them.
        
        Args:
            raw_pages (list[tuple[int, PageData]]): The sequence of classified pages.
            config (UserConfig): User configuration.
            
        Returns:
            list[DocumentGroup]: The final grouped and routed documents.
        """
        from src.processing.grouping import category_presplit, process_with_shrink
        from src.processing.routing import route_document
        
        if not raw_pages:
            return []
            
        pages_only = [p for _, p in raw_pages]
        
        # 1. Category Pre-split
        runs = category_presplit(pages_only)
        
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
