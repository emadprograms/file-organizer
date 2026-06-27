"""
This file contains the tools used to read and understand the PDF pages.
It has a 'VisionExtractor' to read the small text at the bottom of the page,
and a 'CloudExtractor' that sends the page to the AI to figure out what the document is.
"""
import sys
import logging
import threading
from typing import Optional

from src.schemas import PageClassification, Category
from src.cache import SimpleCache
from src.llm import LLMClient

logger = logging.getLogger(__name__)

class VisionExtractor:
    def __init__(self, cache: SimpleCache):
        self.cache = cache

    def extract_footer(self, page_index: int, image_bytes: bytes) -> Optional[str]:
        extracted_footer: Optional[str] = None
        if sys.platform == "darwin":
            try:
                import Vision, Quartz, re  # type: ignore
                from Foundation import NSData  # type: ignore
                ns_data = NSData.dataWithBytes_length_(image_bytes, len(image_bytes))
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
                logger.error(f"Vision OCR Error on page {page_index}: {e}")
        return extracted_footer

class CloudExtractor:
    def __init__(self, cache: SimpleCache, client: LLMClient):
        self.cache = cache
        self.client = client
        self.cache_lock = threading.Lock()

    def extract(self, page_index: int, image_bytes: bytes, extracted_footer: Optional[str]) -> PageClassification:
        if len(image_bytes) < 15000:
            logger.info(f" Page {page_index} is blank (size {len(image_bytes)} bytes). Skipping LLM.")
            res = PageClassification(category=Category.OTHER_LETTERS, residents=["NONE"], date="NONE", summary="Blank page.")
        else:
            logger.info(f" Classifying Page {page_index} directly using Cloud Model...")
            res = self.client.classify_page_direct(image_bytes, extracted_footer)
            msg = f" Cloud Extracted Page {page_index}: {res.category.value} | {res.residents} | {res.date} | Sum: {str(res.summary)}"
            logger.info(msg)
            
        with self.cache_lock:
            self.cache.set(str(page_index), res.model_dump())
        return res
