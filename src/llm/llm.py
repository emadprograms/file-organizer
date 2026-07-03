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

from src.core.schemas import (
    EntityResolutionMapping,
    BulkSemanticMatchResult,
    DateOutlierDetectionResult
)

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

    def activate_cooldown(self) -> None:
        """Activate a long sleep to recover from severe rate limits (e.g., 429)."""
        time.sleep(65)

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
                    response_parsed = future.result(timeout=20)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError("LLM API call hung and timed out after 20 seconds.")

                record_successful_call()
                self.total_requests += 1

                elapsed = time.time() - start_time
                if elapsed < 7.0:
                    time.sleep(7.0 - elapsed)
                
                return response_parsed

            except Exception as e:
                error_str = str(e).lower()
                is_auth = "401" in error_str or "403" in error_str or "400" in error_str or "api key not valid" in error_str or "invalid_api_key" in error_str
                is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str or "timeout" in error_str
                
                log.info(f"[{log_prefix} - {provider_name} attempt {provider_attempts}] LLM call failed: {e}")
                
                if provider_name in ("openrouter", "groq"):
                    current_provider_idx += 1
                    provider_attempts = 0
                    if current_provider_idx < len(provider_sequence):
                        next_name = provider_sequence[current_provider_idx].name
                        log.info(f"[Cloud Fallback] {provider_name} failed. Failing over to {next_name}")
                    continue

                if is_auth:
                    log.info(f"[{log_prefix}] Auth/Bad Request error on {provider_name}: fail fast. Error: {e}")
                    raise e
                    
                if is_429:
                    if provider_attempts >= 3:
                        current_provider_idx += 1
                        provider_attempts = 0
                        if current_provider_idx < len(provider_sequence):
                            next_name = provider_sequence[current_provider_idx].name
                            log.info(f"[Cloud Fallback] Failed over to {next_name}")
                        continue
                    log.info(f"[{log_prefix}] 429 Error on {provider_name}. Sleeping for 65 seconds.")
                    self.activate_cooldown()
                    continue
                    
                if is_5xx or isinstance(e, TimeoutError):
                    current_provider_idx += 1
                    provider_attempts = 0
                    if current_provider_idx < len(provider_sequence):
                        next_name = provider_sequence[current_provider_idx].name
                        log.info(f"[Cloud Fallback] Failed over to {next_name}")
                    continue
                
                if provider_attempts >= 3:
                    current_provider_idx += 1
                    provider_attempts = 0
                    if current_provider_idx < len(provider_sequence):
                        next_name = provider_sequence[current_provider_idx].name
                        log.info(f"[Cloud Fallback] Failed over to {next_name}")
                    continue
                time.sleep(7.5)
                continue

        raise RuntimeError("LLM routing failed across all providers")

    def cluster_names(self, anchor_names: list[str], other_names: list[str], prompt_template: str) -> dict[str, str]:
        """Group other names into anchor names using a Two-Tier Hybrid approach.
        
        Tier 1: Fast local string matching (thefuzz) to collapse severe OCR typos into anchors.
        Tier 2: LLM (Plain Text mode) to link the remaining other names to anchors.
        """
        if not anchor_names or not other_names:
            return {}
            
        # Tier 1: Fast Phonetic Clustering against anchor names
        import difflib
        try:
            from thefuzz import fuzz
        except ImportError:
            fuzz = None

        final_mapping = {}
        unmatched_other_names = []
        
        for other in other_names:
            matched_anchor = None
            if fuzz:
                # First check exact token_set_ratio with 70 threshold for OCR misspellings
                for anchor in anchor_names:
                    if fuzz.token_set_ratio(other, anchor) > 70:
                        matched_anchor = anchor
                        break
                # If still not matched, try phonetic/ratio on normalized names
                if not matched_anchor:
                    for anchor in anchor_names:
                        if fuzz.ratio(other.replace(" ", ""), anchor.replace(" ", "")) > 70:
                            matched_anchor = anchor
                            break
            else:
                matches = difflib.get_close_matches(other, anchor_names, n=1, cutoff=0.70)
                if matches:
                    matched_anchor = matches[0]
                    
            if matched_anchor:
                final_mapping[other] = matched_anchor
            else:
                unmatched_other_names.append(other)

        log.info(f"Tier 1 (Local) matched {len(final_mapping)} names directly to anchors. {len(unmatched_other_names)} remaining for LLM.")
        
        if not unmatched_other_names:
            return final_mapping

        # Tier 2: LLM Cross-Lingual Linking
        log.info(f"Tier 2 (LLM) matching {len(unmatched_other_names)} names to anchors (Plain Text mode)...")
        
        system_prompt = prompt_template
        
        user_prompt = "Official Anchor Names:\n" + "\n".join(f"- {n}" for n in anchor_names) + "\n\nOther Names:\n" + "\n".join(f"- {n}" for n in unmatched_other_names)
        
        try:
            result_text = self._route_llm_call(
                model=GEMINI_MODEL,
                contents=[system_prompt, user_prompt],
                response_schema=None,
                log_prefix="NameClusteringText"
            )
            
            for line in result_text.splitlines():
                if "->" in line:
                    parts = line.split("->")
                    raw = parts[0].strip()
                    canonical = parts[1].strip()
                    if raw and canonical and canonical != "NONE" and canonical in anchor_names:
                        final_mapping[raw] = canonical
                        
            return final_mapping
        except Exception as e:
            log.error(f"[NameClusteringText] LLM failed: {e}. Returning only Tier 1 mapping.")
            return final_mapping





    def classify_page_direct(self, image_bytes: bytes, extracted_footer: Optional[str], prompt_template: str, fields: list) -> Any:
        """Classify a document page using the LLM based on its image content.
        
        Args:
            image_bytes (bytes): PNG image data of the page.
            extracted_footer (Optional[str]): Text previously OCR'd from the footer.
            prompt_template (str): The instructions for extraction.
            fields (list): The list of ConfigField objects.
            
        Returns:
            Any: The classification result (dynamic model).
        """
        from pydantic import create_model, Field
        from typing import Any
        
        with self._cached_schema_lock:
            if self._cached_schema is None:
                type_mapping = {
                    "str": str,
                    "list[str]": list[str],
                    "int": int,
                    "bool": bool
                }
                
                model_fields = {}
                for f in fields:
                    t = type_mapping.get(f.type, Any)
                    model_fields[f.name] = (t, Field(description=f.description))
                    
                self._cached_schema = create_model('DynamicClassification', **model_fields)
            
            DynamicSchema = self._cached_schema

        system_prompt = prompt_template
        user_prompt = "Classify this scanned document page."
        if extracted_footer:
            user_prompt += f"\n\nExtracted Footer Text: {extracted_footer}"
            
        contents = [
            system_prompt,
            user_prompt,
            types.Part.from_bytes(data=image_bytes, mime_type='image/png')
        ]
        
        attempts = 100
        result = self._route_llm_call(
            model=GEMINI_MODEL,
            contents=contents,
            response_schema=DynamicSchema,
            log_prefix="DirectCloud",
            max_attempts=attempts
        )
        return result



    def detect_date_outliers(self, date_pairs: list[tuple[int, str]], prompt_template: str) -> list[int]:
        """Identify page indices whose dates are chronological outliers.
        
        Args:
            date_pairs (list[tuple[int, str]]): List of tuples containing page indices and dates.
            prompt_template (str): The instructions for LLM.
            
        Returns:
            list[int]: List of page indices identified as outliers.
        """
        from src.core.schemas import DateOutlierDetectionResult
        
        system_prompt = prompt_template
        
        # Format the input for the LLM
        pairs_str = "\n".join([f"Page {idx}: {date}" for idx, date in date_pairs])
        user_prompt = f"Identify the outlier page indices from this list:\n\n{pairs_str}"
        
        try:
            result = self._route_llm_call(
                model=GEMINI_MODEL,
                contents=[system_prompt, user_prompt],
                response_schema=DateOutlierDetectionResult,
                log_prefix="DateOutlierDetection"
            )
            return result.outlier_page_indices # type: ignore
        except Exception as e:
            log.info(f"[DateOutlierDetection] Error during LLM call: {e}")
            return []

    def check_bulk_semantic_grouping(self, pages_data: list, prompt_template: str) -> BulkSemanticMatchResult:
        """Group pages logically based on semantic content.
        
        Args:
            pages_data (list): List of page data tuples (page_number, names, summary).
            prompt_template (str): The instructions for LLM.
            
        Returns:
            BulkSemanticMatchResult: The grouping of page indices.
        """
        system_prompt = prompt_template
        user_prompt = f"Group these pages logically:\n{json.dumps(pages_data, ensure_ascii=False, indent=2)}"
        
        try:
            log.info(" Running bulk semantic grouping using Cloud Model...")
            contents = [
                system_prompt,
                user_prompt
            ]
            attempts = 100
            result = self._route_llm_call(
                model=GEMINI_MODEL,
                contents=contents,
                response_schema=BulkSemanticMatchResult,
                log_prefix="BulkSemanticCloud",
                max_attempts=attempts
            )
            return result
        except Exception as e:
            log.info(f"WARNING: Direct Cloud bulk grouping failed: {e}")
            self.activate_cooldown()
            default_groups = [[p[0]] for p in pages_data]
            return BulkSemanticMatchResult(groups=default_groups)
