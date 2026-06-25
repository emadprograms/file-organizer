from typing import List
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.ingest import PdfIngestor
from src.llm import GemmaClient, LLMFailureError, InvalidResponseError
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
                # Pre-check for completely blank pages using file size threshold (15KB for 150 DPI)
                if len(i_bytes) < 15000:
                    print(f" Page {p_idx} is blank (size {len(i_bytes)} bytes). Skipping LLM.")
                    res = PageClassification(
                        category=Category.OTHER_LETTERS,
                        residents=["NONE"],
                        date="NONE",
                        house_number="UNKNOWN"
                    )
                    with cache_lock:
                        cached_pages[str(p_idx)] = res.model_dump()
                        temp_cache_file = f"{cache_file}.tmp"
                        with open(temp_cache_file, "w", encoding="utf-8") as f:
                            json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                        os.replace(temp_cache_file, cache_file)
                    return (p_idx, res)

                res = None
                for attempt in range(3):
                    try:
                        res = self.client.classify_page(image_bytes=i_bytes)
                        break
                    except (LLMFailureError, InvalidResponseError) as e:
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                        else:
                            print(f"WARNING: Extraction fallback on page {p_idx} after 3 retries: {e}")
                            house_number = "UNKNOWN"
                            with cache_lock:
                                for v in cached_pages.values():
                                    if v.get("house_number") and v.get("house_number") != "UNKNOWN":
                                        house_number = v.get("house_number")
                                        break
                            fallback_res = PageClassification(
                                category=Category.OTHER_LETTERS,
                                residents=["UNKNOWN"],
                                date="NONE",
                                house_number=house_number
                            )
                            with cache_lock:
                                cached_pages[str(p_idx)] = fallback_res.model_dump()
                                temp_cache_file = f"{cache_file}.tmp"
                                with open(temp_cache_file, "w", encoding="utf-8") as f:
                                    json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                                os.replace(temp_cache_file, cache_file)
                            return (p_idx, fallback_res)

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
        
        documents = self._group_pages_into_documents(raw_pages, canonical_mapping_clean)
        
        print(f"Identified {len(documents)} document groups based on timeline logic.")
        return documents

    def _group_pages_into_documents(self, raw_pages: list[tuple[int, PageClassification]], canonical_mapping_clean: dict[str, str]) -> list[DocumentGroup]:
        documents: list[DocumentGroup] = []
        current_primary_tenant = "UNKNOWN"
        prefix_buffer: list[DocumentGroup] = []
        verified_residents = set()

        ANCHOR_CATEGORIES = {Category.BASIC_DETAILS, Category.KEY_HANDOVER, Category.CONTRACT}

        for _, page in raw_pages:
            if page.category in ANCHOR_CATEGORIES:
                mapped = [canonical_mapping_clean.get(r.upper().strip(), r) for r in page.residents]
                for m in mapped:
                    if m not in ("NONE", "UNKNOWN", ""):
                        verified_residents.add(m)

        for page_index, page in raw_pages:
            mapped_residents = [canonical_mapping_clean.get(r.upper().strip(), r) for r in page.residents]
            valid_mapped = [r for r in mapped_residents if r not in ("NONE", "UNKNOWN", "")]

            if page.category == Category.AMAR_TAKHSEES:
                if valid_mapped:
                    candidate = valid_mapped[0]
                    words_current = set(current_primary_tenant.split())
                    words_candidate = set(candidate.split())
                    if len(words_current.intersection(words_candidate)) >= min(2, len(words_current), len(words_candidate)):
                        page_primary_tenant = current_primary_tenant
                    elif self.client.check_name_match(current_primary_tenant, candidate, page.category.value):
                        page_primary_tenant = current_primary_tenant
                    else:
                        page_primary_tenant = candidate
                else:
                    page_primary_tenant = current_primary_tenant
            elif page.category == Category.PERSONAL_DETAILS:
                page_primary_tenant = current_primary_tenant
            elif valid_mapped:
                if current_primary_tenant in valid_mapped:
                    page_primary_tenant = current_primary_tenant
                else:
                    if page.category in ANCHOR_CATEGORIES and len(valid_mapped) <= 10:
                        matched = False
                        for candidate in valid_mapped:
                            words_current = set(current_primary_tenant.split())
                            words_candidate = set(candidate.split())
                            if len(words_current.intersection(words_candidate)) >= min(2, len(words_current), len(words_candidate)):
                                matched = True
                                break
                            elif self.client.check_name_match(current_primary_tenant, candidate, page.category.value):
                                matched = True
                                break
                        if matched:
                            page_primary_tenant = current_primary_tenant
                        else:
                            current_primary_tenant = valid_mapped[0]
                            page_primary_tenant = current_primary_tenant
                            
                            if prefix_buffer:
                                for doc in prefix_buffer:
                                    doc.primary_tenant = current_primary_tenant
                                documents.extend(prefix_buffer)
                                prefix_buffer.clear()
                    else:
                        candidate = valid_mapped[0]
                        words_current = set(current_primary_tenant.split())
                        words_candidate = set(candidate.split())
                        if len(words_current.intersection(words_candidate)) >= min(2, len(words_current), len(words_candidate)):
                            page_primary_tenant = current_primary_tenant
                        elif self.client.check_name_match(current_primary_tenant, candidate, page.category.value):
                            page_primary_tenant = current_primary_tenant
                        else:
                            if candidate in verified_residents:
                                page_primary_tenant = candidate
                            else:
                                page_primary_tenant = current_primary_tenant
            else:
                page_primary_tenant = current_primary_tenant

            group_list = prefix_buffer if current_primary_tenant == "UNKNOWN" else documents

            merge_condition = False
            if group_list and group_list[-1].category == page.category and group_list[-1].primary_tenant == page_primary_tenant:
                if getattr(page, 'is_continuation', False):
                    merge_condition = True
                elif page.date != "NONE" and group_list[-1].dates and group_list[-1].dates[-1] == page.date:
                    merge_condition = True

            if merge_condition:
                group_list[-1].end_page = page_index
                if page.date != "NONE":
                    group_list[-1].dates.append(page.date)
            else:
                group_list.append(DocumentGroup(
                    start_page=page_index,
                    end_page=page_index,
                    house_number=page.house_number,
                    primary_tenant=page_primary_tenant,
                    category=page.category,
                    dates=[page.date] if page.date != "NONE" else []
                ))

        if current_primary_tenant == "UNKNOWN" and prefix_buffer:
            documents = prefix_buffer + documents

        return documents
