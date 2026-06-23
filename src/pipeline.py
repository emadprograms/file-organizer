from typing import List
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.ingest import PdfIngestor
from src.llm import GemmaClient
from src.schemas import PageClassification, DocumentGroup, Category


import sys

if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class Pipeline:
    def __init__(self, api_keys: list[str] = None, delay_between_pages: float = 1.0, telemetry_queue=None):
        self.ingestor = PdfIngestor()
        self.client = GemmaClient(api_keys, delay_between_pages, telemetry_queue=telemetry_queue)



    def process_pdf(self, pdf_path: str) -> list[DocumentGroup]:
        """
        Two-pass architecture:
        Pass 1: Vision extraction (category, resident, date) per page.
        Pass 2: Python timeline logic to group consecutive pages by Category + Primary Tenant.
        """
        print(f"Starting Pass 1 (Vision Extraction) for {pdf_path}...")
        
        cache_file = f"{pdf_path}.cache.json"
        cached_pages = {}
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_pages = json.load(f)
                print(f"Loaded {len(cached_pages)} pages from cache.")

        raw_pages = []
        pages_to_process = []
        
        for page_index, image_bytes in self.ingestor.extract_pages_as_images(pdf_path):
            str_index = str(page_index)
            if str_index in cached_pages:
                cache_data = cached_pages[str_index]
                if 'resident' in cache_data and 'residents' not in cache_data:
                    cache_data['residents'] = [cache_data.pop('resident')]
                result = PageClassification(**cache_data)
                msg = f" Cached Page {page_index}: {result.category.value} | {result.residents} | {result.date}"
                try:
                    print(msg)
                except UnicodeEncodeError:
                    fallback = getattr(sys.stdout, 'encoding', 'utf-8') or 'utf-8'
                    print(msg.encode(fallback, errors='replace').decode(fallback))
                raw_pages.append((page_index, result))
            else:
                pages_to_process.append((page_index, image_bytes))
                
        total_expected_pages = len(raw_pages) + len(pages_to_process)
        if total_expected_pages == 0:
            raise ValueError(f"The file {pdf_path} could not be read or contains 0 extractable pages.")
                
        cache_lock = threading.Lock()
        
        def process_single_page(page_info):
            p_idx, i_bytes = page_info
            import time
            try:
                res = self.client.classify_page(image_bytes=i_bytes)
                if res is None:
                    return None
                msg = f" Extracted Page {p_idx}: {res.category.value} | {res.residents} | {res.date}"
                try:
                    print(msg)
                except UnicodeEncodeError:
                    fallback = getattr(sys.stdout, 'encoding', 'utf-8') or 'utf-8'
                    print(msg.encode(fallback, errors='replace').decode(fallback))
                with cache_lock:
                    cached_pages[str(p_idx)] = res.model_dump()
                    # Saving cache progressively can be slow, but it's safe. We do it inside lock.
                    temp_cache_file = f"{cache_file}.tmp"
                    with open(temp_cache_file, "w", encoding="utf-8") as f:
                        json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                    os.replace(temp_cache_file, cache_file)
                return (p_idx, res)
            except Exception as e:
                print(f"Critical failure on page {p_idx}: {e}")
                raise e
                
        if pages_to_process:
            num_workers = 1
            print(f"Processing {len(pages_to_process)} pages sequentially (15 RPM global cap)...")
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(process_single_page, p) for p in pages_to_process]
                for future in as_completed(futures):
                    try:
                        res = future.result()
                        if res:
                            raw_pages.append(res)
                    except Exception as e:
                        try:
                            executor.shutdown(wait=False, cancel_futures=True)
                        except TypeError:
                            executor.shutdown(wait=False)
                        raise RuntimeError(f"Processing aborted due to failure on a page: {e}")
                        
        raw_pages.sort(key=lambda x: x[0])
    
        if len(raw_pages) != total_expected_pages:
            raise RuntimeError(f"CRITICAL: Expected {total_expected_pages} pages, but only recovered {len(raw_pages)}. Aborting Pass 1.5 to prevent data loss.")

        print(f"Starting Pass 1.5 (Entity Resolution) for {pdf_path}...")
        log_lines = []
        for page_index, page in raw_pages:
            res_str = ", ".join(page.residents) if page.residents else "NONE"
            log_lines.append(f"Page {page_index}: {page.category.value} | {res_str} | {page.date}")
        raw_pages_log = "\n".join(log_lines)
        
        canonical_mapping = self.client.resolve_entities(raw_pages_log)
        if not canonical_mapping:
            canonical_mapping = {}
        canonical_mapping_clean = {k.upper().strip(): v for k, v in canonical_mapping.items()}

        print(f"Starting Pass 2 (Tenant Grouping) for {pdf_path}...")
        
        documents: list[DocumentGroup] = []
        current_primary_tenant = "UNKNOWN"

        for page_index, page in raw_pages:
            # 1. Determine the Primary Tenant for this page based on Timeline Rules
            mapped_residents = [canonical_mapping_clean.get(r.upper().strip(), r) for r in page.residents]
            valid_mapped = [r for r in mapped_residents if r not in ("NONE", "UNKNOWN", "")]

            ANCHOR_CATEGORIES = {Category.BASIC_DETAILS, Category.KEY_HANDOVER, Category.CONTRACT}

            if page.category == Category.AMAR_TAKHSEES:
                # Independent, does not change the house's current tenant timeline
                page_primary_tenant = valid_mapped[0] if valid_mapped else current_primary_tenant
            elif page.category == Category.PERSONAL_DETAILS:
                # Inherits the timeline's active tenant (e.g. wife inherits husband's folder)
                page_primary_tenant = current_primary_tenant
            elif valid_mapped:
                # Document has valid names — evaluate if timeline changes
                if current_primary_tenant in valid_mapped:
                    # The current tenant is among the recipients, so the timeline is unbroken
                    page_primary_tenant = current_primary_tenant
                else:
                    # Is this a definitive anchor document for a new tenant?
                    # Only change the timeline if it's an anchor and not a massive list of names
                    if page.category in ANCHOR_CATEGORIES and len(valid_mapped) <= 3:
                        candidate = valid_mapped[0]
                        # Check word overlap to prevent children from hijacking the timeline
                        words_current = set(current_primary_tenant.split())
                        words_candidate = set(candidate.split())
                        
                        # If they share at least 2 words, they are family. Don't split timeline.
                        if len(words_current.intersection(words_candidate)) < 2:
                            current_primary_tenant = candidate
                    page_primary_tenant = current_primary_tenant
            else:
                # Document has NO name (e.g. pictures, generic notifications)
                page_primary_tenant = current_primary_tenant

            # 2. Grouping Logic
            # Merge with previous group IF same Category AND same Primary Tenant
            if (documents and 
                documents[-1].category == page.category and 
                documents[-1].primary_tenant == page_primary_tenant):
                
                documents[-1].end_page = page_index
                if page.date != "NONE":
                    documents[-1].dates.append(page.date)
            else:
                # Start a new group
                documents.append(DocumentGroup(
                    start_page=page_index,
                    end_page=page_index,
                    house_number=page.house_number,
                    primary_tenant=page_primary_tenant,
                    category=page.category,
                    dates=[page.date] if page.date != "NONE" else []
                ))

        print(f"Identified {len(documents)} document groups based on timeline logic.")
        return documents
