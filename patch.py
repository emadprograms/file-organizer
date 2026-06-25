with open('src/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find("        def process_single_page(page_info):")
end_idx = content.find("        raw_pages.sort(key=lambda x: x[0])")

if start_idx != -1 and end_idx != -1:
    new_code = """        if pages_to_process:
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
                            match = re.search(r'(\\d+)\\s*من\\s*(\\d+)', full_text)
                            if not match: match = re.search(r'(\\d+)\\s+(\\d+)\\s*من', full_text)
                            if not match: match = re.search(r'(\\d+)\\s*من', full_text)
                            if match: extracted_footer = match.group(0)
                            else:
                                match = re.search(r'(الصفحة|صفحة|page)[\\s:]*(\\d+)', full_text, re.IGNORECASE)
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
                        page_match = re.search(r'(\\d+)\\s*من', extracted_footer)
                        if not page_match:
                            page_match = re.search(r'(?:الصفحة|صفحة|page)[\\s:]*(\\d+)', extracted_footer, re.IGNORECASE)
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
"""
    with open('src/pipeline.py', 'w', encoding='utf-8') as f:
        f.write(content[:start_idx] + new_code + "\n        " + content[end_idx:])
    print("Patched successfully!")
else:
    print("Indices not found")
