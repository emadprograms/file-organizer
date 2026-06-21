import os
import google.generativeai as genai
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from typing import Dict, Any

class RateLimitError(Exception):
    pass

class GemmaClient:
    def __init__(self, api_keys: list[str] = None):
        if not api_keys:
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("No API keys provided and GEMINI_API_KEY not found in environment.")
            self.api_keys = [key]
        else:
            self.api_keys = api_keys
        
        self.current_key_idx = 0
        self._configure_client()

    def _configure_client(self):
        genai.configure(api_key=self.api_keys[self.current_key_idx])
        # Note: using gemini-1.5-flash as standard for multimodal tasks
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def switch_key(self):
        if len(self.api_keys) > 1:
            self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
            self._configure_client()

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception)
    )
    def process_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Processes image bytes and returns structured data.
        Returns: { 'house_number': str, 'resident_name': str, 'category': str, 'is_continuation': bool }
        """
        prompt = """
        Analyze this document page and extract the following:
        - House Number
        - Resident Name
        - Category (choose exactly one of the 13 defined categories)
        - is_continuation (true if this page seems to be a continuation of the previous page's document, false otherwise)
        
        Return the result as JSON.
        """
        
        try:
            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": image_bytes}
            ])
            
            import json
            import re
            
            text = response.text
            match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
                
            return json.loads(text)
            
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e) or "quota" in str(e).lower():
                self.switch_key()
            raise e
