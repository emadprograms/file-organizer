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
    def __init__(self, api_keys: list[str] = None, delay_between_pages: float = 1.0, telemetry_queue=None, use_local_llm: bool = True):
        self.ingestor = PdfIngestor()
        self.client = GemmaClient(api_keys, delay_between_pages, telemetry_queue=telemetry_queue, use_local_llm=use_local_llm)



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
                
        text_cache_file = f"{pdf_path}.extracted.cache.json"
        extracted_text_cache = {}
        if os.path.exists(text_cache_file):
            with open(text_cache_file, "r", encoding="utf-8") as f:
                extracted_text_cache = json.load(f)
                print(f"Loaded {len(extracted_text_cache)} extracted text pages from cache.")

        raw_pages = []
        pages_to_process = []
        
        for page_index, image_bytes in self.ingestor.extract_pages_as_images(pdf_path):
            str_index = str(page_index)
            if str_index in cached_pages:
                cache_data = cached_pages[str_index]
                if 'resident' in cache_data and 'residents' not in cache_data:
                    cache_data['residents'] = [cache_data.pop('resident')]
                if cache_data.get('category') == 'pictures':
                    cache_data['category'] = 'inspection_pictures'
                result = PageClassification(**cache_data)
                msg = f" Cached Page {page_index}: {result.category.value} | {result.residents} | {result.date} | Sum: {str(result.summary)}"
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
            deferred_local_pages = []
            
            # Phase 1: Loop through each page, checking cache first, then cloud direct, then local OCR fallback
            for p_idx, i_bytes in pages_to_process:
                # 1. Blank Page check
                if len(i_bytes) < 15000:
                    print(f" Page {p_idx} is blank (size {len(i_bytes)} bytes). Skipping LLM.")
                    res = PageClassification(category=Category.OTHER_LETTERS, residents=["NONE"], date="NONE", house_number="UNKNOWN", summary="Blank page.")
                    with cache_lock:
                        cached_pages[str(p_idx)] = res.model_dump()
                        temp_cache_file = f"{cache_file}.tmp"
                        with open(temp_cache_file, "w", encoding="utf-8") as f:
                            json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                        os.replace(temp_cache_file, cache_file)
                    raw_pages.append((p_idx, res))
                    continue

                # 2. Extract footer using Vision framework (macOS local utility)
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
                        request.setRegionOfInterest_(Vision.CGRectMake(0.0, 0.0, 1.0, 0.15))
                        success, error = request_handler.performRequests_error_([request], None)
                        if success:
                            full_text = " ".join([obs.topCandidates_(1)[0].string() for obs in request.results() if obs.topCandidates_(1)])
                            match = re.search(r'(\d+)\s*من\s*(\d+)', full_text)
                            if not match: match = re.search(r'(\d+)\s+(\d+)\s*من', full_text)
                            if not match: match = re.search(r'(\d+)\s*من', full_text)
                            if match: extracted_footer = match.group(0)
                except Exception as e:
                    print(f"Vision OCR Error on page {p_idx}: {e}")

                # 3. Check if we already have the OCR text cached
                if str(p_idx) in extracted_text_cache:
                    print(f" Loaded Arabic text for Page {p_idx} from cache. Deferring local classification.")
                    text = extracted_text_cache[str(p_idx)]
                    deferred_local_pages.append((p_idx, text))
                    continue

                # 4. Check fallback status or try cloud
                use_local = self.client.should_use_local_fallback()
                
                if not use_local:
                    try:
                        print(f" Classifying Page {p_idx} directly using Cloud Model...")
                        res = self.client.classify_page_direct(i_bytes, extracted_footer)
                        
                        msg = f" Cloud Extracted Page {p_idx}: {res.category.value} | {res.residents} | {res.date} | Sum: {str(res.summary)}"
                        try: print(msg)
                        except UnicodeEncodeError: print(msg.encode('utf-8', errors='replace').decode('utf-8'))
                        
                        with cache_lock:
                            cached_pages[str(p_idx)] = res.model_dump()
                            temp_cache_file = f"{cache_file}.tmp"
                            with open(temp_cache_file, "w", encoding="utf-8") as f:
                                json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                            os.replace(temp_cache_file, cache_file)
                        raw_pages.append((p_idx, res))
                        continue
                    except Exception as e:
                        print(f"WARNING: Direct Cloud classification failed for page {p_idx}: {e}")
                        print("  [Transition] Triggering Rate Limit Cooldown. Falling back to local OCR...")
                        self.client.activate_cooldown()
                        use_local = True

                if use_local:
                    try:
                        print(f" Extracting Arabic text from Page {p_idx} using Local Vision Model (Qwen-VL)...")
                        text = self.client.extract_page(i_bytes)
                        with cache_lock:
                            extracted_text_cache[str(p_idx)] = text
                            temp_text_cache_file = f"{text_cache_file}.tmp"
                            with open(temp_text_cache_file, "w", encoding="utf-8") as f:
                                json.dump(extracted_text_cache, f, ensure_ascii=False, indent=2)
                            os.replace(temp_text_cache_file, text_cache_file)
                        deferred_local_pages.append((p_idx, text, extracted_footer))
                    except Exception as e:
                        print(f"WARNING: Local OCR extraction failed on page {p_idx}: {e}")
                        house_number = "UNKNOWN"
                        with cache_lock:
                            for v in cached_pages.values():
                                if v.get("house_number") and v.get("house_number") != "UNKNOWN":
                                    house_number = v.get("house_number")
                                    break
                        fallback_res = PageClassification(category=Category.OTHER_LETTERS, residents=["UNKNOWN"], date="NONE", house_number=house_number, summary="OCR extraction failed.")
                        with cache_lock:
                            cached_pages[str(p_idx)] = fallback_res.model_dump()
                            temp_cache_file = f"{cache_file}.tmp"
                            with open(temp_cache_file, "w", encoding="utf-8") as f:
                                json.dump(cached_pages, f, ensure_ascii=False, indent=2)
                            os.replace(temp_cache_file, cache_file)
                        raw_pages.append((p_idx, fallback_res))

            # Phase 2: Run deferred local classification (Pass 1b) at the very end
            if deferred_local_pages:
                print(f"Pass 1b: Running local text classification (Qwen-14B) for {len(deferred_local_pages)} deferred pages...")
                for p_idx, text, extracted_footer in deferred_local_pages:
                    try:
                        print(f" Classifying text for Page {p_idx} using 14B Text Model...")
                        res = self.client.classify_extracted_page(text, extracted_footer)
                        
                        msg = f" Local Classified Page {p_idx}: {res.category.value} | {res.residents} | {res.date} | Sum: {str(res.summary)}"
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
                        print(f"WARNING: Local classification failed on page {p_idx}: {e}")
                        house_number = "UNKNOWN"
                        with cache_lock:
                            for v in cached_pages.values():
                                if v.get("house_number") and v.get("house_number") != "UNKNOWN":
                                    house_number = v.get("house_number")
                                    break
                        fallback_res = PageClassification(category=Category.OTHER_LETTERS, residents=["UNKNOWN"], date="NONE", house_number=house_number, summary="Local classification failed.")
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

        print(f"Starting Pass 1.5 (Date Cleaning & Interpolation) for {pdf_path}...")
        self._interpolate_dates(raw_pages)

        print(f"Starting Pass 1.5 (Dependent Alias Mapping) for {pdf_path}...")
        canonical_mapping_clean = self._map_aliases(raw_pages)

        print(f"Starting Pass 2 (Tenant Grouping) for {pdf_path}...")
        
        documents = self._group_pages_into_documents(raw_pages, canonical_mapping_clean)
        
        print(f"Identified {len(documents)} document groups based on timeline logic.")
        return documents

    def _interpolate_dates(self, raw_pages: list[tuple[int, PageClassification]]):
        from datetime import datetime
        
        for i in range(len(raw_pages)):
            d = raw_pages[i][1].date
            if d and d != "NONE":
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d")
                    if dt.year < 1970 or dt.year > datetime.now().year:
                        raw_pages[i][1].date = "NONE"
                except ValueError:
                    raw_pages[i][1].date = "NONE"
                    
        for i in range(len(raw_pages)):
            if raw_pages[i][1].date == "NONE":
                last_valid = None
                for j in range(i-1, -1, -1):
                    if raw_pages[j][1].date != "NONE":
                        last_valid = raw_pages[j][1].date
                        break
                next_valid = None
                for j in range(i+1, len(raw_pages)):
                    if raw_pages[j][1].date != "NONE":
                        next_valid = raw_pages[j][1].date
                        break
                        
                if last_valid and next_valid:
                    raw_pages[i][1].date = last_valid
                elif last_valid:
                    raw_pages[i][1].date = last_valid
                elif next_valid:
                    raw_pages[i][1].date = next_valid

    def _map_aliases(self, raw_pages: list[tuple[int, PageClassification]]) -> dict[str, str]:
        canonical_mapping = {}
        active_primary_tenant = "UNKNOWN"
        ANCHOR_CATEGORIES = {Category.BASIC_DETAILS, Category.KEY_HANDOVER, Category.CONTRACT}
        
        from collections import Counter
        name_counts = Counter()
        for _, page in raw_pages:
            for r in page.residents:
                if r and r not in ("NONE", "UNKNOWN"):
                    name_counts[r.upper().strip()] += 1

        for _, page in raw_pages:
            mapped_residents = [r.upper().strip() for r in page.residents if r not in ("NONE", "UNKNOWN", "")]
            
            if page.category in ANCHOR_CATEGORIES:
                if mapped_residents:
                    active_primary_tenant = mapped_residents[0]
            else:
                for r in mapped_residents:
                    if name_counts[r] > 3:
                        active_primary_tenant = r
                        break
                        
            if page.category == Category.PERSONAL_DETAILS and active_primary_tenant != "UNKNOWN":
                for r in mapped_residents:
                    if r != active_primary_tenant:
                        canonical_mapping[r] = active_primary_tenant
                        
        return canonical_mapping

    def _group_pages_into_documents(self, raw_pages: list[tuple[int, PageClassification]], canonical_mapping_clean: dict[str, str]) -> list[DocumentGroup]:
        documents: list[DocumentGroup] = []
        
        # 1. Pre-group by Category (The "Category Wall")
        category_blocks = []
        if raw_pages:
            current_block = [raw_pages[0]]
            current_category = raw_pages[0][1].category
            for p_idx, p in raw_pages[1:]:
                if p.category == current_category:
                    current_block.append((p_idx, p))
                else:
                    category_blocks.append(current_block)
                    current_block = [(p_idx, p)]
                    current_category = p.category
            if current_block:
                category_blocks.append(current_block)

        all_groups = []
        chunk_size = 25
        
        for block in category_blocks:
            if len(block) == 1:
                all_groups.append([block[0][0]])
                continue
                
            block_groups = []
            for i in range(0, len(block), chunk_size):
                # Overlapping sliding window (overlap by 2 pages)
                start_idx = max(0, i - 2) if i > 0 else 0
                chunk = block[start_idx:i+chunk_size]
                
                pages_data = []
                for p_idx, p in chunk:
                    names_str = ", ".join([canonical_mapping_clean.get(r.upper().strip(), r) for r in p.residents])
                    summary_str = p.summary
                    pages_data.append([p_idx, names_str, summary_str])
                
                result = self.client.check_bulk_semantic_grouping(pages_data)
                
                # Merge overlapping groups using set intersection
                for new_g in result.groups:
                    if not new_g: continue
                    shared = False
                    for existing_g in block_groups:
                        if set(existing_g).intersection(set(new_g)):
                            for x in new_g:
                                if x not in existing_g:
                                    existing_g.append(x)
                            existing_g.sort()
                            shared = True
                            break
                    if not shared:
                        # Ensure we don't accidentally pull in pages from outside this block's actual chunk scope
                        # (Though the LLM should only return what we gave it)
                        block_groups.append(new_g)
                        
            all_groups.extend(block_groups)
            
        page_map = {idx: p for idx, p in raw_pages}
        for group in all_groups:
            if not group: continue
            group.sort()
            start_page = group[0]
            end_page = group[-1]
            
            group_names = []
            for p_idx in group:
                p = page_map[p_idx]
                for r in p.residents:
                    mapped = canonical_mapping_clean.get(r.upper().strip(), r)
                    if mapped not in ("NONE", "UNKNOWN", ""):
                        group_names.append(mapped)
            
            primary_tenant = "UNKNOWN"
            if group_names:
                from collections import Counter
                primary_tenant = Counter(group_names).most_common(1)[0][0]
                
            category = page_map[start_page].category
            house_number = page_map[start_page].house_number
            dates = [page_map[p_idx].date for p_idx in group if page_map[p_idx].date != "NONE"]
            
            documents.append(DocumentGroup(
                start_page=start_page,
                end_page=end_page,
                house_number=house_number,
                primary_tenant=primary_tenant,
                category=category,
                dates=dates
            ))
            
        return documents
