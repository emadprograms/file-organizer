import time
import logging
from typing import Optional, Any, Callable
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger("file_organizer")

class LLMClientError(Exception):
    """Base exception for LLM Client errors."""
    pass

class LLMRateLimitError(LLMClientError):
    """Raised when max retries for 429 Rate Limit are exceeded."""
    pass

class LLMServerError(LLMClientError):
    """Raised when 500 Server Errors exceed maximum allowed."""
    pass

class LLMClient:
    def __init__(self, api_key: str | None = None):
        self.client = genai.Client(api_key=api_key)
        self.default_model = "gemma-4-31b-it"
        self._last_request_start_time = 0.0
        self._rate_limit_seconds = 7.0

    def _wait_for_rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_start_time
        if elapsed < self._rate_limit_seconds and self._last_request_start_time > 0:
            time.sleep(self._rate_limit_seconds - elapsed)

    def generate_content(
        self,
        contents: Any,
        model: Optional[str] = None,
        is_boundary_call: bool = False,
        on_shrink_chunk: Optional[Callable[[], None]] = None,
        **kwargs
    ) -> Optional[types.GenerateContentResponse]:
        """
        Generates content using the LLM with built-in retry and rate limiting logic.
        """
        model = model or self.default_model
        
        consecutive_429 = 0
        consecutive_500 = 0
        
        while True:
            self._wait_for_rate_limit()
            self._last_request_start_time = time.time()
            
            try:
                logger.debug(f"Sending request to LLM (model: {model}).")
                logger.debug(f"Contents being sent:\n{contents}")
                
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    **kwargs
                )
                
                logger.debug(f"Received response from LLM:")
                logger.debug(f"{response.text if hasattr(response, 'text') else response}")
                
                return response
                
            except APIError as e:
                status_code = e.code if hasattr(e, 'code') else None
                message = getattr(e, 'message', str(e))
                
                # 400 or 404 -> immediate fail
                if status_code in (400, 404):
                    logger.error(f"HTTP {status_code} error: {message}")
                    raise LLMClientError(f"HTTP {status_code}: {message}") from e
                
                # 429 -> wait 65s, fail after 3
                if status_code == 429:
                    consecutive_429 += 1
                    if consecutive_429 >= 3:
                        logger.error("Max retries (3) reached for HTTP 429.")
                        raise LLMRateLimitError("Exceeded max retries for 429 errors.") from e
                    logger.warning(f"HTTP 429. Waiting 65s before retry (Attempt {consecutive_429}/3).")
                    time.sleep(65)
                    continue
                    
                # 500+ -> wait 15s
                if status_code and status_code >= 500:
                    consecutive_500 += 1
                    logger.warning(f"HTTP {status_code}. Consecutive 500s: {consecutive_500}")
                    
                    if is_boundary_call:
                        if consecutive_500 == 5:
                            logger.warning("5 consecutive 500s on boundary call. Signaling chunk shrink.")
                            if on_shrink_chunk:
                                on_shrink_chunk()
                        if consecutive_500 >= 10:
                            logger.error("10 consecutive 500s on boundary call. Failing.")
                            raise LLMServerError("Boundary call failed after 10 consecutive 500 errors.") from e
                    else:
                        if consecutive_500 >= 5:
                            logger.warning("5 consecutive 500s on non-boundary call. Skipping item.")
                            return None
                            
                    time.sleep(15)
                    continue
                    
                # Unknown API error or missing code
                logger.error(f"Unknown APIError: {e}")
                raise LLMClientError(f"Unknown APIError: {e}") from e
