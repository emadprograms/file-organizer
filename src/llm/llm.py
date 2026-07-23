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
    
    def __init__(self, api_key: str | None = None, delay_between_pages: float = 7.0) -> None:
        """Initialize the LLMClient with API credentials.
        
        Args:
            api_key (str | None): Primary API key (typically for Gemini).
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
        self.default_model = GEMINI_MODEL

    def activate_cooldown(self) -> None:
        """Activate a long sleep to recover from severe rate limits (e.g., 429)."""
        time.sleep(65)
        
    def close(self) -> None:
        """Clean up any resources if necessary."""
        pass

    def generate_content(
        self,
        contents: list[Any],
        model: str | None = None,
        is_boundary_call: bool = False,
        response_schema: type | None = None,
        validation_context: dict[str, Any] | None = None,
        **kwargs: Any
    ) -> Any:
        """Compatibility wrapper for the LLM interface.
        
        Delegates to the robust _route_llm_call method.
        
        Args:
            contents (list[Any]): The messages payload to be routed to the LLM.
            model (str | None): Optional model string to use instead of the default.
            is_boundary_call (bool): Whether this is a boundary detection call (skips retries).
            response_schema (type | None): Optional Pydantic model type for structured output validation.
            validation_context (dict[str, Any] | None): Optional context dictionary for Pydantic field validators.
            **kwargs (Any): Additional keyword arguments.
            
        Returns:
            Any: A validated Pydantic object if response_schema is provided, otherwise raw text/dict.
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

    def upload_file(self, file_path: str) -> Any:
        """Upload a file to the active provider's cloud storage.
        
        Args:
            file_path (str): The local path to the file.
            
        Returns:
            Any: A provider-specific file object.
        """
        if not hasattr(self.provider, "upload_file"):
            raise NotImplementedError(f"Provider {self.provider.name} does not support upload_file")
        return self.provider.upload_file(file_path)
        
    def delete_file(self, file_obj: Any) -> None:
        """Delete a file from the active provider's cloud storage.
        
        Args:
            file_obj (Any): The provider-specific file object to delete.
        """
        if hasattr(self.provider, "delete_file"):
            self.provider.delete_file(file_obj)

    def _route_llm_call(
        self, 
        model: str, 
        contents: list[Any], 
        response_schema: type | None = None, 
        validation_context: dict[str, Any] | None = None, 
        log_prefix: str = "Retry", 
        max_attempts: int | None = None
    ) -> Any:
        """Route an LLM call through the provider with deterministic resilience and fallbacks.

        Handles rotation between providers, exponential backoffs, and tracking of request rates.
        This internal method ensures fail-safety without leaking exceptions unnecessarily.

        Args:
            model (str): The primary LLM model string to use (e.g., 'gemini-1.5-flash').
            contents (list[Any]): The messages payload to be routed to the LLM.
            response_schema (type | None): Optional Pydantic model type for structured output validation.
            validation_context (dict[str, Any] | None): Optional context dictionary for Pydantic field validators.
            log_prefix (str): Prefix used for log tracking (default: "Retry").
            max_attempts (int | None): Number of times to retry the primary model before fallback.

        Returns:
            Any: A validated Pydantic object if response_schema is provided, otherwise raw text/dict.
            
        Raises:
            ProviderRotationExhaustedError: If all configured models and fallbacks fail.
        """
        if getattr(self, "skip_llm", False):
            from src.llm.mock import MockLLMProvider
            self.provider = MockLLMProvider()

        provider_obj = self.provider
        provider_name = provider_obj.name
        primary_max_retries = max_attempts if max_attempts is not None else 3

        fallback_models = ["gemini-3.5-flash", "gemini-3-flash", "gemini-2.5-flash"]
        models_to_try = [model]
        for fbm in fallback_models:
            if fbm not in models_to_try:
                models_to_try.append(fbm)
                
        last_error_str = "Unknown"

        for model_idx, current_model in enumerate(models_to_try):
            is_primary = (model_idx == 0)
            max_retries = primary_max_retries if is_primary else 0

            for attempt in range(max_retries + 1):
                # Enforce application-level rate limit
                now = time.time()
                elapsed = now - self._last_request_time
                if elapsed < self.delay_between_pages and not getattr(self, 'skip_llm', False):
                    sleep_time = self.delay_between_pages - elapsed
                    if getattr(self, "verbose", False):
                        logger.debug(f"[{log_prefix}] Enforcing app rate limit. Sleeping {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    
                self._last_request_time = time.time()

                try:
                    # We call the provider directly. 
                    # Network timeouts are handled natively by the underlying google-genai library.
                    response_parsed = provider_obj.generate(
                        model=current_model,
                        contents=contents,
                        response_schema=response_schema,
                        validation_context=validation_context
                    )

                    # Success path
                    try:
                        payload = {"model": current_model, "provider": provider_name, "prompt": contents}
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
                            "model": current_model, 
                            "provider": provider_name,
                            "prompt": contents
                        })
                    except Exception as trace_err:
                        logger.debug(f"Failed to write error trace: {trace_err}")

                    error_str = str(e).lower()
                    last_error_str = error_str

                    # Case A: Immediate Halt (400, 401, 403, or Auth errors)
                    is_auth_fail = any(x in error_str for x in ["401", "403", "400", "api key not valid", "invalid_api_key"])
                    if is_auth_fail:
                        logger.error(f"[{log_prefix}] Critical Auth/Request error on {provider_name} ({current_model}): {e}. Halting pipeline.")
                        raise LLMFailureError(f"Critical LLM API error: {e}")

                    # Case B: Read Timeout -> No retries for timeout! Fail fast to next model.
                    is_timeout = "timeout" in error_str or "timed out" in error_str or isinstance(e, TimeoutError)
                    if is_timeout:
                        logger.warning(f"[{log_prefix} - {provider_name}] Read timeout on {current_model}. Falling back to next model immediately.")
                        break # Break out of retries for this model, move to next model

                    # Case C: Rate Limit (429) -> Sleep 65s, Retry
                    if "429" in error_str:
                        if attempt < max_retries:
                            logger.warning(f"[{log_prefix} - {provider_name}] Rate limited (429) on {current_model}. Sleeping 65s before retry {attempt+1}/{max_retries}...")
                            time.sleep(65)
                            continue 
                        else:
                            logger.warning(f"[{log_prefix} - {provider_name}] Rate limit retries exhausted on {current_model}.")
                            break

                    # Case D: Server Error (500, 503) -> Sleep 5s, Retry
                    is_server_err = any(x in error_str for x in ["500", "503", "internal error"])
                    if is_server_err:
                        if attempt < max_retries:
                            logger.warning(f"[{log_prefix} - {provider_name}] Server error on {current_model}. Sleeping 5s before retry {attempt+1}/{max_retries}...")
                            time.sleep(5)
                            continue
                        else:
                            logger.warning(f"[{log_prefix} - {provider_name}] Server error retries exhausted on {current_model}.")
                            break

                    # Case E: Unexpected error
                    logger.error(f"[{log_prefix} - {provider_name}] Unexpected LLM error on {current_model}: {e}")
                    if attempt < max_retries:
                        time.sleep(2) # Minimal backoff for unknown errors
                        continue
                    else:
                        break

        raise ProviderRotationExhaustedError(f"LLM orchestration failed after exhausting all models on {provider_name}. Last error: {last_error_str}")
