"""Core LLM orchestration and client management.

This module provides the `LLMClient` which manages LLM requests via Google Gemini.
It implements resilient API routing, error handling, and rate-limit backoffs.
"""
from src.core.config import record_successful_call, GEMINI_MODEL
from src.utils.logger import log_decision_trace
import os
import time
from typing import Optional, Any

import logging

from src.core.exceptions import PipelineHaltError, ProviderRotationExhaustedError
from src.llm.providers import LLMProvider, GeminiProvider

logger = logging.getLogger(f"file_organizer.{__name__}")


class LLMFailureError(PipelineHaltError):
    """Exception raised when an LLM API call fails repeatedly."""
    pass

class InvalidResponseError(Exception):
    """Exception raised when an LLM returns a malformed or unparsable response."""
    pass


class LLMClient:
    """Client for orchestrating LLM requests.
    
    Manages API keys and handles exponential backoff and rate limits for Gemini.
    """
    
    def __init__(self, api_key: str, delay_between_pages: float = 7.0) -> None:
        """Initialize the LLMClient with API credentials.
        
        Args:
            api_key (str): Primary API key (typically for Gemini).
            delay_between_pages (float): Delay in seconds between page extractions.
                Defaults to 7.0.
        """
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("No API key provided and GEMINI_API_KEY not found in environment.")
        self.api_key = api_key
        
        self.provider: LLMProvider = GeminiProvider(api_key)
        self.delay_between_pages = delay_between_pages
        self.total_requests = 0
        self._last_request_time = 0.0

    def activate_cooldown(self) -> None:
        """Activate a long sleep to recover from severe rate limits (e.g., 429)."""
        time.sleep(65)
        
    def close(self) -> None:
        """Clean up any resources if necessary."""
        pass

    def generate_content(
        self,
        contents: Any,
        model: Optional[str] = None,
        is_boundary_call: bool = False,
        response_schema: type | None = None,
        validation_context: dict | None = None,
        **kwargs
    ) -> Any:
        """
        Compatibility wrapper for the LLM interface.
        Delegates to the robust _route_llm_call method.
        """
        model = model or getattr(self, "default_model", GEMINI_MODEL)
        log_prefix = "BoundaryCall" if is_boundary_call else "GenerateContent"
        
        return self._route_llm_call(
            model=model,
            contents=contents,
            response_schema=response_schema,
            validation_context=validation_context,
            log_prefix=log_prefix,
            max_attempts=0 if is_boundary_call else 3
        )

    def _route_llm_call(self, model: str, contents: list, response_schema: type | None = None, validation_context: dict | None = None, log_prefix: str = "Retry", max_attempts: Optional[int] = None) -> Any:
        """Route an LLM call through the provider with deterministic resilience."""
        if getattr(self, "skip_llm", False):
            from src.llm.mock import MockLLMProvider
            self.provider = MockLLMProvider()

        provider_obj = self.provider
        provider_name = provider_obj.name
        max_retries = max_attempts if max_attempts is not None else 3

        for attempt in range(max_retries + 1):
            # Enforce application-level rate limit
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.delay_between_pages:
                sleep_time = self.delay_between_pages - elapsed
                if getattr(self, "verbose", False):
                    logger.debug(f"[{log_prefix}] Enforcing app rate limit. Sleeping {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                
            self._last_request_time = time.time()

            try:
                # We call the provider directly. 
                # Network timeouts are handled natively by the underlying google-genai library.
                response_parsed = provider_obj.generate(
                    model=model,
                    contents=contents,
                    response_schema=response_schema,
                    validation_context=validation_context
                )

                # Success path
                try:
                    payload = {"model": model, "provider": provider_name, "prompt": contents}
                    if hasattr(response_parsed, "model_dump"):
                        payload["response"] = response_parsed.model_dump()
                    else:
                        payload["response"] = str(response_parsed)
                    log_decision_trace("llm_success", payload)
                except Exception as trace_err:
                    logger.debug(f"Failed to write trace: {trace_err}")

                record_successful_call()
                self.total_requests += 1

                if getattr(self, "verbose", False):
                    logger.debug(f"[{log_prefix}] Prompt: {contents}")
                    logger.debug(f"[{log_prefix}] Response: {response_parsed}")

                return response_parsed

            except Exception as e:
                # Trace error
                try:
                    log_decision_trace("llm_error", {
                        "error": str(e), 
                        "model": model, 
                        "provider": provider_name,
                        "prompt": contents
                    })
                except Exception as trace_err:
                    logger.debug(f"Failed to write error trace: {trace_err}")

                error_str = str(e).lower()

                # Case A: Immediate Halt (400, 401, 403, or Auth errors)
                is_auth_fail = any(x in error_str for x in ["401", "403", "400", "api key not valid", "invalid_api_key"])
                if is_auth_fail:
                    logger.error(f"[{log_prefix}] Critical Auth/Request error on {provider_name}: {e}. Halting pipeline.")
                    raise LLMFailureError(f"Critical LLM API error: {e}")

                # Case B: Rate Limit (429) -> Sleep 65s, Retry
                if "429" in error_str:
                    if attempt < max_retries:
                        logger.warning(f"[{log_prefix} - {provider_name}] Rate limited (429). Sleeping 65s before retry {attempt+1}/{max_retries}...")
                        time.sleep(65)
                        continue 
                    else:
                        logger.error(f"[{log_prefix} - {provider_name}] Rate limit retries exhausted.")
                        break

                # Case C: Server Error (500, 503, Timeout) -> Sleep 5s, Retry
                is_server_err = any(x in error_str for x in ["500", "503", "internal error"]) or isinstance(e, TimeoutError)
                if is_server_err:
                    if attempt < max_retries:
                        logger.warning(f"[{log_prefix} - {provider_name}] Server error/timeout. Sleeping 5s before retry {attempt+1}/{max_retries}...")
                        time.sleep(5)  # Reduced from 15s to 5s
                        continue
                    else:
                        logger.error(f"[{log_prefix} - {provider_name}] Server error retries exhausted.")
                        break

                # Case D: Unexpected error
                logger.error(f"[{log_prefix} - {provider_name}] Unexpected LLM error: {e}")
                if attempt < max_retries:
                    time.sleep(2) # Minimal backoff for unknown errors
                    continue
                else:
                    break

        raise ProviderRotationExhaustedError(f"LLM orchestration failed after {max_retries} retries on {provider_name}. Last error: {error_str if 'error_str' in locals() else 'Unknown'}")
