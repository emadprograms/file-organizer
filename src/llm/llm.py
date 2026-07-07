"""Core LLM orchestration and client management.

This module provides the `LLMClient` which orchestrates LLM requests across multiple
provider strategies (defined in `providers.py`). It implements resilient API routing,
error handling, rate-limit backoffs, and cloud failover for robust document processing.
"""
from src.core.config import record_successful_call, OPENROUTER_MODEL, GROQ_MODEL, GEMINI_MODEL
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



log = logging.getLogger(__name__)


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

        """Route an LLM call through configured providers with failover.
        
        Attempts to call the primary provider and falls back to secondary
        providers if rate limits or server errors are encountered.
        
        Args:
            model (str): The model identifier to use.
            contents (list): Prompt contents (text and/or images).
            response_schema (type): Pydantic model for structured output.
            log_prefix (str): Prefix used for logging. Defaults to "Retry".
            max_attempts (Optional[int]): Ignored legacy parameter.
            
        Returns:
            Any: An instance of the response_schema.
            
        Raises:
            RuntimeError: If all providers fail.
        """
        if getattr(self, "skip_llm", False):
            if response_schema is None:
                # Handle name canonicalization requests by returning an identity map
                for content in contents:
                    if isinstance(content, str) and "Raw names:" in content:
                        try:
                            # Extract the JSON list of names from the prompt
                            start_idx = content.find("[")
                            end_idx = content.rfind("]") + 1
                            if start_idx != -1 and end_idx != -1:
                                names = json.loads(content[start_idx:end_idx])
                                if isinstance(names, list):
                                    return json.dumps({name: name for name in names}, ensure_ascii=False)
                        except Exception:
                            pass
                return "{}"
            schema_name = response_schema.__name__
            if schema_name == "GroupingResponse":
                import re
                from src.core.schemas import GroupingResponse, GroupEntry
                content_str = str(contents)
                m = re.search(r'Chunk range: Page (\d+) to Page (\d+)', content_str)
                if m:
                    start, end = int(m.group(1)), int(m.group(2))
                else:
                    start, end = 0, 0
                return GroupingResponse(groups=[GroupEntry(start_page=start, end_page=end, reason="mock skip-llm", brief_arabic_title="عنوان تجريبي")])
            elif schema_name == "RoutingResponse":
                from src.processing.routing import RoutingResponse
                return RoutingResponse(selected_folder="13_others", reason="mock skip-llm")
                
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

        current_provider_idx = 0
        provider_attempts = 0
        last_error_is_5xx = False
        
        while current_provider_idx < len(provider_sequence):
            provider_obj = provider_sequence[current_provider_idx]
            provider_name = provider_obj.name
            provider_attempts += 1
            
            start_time = time.time()
            try:
                future = self._executor.submit(
                    provider_obj.generate,
                    model=model,
                    contents=contents,
                    response_schema=response_schema
                )
                
                try:
                    response_parsed = future.result(timeout=300)
                    
                    # Trace logging for successful calls
                    import uuid
                    from datetime import datetime
                    from src.logger import LOGS_DIR
                    run_id = str(uuid.uuid4())[:8]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    traces_dir = os.path.join(LOGS_DIR, "traces")
                    os.makedirs(traces_dir, exist_ok=True)
                    trace_path = os.path.join(traces_dir, f"{run_id}_{timestamp}.json")
                    try:
                        payload = {"model": model, "provider": provider_name}
                        if hasattr(response_parsed, "model_dump"):
                            payload["response"] = response_parsed.model_dump()
                        else:
                            payload["response"] = str(response_parsed)
                        with open(trace_path, "w", encoding="utf-8") as f:
                            json.dump(payload, f, ensure_ascii=False, indent=2)
                    except Exception as trace_err:
                        log.debug(f"Failed to write trace: {trace_err}")
                except Exception as parse_err:
                    # Trace logging for errors
                    import uuid
                    from datetime import datetime
                    from src.logger import LOGS_DIR
                    run_id = str(uuid.uuid4())[:8]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    traces_dir = os.path.join(LOGS_DIR, "traces")
                    os.makedirs(traces_dir, exist_ok=True)
                    error_trace_path = os.path.join(traces_dir, f"{run_id}_{timestamp}.error.json")
                    try:
                        with open(error_trace_path, "w", encoding="utf-8") as f:
                            json.dump({"error": str(parse_err), "model": model, "provider": provider_name}, f, ensure_ascii=False, indent=2)
                    except Exception as trace_err:
                        log.debug(f"Failed to write error trace: {trace_err}")
                        
                    if isinstance(parse_err, concurrent.futures.TimeoutError):
                        raise TimeoutError("LLM API call hung and timed out after 300 seconds.")
                    raise parse_err

                record_successful_call()
                self.total_requests += 1
                self.global_consecutive_500_errors = 0

                elapsed = time.time() - start_time
                if elapsed < 7.0:
                    time.sleep(7.0 - elapsed)
                
                if getattr(self, "verbose", False):
                    log.debug(f"[{log_prefix}] Prompt: {contents}")
                    log.debug(f"[{log_prefix}] Response: {response_parsed}")

                return response_parsed

            except Exception as e:
                error_str = str(e).lower()
                is_auth = "401" in error_str or "403" in error_str or "400" in error_str or "api key not valid" in error_str or "invalid_api_key" in error_str
                is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str or "timeout" in error_str
                
                last_error_is_5xx = is_5xx or isinstance(e, TimeoutError)
                
                log.warning(f"[{log_prefix} - {provider_name} attempt {provider_attempts}] LLM call failed: {e}")
                
                if provider_name in ("openrouter", "groq"):
                    current_provider_idx += 1
                    provider_attempts = 0
                    if current_provider_idx < len(provider_sequence):
                        next_name = provider_sequence[current_provider_idx].name
                        log.warning(f"[Cloud Fallback] {provider_name} failed. Failing over to {next_name}")
                    continue

                if is_auth:
                    log.warning(f"[{log_prefix}] Auth/Bad Request error on {provider_name}: fail fast. Error: {e}")
                    raise e
                    
                if is_429:
                    if provider_attempts >= 3:
                        current_provider_idx += 1
                        provider_attempts = 0
                        if current_provider_idx < len(provider_sequence):
                            next_name = provider_sequence[current_provider_idx].name
                            log.warning(f"[Cloud Fallback] Failed over to {next_name}")
                        continue
                    log.warning(f"[{log_prefix}] 429 Error on {provider_name}. Sleeping for 65 seconds.")
                    self.activate_cooldown()
                    continue
                    
                if is_5xx or isinstance(e, TimeoutError):
                    if provider_attempts >= 3:
                        current_provider_idx += 1
                        provider_attempts = 0
                        if current_provider_idx < len(provider_sequence):
                            next_name = provider_sequence[current_provider_idx].name
                            log.warning(f"[Cloud Fallback] Failed over to {next_name}")
                        continue
                    log.warning(f"[{log_prefix}] 5xx/Timeout on {provider_name}. Retrying (attempt {provider_attempts}/3)...")
                    time.sleep(7.5 * provider_attempts)
                    continue
                
                if provider_attempts >= 3:
                    current_provider_idx += 1
                    provider_attempts = 0
                    if current_provider_idx < len(provider_sequence):
                        next_name = provider_sequence[current_provider_idx].name
                        log.warning(f"[Cloud Fallback] Failed over to {next_name}")
                    continue
                time.sleep(7.5)
                continue

        if last_error_is_5xx:
            self.global_consecutive_500_errors += 1
            if self.global_consecutive_500_errors >= 5:
                raise LLMFailureError("Global 500 error limit reached. Aborting pipeline.")

        raise RuntimeError("LLM routing failed across all providers")

