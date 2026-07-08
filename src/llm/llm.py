"""Core LLM orchestration and client management.

This module provides the `LLMClient` which orchestrates LLM requests across multiple
provider strategies (defined in `providers.py`). It implements resilient API routing,
error handling, rate-limit backoffs, and cloud failover for robust document processing.
"""
from src.core.config import record_successful_call, OPENROUTER_MODEL, GROQ_MODEL, GEMINI_MODEL
from src.logger import log_decision_trace
import concurrent.futures
import os
import time
import json
from typing import Optional, Any, Deque, Protocol

import re
import random
import threading
import logging
import base64
from collections import deque
from google import genai
from google.genai import types
import openai

logger = logging.getLogger(f"file_organizer.{__name__}")


class LLMFailureError(Exception):
    """Exception raised when an LLM API call fails repeatedly."""
    pass

class InvalidResponseError(Exception):
    """Exception raised when an LLM returns a malformed or unparsable response."""
    pass


from src.llm.providers import LLMProvider, GeminiProvider, OpenRouterProvider, GroqProvider

class LLMClient:
    """Client for orchestrating LLM requests across multiple providers.
    
    Manages API keys, provider fallback logic, and specific orchestration tasks
    like name clustering and date outlier detection.
    """
    
    def __init__(self, api_key: str, delay_between_pages: float = 5.0) -> None:
        """Initialize the LLMClient with API credentials.
        
        Args:
            api_key (str): Primary API key (typically for Gemini).
            delay_between_pages (float): Delay in seconds between page extractions.
                Defaults to 5.0.
        """
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("No API key provided and GEMINI_API_KEY not found in environment.")
        self.api_key = api_key
        
        self.providers: list[LLMProvider] = [GeminiProvider(api_key)]
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if openrouter_key:
            self.providers.append(OpenRouterProvider(openrouter_key))
            
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_key:
            self.providers.append(GroqProvider(groq_key))

        self.delay_between_pages = delay_between_pages
        self.total_requests = 0
        self._fallback_toggle = False
        self._fallback_toggle_lock = threading.Lock()
        self._cached_schema = None
        self._cached_schema_lock = threading.Lock()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self.global_consecutive_500_errors = 0

    def activate_cooldown(self) -> None:
        """Activate a long sleep to recover from severe rate limits (e.g., 429)."""
        time.sleep(65)

    def generate_content(
        self,
        contents: Any,
        model: Optional[str] = None,
        is_boundary_call: bool = False,
        response_schema: type | None = None,
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
            log_prefix=log_prefix
        )

    def _route_llm_call(self, model: str, contents: list, response_schema: type | None = None, log_prefix: str = "Retry", max_attempts: Optional[int] = None) -> Any:
        """Route an LLM call through configured providers with failover using tenacity."""
        if getattr(self, "skip_llm", False):
            from src.llm.mock import MockLLMProvider
            self.providers = [MockLLMProvider()]

        provider_sequence = [self.providers[0]]
        or_provider = next((p for p in self.providers if p.name == "openrouter"), None)
        groq_provider = next((p for p in self.providers if p.name == "groq"), None)
        
        secondary_1, secondary_2 = None, None
        with self._fallback_toggle_lock:
            if not self._fallback_toggle:
                secondary_1, secondary_2 = or_provider, groq_provider
            else:
                secondary_1, secondary_2 = groq_provider, or_provider
                
            self._fallback_toggle = not self._fallback_toggle
        
        if secondary_1:
            provider_sequence.append(secondary_1)
            provider_sequence.append(self.providers[0])
        if secondary_2:
            provider_sequence.append(secondary_2)

        import tenacity

        def should_retry(retry_state):
            if retry_state.outcome.failed:
                e = retry_state.outcome.exception()
                error_str = str(e).lower()
                is_auth = "401" in error_str or "403" in error_str or "400" in error_str or "api key not valid" in error_str or "invalid_api_key" in error_str
                if is_auth:
                    return False
                return True
            return False

        last_error_is_5xx = False
        
        for provider_obj in provider_sequence:
            provider_name = provider_obj.name
            
            # Use tenacity for backoff on this provider
            @tenacity.retry(
                wait=tenacity.wait_exponential(multiplier=1, min=2, max=65),
                stop=tenacity.stop_after_attempt(3),
                retry=tenacity.retry_if_exception(should_retry),
                reraise=True
            )
            def _call_provider():
                try:
                    future = self._executor.submit(
                        provider_obj.generate,
                        model=model,
                        contents=contents,
                        response_schema=response_schema
                    )
                    response_parsed = future.result(timeout=300)
                    
                    # Trace logging for successful calls
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
                    self.global_consecutive_500_errors = 0
                    
                    if getattr(self, "verbose", False):
                        logger.debug(f"[{log_prefix}] Prompt: {contents}")
                        logger.debug(f"[{log_prefix}] Response: {response_parsed}")

                    return response_parsed

                except Exception as e:
                    # Trace logging for errors
                    try:
                        log_decision_trace("llm_error", {
                            "error": str(e), 
                            "model": model, 
                            "provider": provider_name,
                            "prompt": contents
                        })
                    except Exception as trace_err:
                        logger.debug(f"Failed to write error trace: {trace_err}")
                        
                    if isinstance(e, concurrent.futures.TimeoutError):
                        raise TimeoutError("LLM API call hung and timed out after 300 seconds.")
                    
                    logger.warning(f"[{log_prefix} - {provider_name}] LLM call failed: {e}")
                    raise e
                    
            try:
                return _call_provider()
            except Exception as e:
                error_str = str(e).lower()
                is_auth = "401" in error_str or "403" in error_str or "400" in error_str or "api key not valid" in error_str or "invalid_api_key" in error_str
                if is_auth:
                    logger.warning(f"[{log_prefix}] Auth/Bad Request error on {provider_name}: fail fast. Error: {e}")
                    raise e
                
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str or "timeout" in error_str
                last_error_is_5xx = is_5xx or isinstance(e, TimeoutError)
                if last_error_is_5xx:
                    self.global_consecutive_500_errors += 1
                    if self.global_consecutive_500_errors >= 5:
                        raise LLMFailureError("Global 500 error limit reached. Aborting pipeline.")
                
                logger.warning(f"[Cloud Fallback] {provider_name} exhausted retries. Failing over to next provider.")
                continue

        raise RuntimeError("LLM routing failed across all providers")

