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
        
        if pages_to_process:
            print(f"Pass 1a: Extracting text for {len(pages_to_process)} pages...")
            extracted_pages = []
            for p_idx, i_bytes in pages_to_process:
                if len(i_bytes) < 15000:
                    print(f" Page {p_idx} is blank (size {len(i_bytes)} bytes). Skipping LLM.")
                    res = PageClassification(category=Category.OTHER_LETTERS, residents=["NONE"], date="NONE", house_number="UNKNOWN")
                    with cache_lock:
                        cached_pages[str(p_idx)] = res.model_dump()
                        temp_cache_file = f"{cache_file}.tmp"
                        with open(temp_cache_file, "w", encoding="utf-8") as f:
                            json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                        os.replace(temp_cache_file, cache_file)
                    raw_pages.append((p_idx, res))
                    continue
                    
                extracted_footer = None
                try:
                    import Vision, Quartz, re
                    from Foundation import NSData
                    ns_data = NSData.dataWithBytes_length_(i_bytes, len(i_bytes))
                    cg_data_provider = Quartz.CGDataProviderCreateWithCFData(ns_data)
                    cg_image = Quartz.CGImageCreateWithPNGDataProvider(cg_data_provider, None, False, Quartz.kCGRenderingIntentDefault)
                    if cg_image:
                        request_handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
                        request = Vision.VNRecognizeTextRequest.alloc().init()
                        request.setRecognitionLanguages_(["ar", "en"])
                        request.setRegionOfInterest_(Vision.CGRectMake(0.0, 0.0, 1.0, 0.1))
                        success, error = request_handler.performRequests_error_([request], None)
                        if success:
                            full_text = " ".join([obs.topCandidates_(1)[0].string() for obs in request.results() if obs.topCandidates_(1)])
                            match = re.search(r'(\d+)\s*من\s*(\d+)', full_text)
                            if not match: match = re.search(r'(\d+)\s+(\d+)\s*من', full_text)
                            if not match: match = re.search(r'(\d+)\s*من', full_text)
                            if match: extracted_footer = match.group(0)
                            else:
                                match = re.search(r'(الصفحة|صفحة|page)[\s:]*(\d+)', full_text, re.IGNORECASE)
                                if match: extracted_footer = match.group(0)
                except Exception as e:
                    print(f"Vision OCR Error on page {p_idx}: {e}")
                    
                try:
                    text = self.client.extract_page(i_bytes)
                    extracted_pages.append((p_idx, text, extracted_footer))
                except Exception as e:
                    print(f"WARNING: Extraction fallback on page {p_idx} after retries: {e}")
                    house_number = "UNKNOWN"
                    with cache_lock:
                        for v in cached_pages.values():
                            if v.get("house_number") and v.get("house_number") != "UNKNOWN":
                                house_number = v.get("house_number")
                                break
                    fallback_res = PageClassification(category=Category.OTHER_LETTERS, residents=["UNKNOWN"], date="NONE", house_number=house_number)
                    with cache_lock:
                        cached_pages[str(p_idx)] = fallback_res.model_dump()
                        temp_cache_file = f"{cache_file}.tmp"
                        with open(temp_cache_file, "w", encoding="utf-8") as f:
                            json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                        os.replace(temp_cache_file, cache_file)
                    raw_pages.append((p_idx, fallback_res))
            
            print(f"Pass 1b: Classifying text for {len(extracted_pages)} pages...")
            for p_idx, text, extracted_footer in extracted_pages:
                try:
                    res = self.client.classify_extracted_page(text, extracted_footer)
                    if extracted_footer:
                        import re
                        page_match = re.search(r'(\d+)\s*من', extracted_footer)
                        if not page_match:
                            page_match = re.search(r'(?:الصفحة|صفحة|page)[\s:]*(\d+)', extracted_footer, re.IGNORECASE)
                        if page_match:
                            try:
                                extracted_page_num = int(page_match.group(1))
                                if extracted_page_num > 1:
                                    res.is_continuation = True
                                    print(f" [Heuristic] Footer '{extracted_footer}' implies page {extracted_page_num}. Forcing is_continuation=True.")
                            except ValueError:
                                pass
                    msg = f" Extracted Page {p_idx}: {res.category.value} | {res.residents} | {res.date}"
                    try: print(msg)
                    except UnicodeEncodeError: print(msg.encode('utf-8', errors='replace').decode('utf-8'))
                    with cache_lock:
                        cached_pages[str(p_idx)] = res.model_dump()
                        temp_cache_file = f"{cache_file}.tmp"
                        with open(temp_cache_file, "w", encoding="utf-8") as f:
                            json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                        os.replace(temp_cache_file, cache_file)
                    raw_pages.append((p_idx, res))
                except Exception as e:
                    print(f"WARNING: Classification fallback on page {p_idx} after retries: {e}")
                    house_number = "UNKNOWN"
                    with cache_lock:
                        for v in cached_pages.values():
                            if v.get("house_number") and v.get("house_number") != "UNKNOWN":
                                house_number = v.get("house_number")
                                break
                    fallback_res = PageClassification(category=Category.OTHER_LETTERS, residents=["UNKNOWN"], date="NONE", house_number=house_number)
                    with cache_lock:
                        cached_pages[str(p_idx)] = fallback_res.model_dump()
                        temp_cache_file = f"{cache_file}.tmp"
                        with open(temp_cache_file, "w", encoding="utf-8") as f:
                            json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                        os.replace(temp_cache_file, cache_file)
                    raw_pages.append((p_idx, fallback_res))

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

        for i, (page_index, page) in enumerate(raw_pages):
            effective_continuation = getattr(page, 'is_continuation', False)

            mapped_residents = [canonical_mapping_clean.get(r.upper().strip(), r) for r in page.residents]
            valid_mapped = [r for r in mapped_residents if r not in ("NONE", "UNKNOWN", "")]

            group_list_temp = prefix_buffer if current_primary_tenant == "UNKNOWN" else documents
            
            if effective_continuation and group_list_temp:
                page_primary_tenant = group_list_temp[-1].primary_tenant
                page.category = group_list_temp[-1].category
            else:
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
                if effective_continuation:
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
