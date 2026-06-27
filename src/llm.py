from src.config import record_successful_call
import concurrent.futures
import os
import time
import json
from typing import Optional, Any, Deque

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
    pass

class InvalidResponseError(Exception):
    pass

class GemmaClient:
    def __init__(self, api_key: str, delay_between_pages: float = 5.0) -> None:
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("No API key provided and GEMINI_API_KEY not found in environment.")
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key)
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_client = openai.Client(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1") if openrouter_key else None
        
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_client = openai.Client(api_key=groq_key, base_url="https://api.groq.com/openai/v1") if groq_key else None

        self.delay_between_pages = delay_between_pages
        self.total_requests = 0

    def activate_cooldown(self) -> None:
        time.sleep(65)

    def _route_llm_call(self, model: str, contents: list, response_schema: type, log_prefix: str = "Retry", max_attempts: Optional[int] = None) -> Any:
        from src.config import OPENROUTER_MODEL, GROQ_MODEL
        providers = ["gemini"]
        if self.openrouter_client is not None:
            providers.append("openrouter")
        if self.groq_client is not None:
            providers.append("groq")
        current_provider_idx = 0
        provider_attempts = 0
        
        while current_provider_idx < len(providers):
            provider = providers[current_provider_idx]
            provider_attempts += 1
            
            start_time = time.time()
            try:
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                
                if provider == "gemini":
                    future = executor.submit(
                        self.client.models.generate_content,
                        model=model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=response_schema,
                            temperature=0
                        )
                    )
                else:
                    prompt_content = []
                    for part in contents:
                        if isinstance(part, str):
                            prompt_content.append({"type": "text", "text": part})
                        elif hasattr(part, "data") and hasattr(part, "mime_type"):
                            b64 = base64.b64encode(part.data).decode("utf-8")
                            prompt_content.append({"type": "image_url", "image_url": {"url": f"data:{part.mime_type};base64,{b64}"}})  # type: ignore
                    messages = [{"role": "user", "content": prompt_content}]
                    
                    if provider == "openrouter":
                        client = self.openrouter_client
                        fallback_model = OPENROUTER_MODEL
                    else:
                        client = self.groq_client
                        fallback_model = GROQ_MODEL
                        
                    future = executor.submit(
                        client.chat.completions.create,  # type: ignore
                        model=fallback_model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0
                    )
                    
                try:
                    response = future.result(timeout=90)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError("LLM API call hung and timed out after 90 seconds.")
                finally:
                    executor.shutdown(wait=False)

                record_successful_call()
                self.total_requests += 1

                elapsed = time.time() - start_time
                if elapsed < 7.0:
                    time.sleep(7.0 - elapsed)
                
                if provider == "gemini":
                    if response.parsed is not None:
                        return response.parsed
                    text = response.text.strip()  # type: ignore
                else:
                    text = response.choices[0].message.content.strip()  # type: ignore
                    
                json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
                if json_match:
                    text = json_match.group(1)
                data = json.loads(text)
                return response_schema(**data)

            except Exception as e:
                error_str = str(e).lower()
                is_auth = "401" in error_str or "403" in error_str or "400" in error_str or "api key not valid" in error_str or "invalid_api_key" in error_str
                is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str or "timeout" in error_str
                
                log.info(f"[{log_prefix} - {provider} attempt {provider_attempts}] LLM call failed: {e}")
                
                if is_auth:
                    log.info(f"[{log_prefix}] Auth/Bad Request error on {provider}: fail fast. Error: {e}")
                    raise e
                    
                if is_429:
                    if provider_attempts >= 3:
                        current_provider_idx += 1
                        provider_attempts = 0
                        if current_provider_idx < len(providers):
                            next_prov = providers[current_provider_idx]
                            next_name = "OpenRouter" if next_prov == "openrouter" else "Groq"
                            log.info(f"[Cloud Fallback] Failed over to {next_name}")
                        continue
                    log.info(f"[{log_prefix}] 429 Error on {provider}. Sleeping for 65 seconds.")
                    time.sleep(65)
                    continue
                    
                if is_5xx or isinstance(e, TimeoutError):
                    current_provider_idx += 1
                    provider_attempts = 0
                    if current_provider_idx < len(providers):
                        next_prov = providers[current_provider_idx]
                        next_name = "OpenRouter" if next_prov == "openrouter" else "Groq"
                        log.info(f"[Cloud Fallback] Failed over to {next_name}")
                    continue
                
                if provider_attempts >= 3:
                    current_provider_idx += 1
                    provider_attempts = 0
                    if current_provider_idx < len(providers):
                        next_prov = providers[current_provider_idx]
                        next_name = "OpenRouter" if next_prov == "openrouter" else "Groq"
                        log.info(f"[Cloud Fallback] Failed over to {next_name}")
                    continue
                time.sleep(7.5)
                continue

        raise RuntimeError("LLM routing failed across all providers")

    def cluster_names(self, unique_names: list[str]) -> dict[str, str]:
        """
        Takes a list of unique names and asks the LLM to group them into canonical identities.
        Returns a mapping of {ORIGINAL_NAME: CANONICAL_NAME} (uppercase stripped).
        """
        if not unique_names:
            return {}
            
        system_prompt = "You are an expert at resolving Arabic and English name variations. Your task is to map multiple variations, misspellings, or abbreviations of the same name to a single 'canonical' identity."
        
        import json
        user_prompt = f"""Given the following list of unique names extracted from a file, some are variations or misspellings of the exact same person.
        
List of names:
{json.dumps(unique_names, ensure_ascii=False)}

Group the names that refer to the same person. Pick the most complete, correctly spelled version of the name as the 'canonical_name'.
For any name that does not have variations, map it to itself.
Return the mapping_list with each original raw_name and its resolved canonical_name.
"""
        from src.schemas import EntityResolutionMapping
        
        contents = [
            system_prompt,
            user_prompt
        ]
        
        try:
            result = self._route_llm_call(
                model="gemini-2.5-flash",
                contents=contents,
                response_schema=EntityResolutionMapping,
                log_prefix="Name Clustering",
                max_attempts=3
            )
        except Exception as e:
            log.info(f"[Name Clustering] Failed to cluster names using LLM: {e}")
            result = None
            
        # Fallback to self-mapping
        mapping = {n.upper().strip(): n.upper().strip() for n in unique_names}
        
        if result and hasattr(result, "mapping_list"): # type: ignore
            for item in result.mapping_list:
                raw = item.raw_name.upper().strip()
                canonical = item.canonical_name.upper().strip()
                if raw in mapping:
                    mapping[raw] = canonical
                    
        return mapping

    def _build_system_prompt(self) -> str:
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


    def classify_page_direct(self, image_bytes: bytes, extracted_footer: Optional[str] = None) -> PageClassification:
        system_prompt = self._build_system_prompt()
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
            model='gemma-4-31b-it',
            contents=contents,
            response_schema=PageClassification,
            log_prefix="DirectCloud",
            max_attempts=attempts
        )
        return result



    def detect_date_outliers(self, date_pairs: list[tuple[int, str]]) -> list[int]:
        """
        Uses the LLM to identify page indices whose dates are chronological outliers.
        Returns a list of outlier page indices.
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
                model='gemma-4-31b-it',
                contents=[system_prompt, user_prompt],
                response_schema=DateOutlierDetectionResult,
                log_prefix="DateOutlierDetection"
            )
            return result.outlier_page_indices # type: ignore
        except Exception as e:
            log.info(f"[DateOutlierDetection] Error during LLM call: {e}")
            return []

    def check_bulk_semantic_grouping(self, pages_data: list) -> BulkSemanticMatchResult:
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
                model='gemma-4-31b-it',
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



