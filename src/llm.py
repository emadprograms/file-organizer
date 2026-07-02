"""Core LLM orchestration and client management.

This module provides the `LLMClient` which orchestrates LLM requests across multiple
provider strategies (defined in `providers.py`). It implements resilient API routing,
error handling, rate-limit backoffs, and cloud failover for robust document processing.
"""
from src.config import record_successful_call, OPENROUTER_MODEL, GROQ_MODEL, GEMINI_MODEL
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

from src.schemas import (
    PageClassification,
    EntityResolutionMapping,
    Category,
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


from src.providers import LLMProvider, GeminiProvider, OpenRouterProvider, GroqProvider

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
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                future = executor.submit(
                    provider_obj.generate,
                    model=model,
                    contents=contents,
                    response_schema=response_schema
                )
                
                try:
                    response_parsed = future.result(timeout=300)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError("LLM API call hung and timed out after 5 minutes.")
                finally:
                    executor.shutdown(wait=False)

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

    def cluster_names(self, anchor_names: list[str], other_names: list[str]) -> dict[str, str]:
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
                for anchor in anchor_names:
                    # token_set_ratio is highly resilient to word reordering and partial OCR loss
                    if fuzz.token_set_ratio(other, anchor) > 85:
                        matched_anchor = anchor
                        break
            else:
                matches = difflib.get_close_matches(other, anchor_names, n=1, cutoff=0.85)
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
        
        system_prompt = (
            "You are an expert at entity resolution for Bahrain housing documents.\n"
            "You will be given a list of 'Official Anchor Names' and a list of 'Other Names' (which include severe OCR typos and variations in both Arabic and English).\n"
            "Your task is to match each 'Other Name' to its correct 'Official Anchor Name'.\n"
            "CRITICAL RULES:\n"
            "1. Link English names to their Arabic counterparts if they represent the same person.\n"
            "2. If an 'Other Name' clearly refers to a completely different person (e.g. an inspector), match it to 'NONE'.\n"
            "3. Output YOUR RESPONSE EXACTLY as a list of mappings in plain text format:\n"
            "Other Name -> Official Anchor Name\n\n"
            "Example Output:\n"
            "YOUNIS MOHD. MAYAN -> YOUNIS MOHAMMED MALIK\n"
            "يونس محمد -> YOUNIS MOHAMMED MALIK\n"
            "ALI HASSAN -> NONE\n\n"
            "DO NOT output JSON. DO NOT output anything else except the mappings."
        )
        
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


    def _build_system_prompt(self) -> str:
        """Build the system prompt for document classification.
        
        Constructs the detailed instructions, categories, and extraction rules
        used to prompt the LLM for page classification.
        
        Returns:
            str: The complete system prompt.
        """
        return """You are an Arabic document classification expert analyzing scanned housing files from the Bahrain/Gulf region.

You are receiving a scanned page IMAGE. Read the page directly using your vision capabilities and classify it.

CRITICAL FIRST STEP: If the image is a letter, first analyze the subject (الموضوع) of the letter or document before looking at the body text.

Classify this page into exactly ONE of the following 13 categories:

1. Basic Details Form — البيانات الأساسية (SINGLE-PERSON FORMS ONLY. Forms with fields like Name, Rank, Allotment Date (تاريخ التخصيص), and Vacation Date (تاريخ الإخلاء) for ONE person are basic_details. CRITICAL FATAL ERROR: You are STRICTLY FORBIDDEN from selecting this if the page is a roster, schedule, or table listing MULTIPLE different people's names (e.g., 'كشف بأسماء', 3+ distinct people). Multi-person rosters are NEVER basic_details. WARNING: basic_details forms may mention rent amounts; do NOT misclassify them as rent_deduction just because of a rent amount. ONLY choose this for a form containing boxes/blanks dedicated to ONE specific person.)
2. Personal Identification — البيانات الشخصية (Pictures of identity cards, passports, and other non-form documents related to the person and his family. Anything related to the person and his family that is NOT a form goes into personal details.)
3. Allocation Order — أمر تخصيص (Allocation orders. STRICT DEFINITION: A letter from a higher authority ordering to give a place to stay. FORMS OR TABLES ARE NEVER AMAR TAKHSEES. It MUST be a letter paragraph format. Strong pattern: Exact subject 'الموضوع : الوحدات السكنية' AND format is a letter.)
4. Key Handover Certificate — نموذج تسليم المفتاح (ONLY use this for the INITIAL key handover after making the contract. Do NOT use this for temporary key handovers related to maintenance. If the word 'الأشغال' (Ashgal) is present anywhere, it is NEVER key_handover_form. Strong pattern: Contains 'استمارة تسليم الوحدات السكنية التابعة لوزارة الداخلية'.)
5. Housing Contract — العقد (Rental or housing contracts. STRICT DEFINITION: If the page contains contract articles like "مادة (1)", "مادة (2)", "الطرف الأول" (First Party), "الطرف الثاني" (Second Party), or "التمهيد" (Preamble), it MUST be a contract. WARNING: Contract pages often discuss rent deduction, allowances, or eviction inside their clauses. If these topics appear as part of a contract's "مادة" or terms, you MUST classify it as a contract and NEVER as rent_deduction, allowance_deduction, or notifications.)
6. Electricity and Water — رسائل الكهرباء والماء (EWA electricity/water letters. Strong pattern: Contains a meter number, such as 'الوحدة السكنية رقم', or the terms 'electricity & water' or 'ewa' in English at the beginning of the form. WARNING: These can be forms with details filled out; do NOT misclassify them as basic_details just because they are forms.)
7. Rent Deduction Notice — خصم الإيجار (Rent deduction notices or rosters. Usually formatted as letters addressed to someone to deduct rent. STRICT DEFINITION: They ALWAYS mention deducting amounts like "30" or "60" (bd). WARNING: Contracts and basic_details forms are EXEMPT and can mention rent amounts without being rent_deduction. Do NOT classify a single-person profile form (with rank, allotment date) or a contract clause as rent_deduction just because it mentions an amount. Use the amount presence ONLY to disambiguate from allowance_deduction.)
8. Allowance Deduction Notice — خصم العلاوة (Allowance deduction notices. Strong pattern: Subject is 'الموضوع: وقف استقطاع بدل الانتفاع'. Will NOT have "30 bd" or "60 bd" written on it.)
9. General Notifications — الإشعارات (General notifications, warnings, and ANY documents regarding vacating the house/eviction. STRICT DEFINITION: If the document mentions the tenant vacating the house (إخلاء), refusing to vacate, extensions for vacating, or any similar eviction terms, it MUST be notifications. Also includes 'إشعار' or 'اشعار'. Do NOT put eviction/vacating notices in other_letters. Do NOT use this for allocation orders.)
10. Maintenance Records — الصيانة (Maintenance requests, reports, work orders. STRICT RULE: If the word 'الأشغال' (Ashgal) is written ANYWHERE on the document, it MUST be maintenance. Even if it looks like a key handover form, if 'الأشغال' is present, it goes to maintenance. Do NOT put inspection notices or reports here.)
11. Inspection and Pictures — التفتيش والصور (Notices of inspection, inspection reports, house visits, yellow papers with inspection details, and photographs of the property. ANY letters or reports regarding inspection MUST go here, NOT to maintenance.)
12. Property Modifications — التعديلات (Modification requests or approvals. Strong pattern: Subject contains 'طلب' (talab) and mentions modifying the house.)
13. Miscellaneous Letters — رسائل أخرى (Any letters that don't fit the above. Also use this for generic multi-person rosters like 'كشف بأسماء' that do not clearly belong to another category.)

NAME EXTRACTION RULES (CRITICAL):
- Arabic names typically have 4 to 5 parts. Extract ALL parts of the name.
- If a document states a person's relationship (e.g., Wife - زوجة, Son - ابن), append it to their name in parentheses, e.g., "آمنة (زوجة)".
- If a document is addressed to MULTIPLE people, extract ALL of their names as a list of strings.
- Do NOT return an empty list or ["NONE"] unless you are absolutely certain there is no name anywhere on the page. Most documents DO contain a name.
- Only return ["NONE"] for categories where no resident is expected: Allocation Order, Inspection and Pictures, or Miscellaneous Letters with no addressee.

DATE EXTRACTION RULES:
- Find any visible date on the document.
- Normalize the date to YYYY-MM-DD format (e.g., 2008-05-14).
- FATAL RULE: You are STRICTLY FORBIDDEN from extracting Hijri dates (e.g., 1445 AH). ONLY extract Gregorian dates. Ignore Hijri dates even if both exist.
- If no Gregorian date is visible anywhere, return "NONE".

SPECIAL RULES:
- Normalize Arabic names intelligently: group variations like "محمد" and "المحمد" as the same person.
- Tolerate OCR noise and imperfect text in scanned documents.

Return a JSON object with: residents (list of strings), category, date, and summary (string)."""


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
            
        DynamicSchema = create_model('DynamicClassification', **model_fields)

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



    def detect_date_outliers(self, date_pairs: list[tuple[int, str]]) -> list[int]:
        """Identify page indices whose dates are chronological outliers.
        
        Args:
            date_pairs (list[tuple[int, str]]): List of tuples containing page indices and dates.
            
        Returns:
            list[int]: List of page indices identified as outliers.
        """
        from src.schemas import DateOutlierDetectionResult
        
        system_prompt = (
            "You are a chronological analysis expert. You will be given a list of page indices and their associated dates "
            "from a single document. Your task is to identify which dates are 'outliers'—meaning they do not belong to the "
            "primary chronological timeline of the document (e.g., a birth date from 1980 appearing in a document from 2024).\n\n"
            "CRITICAL RULES:\n"
            "1. Look for the main chronological 'chapters' of the document.\n"
            "2. A date is an outlier if it clearly belongs to a different life stage or event era than the rest of the sequence.\n"
            "3. Do NOT flag dates that show natural progression (e.g., 2021, 2022, 2023).\n"
            "4. Return ONLY a JSON object containing the 'outlier_page_indices' list."
        )
        
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

    def check_bulk_semantic_grouping(self, pages_data: list) -> BulkSemanticMatchResult:
        """Group pages logically based on semantic content.
        
        Args:
            pages_data (list): List of page data tuples (page_number, names, summary).
            
        Returns:
            BulkSemanticMatchResult: The grouping of page indices.
        """
        system_prompt = (
            "You are an expert document organizer analyzing a sequence of pages from a single property file.\n\n"
            "CRITICAL RULES:\n"
            "1. You will be provided with an array of pages. Each page has [page_number, extracted_names, page_summary].\n"
            "2. Group consecutive pages together ONLY if they semantically belong to the exact same document/event.\n"
            "3. If a page starts a new document or a completely different topic, it belongs in a new group.\n"
            "4. A document can span multiple consecutive pages (e.g., a 5-page contract).\n"
            "5. Return a JSON object with a 'groups' field containing a list of lists of page numbers.\n"
        )
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
