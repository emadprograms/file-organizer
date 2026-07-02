"""Information extraction components for processing document pages.

Provides the VisionExtractor for local OCR (e.g., footer extraction) and
the CloudExtractor for LLM-based page classification.
"""
import sys
import logging
import threading
from typing import Optional, Any

from src.cache import SimpleCache
from src.llm import LLMClient

logger = logging.getLogger(__name__)

class VisionExtractor:
    """Extractor for performing local OCR tasks on page images."""
    def __init__(self, cache: SimpleCache):
        """Initialize the VisionExtractor.
        
        Args:
            cache (SimpleCache): Cache instance for storing/retrieving OCR results.
        """
        self.cache = cache

    def extract_footer(self, page_index: int, image_bytes: bytes) -> Optional[str]:
        """Extract pagination text from the footer of a page image.
        
        Uses macOS Vision framework (if available) to OCR the bottom 15% of the
        page and extracts text like "1 of 5" or "1 من 5".
        
        Args:
            page_index (int): The 1-indexed page number being processed.
            image_bytes (bytes): The PNG image data of the page.
            
        Returns:
            Optional[str]: The extracted footer string, or None if not found or unsupported.
        """
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
    """Extractor for sending page images to an LLM for classification."""
    def __init__(self, cache: SimpleCache, client: LLMClient):
        """Initialize the CloudExtractor.
        
        Args:
            cache (SimpleCache): Cache instance to avoid redundant API calls.
            client (LLMClient): The LLM client to use for classification.
        """
        self.cache = cache
        self.client = client
        self.cache_lock = threading.Lock()

    def extract(self, page_index: int, image_bytes: bytes, extracted_footer: Optional[str], prompt_template: str, fields: list) -> Any:
        """Classify a single document page using the LLM.
        
        Skips LLM invocation for pages that are clearly blank based on image size.
        Caches the result to avoid redundant classification on subsequent runs.
        
        Args:
            page_index (int): The 1-indexed page number being classified.
            image_bytes (bytes): The PNG image data of the page.
            extracted_footer (Optional[str]): Any text previously extracted from the footer.
            
        Returns:
            Any: The structured classification result from the LLM.
        """
        if len(image_bytes) < 15000:
            logger.info(f" Page {page_index} is blank (size {len(image_bytes)} bytes). Skipping LLM.")
            from pydantic import create_model, Field
            from typing import Any
            type_mapping = {"str": str, "list[str]": list[str], "int": int, "bool": bool}
            model_fields = {}
            fallback_values = {}
            for f in fields:
                t = type_mapping.get(f.type, Any)
                model_fields[f.name] = (t, Field(description=f.description))
                fallback_values[f.name] = ["NONE"] if f.type == "list[str]" else "NONE"
            DynamicSchema = create_model('DynamicClassification', **model_fields)
            res = DynamicSchema(**fallback_values)
        else:
            logger.info(f" Classifying Page {page_index} directly using Cloud Model...")
            res = self.client.classify_page_direct(image_bytes, extracted_footer, prompt_template, fields)
            msg = f" Cloud Extracted Page {page_index}: {res.model_dump()}"
            logger.info(msg)
            
        with self.cache_lock:
            dumped_data = res.model_dump(mode='json')
            self.cache.set(str(page_index), dumped_data)
            logger.debug(f"Saved page {page_index} to cache {self.cache.filename}")
        return res
