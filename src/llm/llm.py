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


from src.core.exceptions import PipelineHaltError, ProviderRotationExhaustedError

class LLMFailureError(PipelineHaltError):
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

    def activate_cooldown(self) -> None:
        """Activate a long sleep to recover from severe rate limits (e.g., 429)."""
        time.sleep(65)
        
    def close(self) -> None:
        """Gracefully shut down the thread pool executor to prevent hangs."""
        if hasattr(self, '_executor') and self._executor:
            self._executor.shutdown(wait=False)

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
            log_prefix=log_prefix
        )

    def _route_llm_call(self, model: str, contents: list, response_schema: type | None = None, validation_context: dict | None = None, log_prefix: str = "Retry", max_attempts: Optional[int] = None) -> Any:
        """Route an LLM call through configured providers with deterministic resilience and failover."""
        if getattr(self, "skip_llm", False):
            from src.llm.mock import MockLLMProvider
            self.providers = [MockLLMProvider()]

        # 1. Determine Provider Sequence: [Gemini, S1, Gemini, S2]
        primary = self.providers[0]
        or_provider = next((p for p in self.providers if p.name == "openrouter"), None)
        groq_provider = next((p for p in self.providers if p.name == "groq"), None)

        secondary_1, secondary_2 = None, None
        with self._fallback_toggle_lock:
            if not self._fallback_toggle:
                secondary_1, secondary_2 = or_provider, groq_provider
            else:
                secondary_1, secondary_2 = groq_provider, or_provider
            self._fallback_toggle = not self._fallback_toggle

        # Sequence: Gemini -> S1 -> Gemini -> S2
        sequence = [primary]
        if secondary_1: sequence.append(secondary_1)
        sequence.append(primary)
        if secondary_2: sequence.append(secondary_2)

        # Filter out Nones
        provider_sequence = [p for p in sequence if p is not None]

        # 2. Resilience Loop
        max_retries = max_attempts or 3
        current_provider_idx = 0

        for attempt in range(max_retries + 1): # 1 initial + max_retries
            if current_provider_idx >= len(provider_sequence):
                break

            provider_obj = provider_sequence[current_provider_idx]
            provider_name = provider_obj.name

            try:
                future = self._executor.submit(
                    provider_obj.generate,
                    model=model,
                    contents=contents,
                    response_schema=response_schema,
                    validation_context=validation_context
                )
                response_parsed = future.result(timeout=300)

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

                # Case B: Rate Limit (429) -> Sleep 65s, Retry SAME provider
                if "429" in error_str:
                    if attempt < max_retries:
                        logger.warning(f"[{log_prefix} - {provider_name}] Rate limited (429). Sleeping 65s before retry {attempt+1}/{max_retries}...")
                        time.sleep(65)
                        continue # Retry same provider (index doesn't advance)
                    else:
                        logger.error(f"[{log_prefix} - {provider_name}] Rate limit retries exhausted.")
                        break

                # Case C: Server Error (500, 503, Timeout) -> Sleep 15s, Rotate provider
                is_server_err = any(x in error_str for x in ["500", "503", "internal error"]) or isinstance(e, (TimeoutError, concurrent.futures.TimeoutError))
                if is_server_err:
                    if attempt < max_retries:
                        logger.warning(f"[{log_prefix} - {provider_name}] Server error/timeout. Sleeping 15s and rotating provider...")
                        time.sleep(15)
                        current_provider_idx += 1
                        continue
                    else:
                        logger.error(f"[{log_prefix} - {provider_name}] Server error retries exhausted.")
                        break

                # Case D: Unexpected error
                logger.error(f"[{log_prefix} - {provider_name}] Unexpected LLM error: {e}")
                if attempt < max_retries:
                    time.sleep(2) # Minimal backoff for unknown errors
                    current_provider_idx += 1
                    continue
                else:
                    break

        raise ProviderRotationExhaustedError(f"LLM orchestration failed after {max_retries} retries across available providers. Last error: {error_str if 'error_str' in locals() else 'Unknown'}")
