import concurrent.futures
from typing import List, Dict, Any, Tuple
from src.ingest import PdfIngestor
from src.llm import GemmaClient

class Pipeline:
    def __init__(self, api_keys: List[str] = None):
        self.ingestor = PdfIngestor()
        self.client = GemmaClient(api_keys)
        num_keys = len(api_keys) if api_keys else 1
        self.max_workers = min(10, num_keys * 3)

    def _process_single_page(self, page_index: int, image_bytes: bytes) -> Tuple[int, Dict[str, Any]]:
        result = self.client.process_image(image_bytes)
        return page_index, result

    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        print(f"Starting processing for {pdf_path}...")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {}
            for page_index, image_bytes in self.ingestor.extract_pages_as_images(pdf_path):
                future = executor.submit(self._process_single_page, page_index, image_bytes)
                future_to_page[future] = page_index
                
            for future in concurrent.futures.as_completed(future_to_page):
                page_index = future_to_page[future]
                try:
                    res_idx, data = future.result()
                    results.append((res_idx, data))
                except Exception as exc:
                    print(f"Page {page_index} generated an exception: {exc}")
        
        results.sort(key=lambda x: x[0])
        
        documents = []
        current_doc = None
        
        for idx, data in results:
            if not current_doc:
                current_doc = {"start_page": idx, "end_page": idx, "data": data}
            elif data.get("is_continuation", False):
                current_doc["end_page"] = idx
            else:
                documents.append(current_doc)
                current_doc = {"start_page": idx, "end_page": idx, "data": data}
                
        if current_doc:
            documents.append(current_doc)
            
        return documents
