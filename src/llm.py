import os
import time
import json
import threading
import logging
from google import genai
from google.genai import types

from src.schemas import PageClassification, EntityResolutionMapping

log = logging.getLogger(__name__)

class RateLimitError(Exception):
    pass

class InvalidResponseError(Exception):
    pass

class GemmaClient:
    NONE_EXPECTED_CATEGORIES = {'amar_takhsees', 'pictures', 'other_letters'}

    def __init__(self, api_keys: list[str] = None, delay_between_pages: float = 5.0):
        if not api_keys:
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("No API keys provided and GEMINI_API_KEY not found in environment.")
            self.api_keys = [key]
        else:
            self.api_keys = api_keys

        self.clients = {key: genai.Client(api_key=key) for key in self.api_keys}
        
        self.cooldown_keys = {}  # key -> release_time
        self.key_strikes = {key: 0 for key in self.api_keys}
        self.current_key_idx = 0
        
        self.delay_between_pages = delay_between_pages
        self.lock = threading.Lock()
        self.global_cooldown_until = 0.0
        self.last_request_time = 0.0

    def _get_client_and_key(self):
        while True:
            with self.lock:
                now = time.time()
                
                # Global IP Throttle: Protects against IP bans by freezing ALL threads
                if now < self.global_cooldown_until:
                    sleep_time = self.global_cooldown_until - now
                else:
                    # STRICT 2.0 SECOND GAP BETWEEN ALL API REQUESTS
                    # This prevents the "Thundering Herd" post-cooldown.
                    time_since_last = now - self.last_request_time
                    if time_since_last < 2.0:
                        sleep_time = 2.0 - time_since_last
                    else:
                        # We are allowed to proceed!
                        
                        # Reclaim keys from penalty box
                        released = [k for k, t in self.cooldown_keys.items() if now >= t]
                        for k in released:
                            del self.cooldown_keys[k]

                        # Find an available key via round-robin
                        if len(self.cooldown_keys) < len(self.api_keys):
                            for _ in range(len(self.api_keys)):
                                self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                                key = self.api_keys[self.current_key_idx]
                                if key not in self.cooldown_keys:
                                    self.last_request_time = time.time() # Update lock time
                                    return self.clients[key], key
                        
                        # If ALL keys are in cooldown, find the shortest wait time
                        earliest_release = min(self.cooldown_keys.values())
                        sleep_time = earliest_release - now
                        if sleep_time < 0.1: sleep_time = 0.5
            
            # Sleep outside the lock so other threads can do work or queue up
            print(f"[Rate Limit Guard] Staggering... Thread sleeping for {sleep_time:.1f}s...")
            time.sleep(sleep_time)

    def _report_failure(self, key: str, is_429: bool):
        with self.lock:
            self.key_strikes[key] += 1
            strikes = self.key_strikes[key]
            now = time.time()
            
            if is_429:
                # Progressive backoff for Rate Limits / Resource Exhausted
                cooldown_periods = {1: 15, 2: 30, 3: 60, 4: 120}
                penalty = cooldown_periods.get(strikes, 180)
                print(f"[Rate Limit Guard] Key penalized for {penalty}s due to 429/RateLimit (Strike {strikes}).")
                # Trigger Global IP Throttle to protect other keys and stop the thundering herd
                self.global_cooldown_until = max(self.global_cooldown_until, now + 15.0)
            else:
                # Shorter backoff for 5xx server errors to prevent thundering herds
                penalty = min(5 * strikes, 30)
                print(f"[Rate Limit Guard] Key penalized for {penalty}s due to Server Error (Strike {strikes}).")
                # Trigger Minor Global Throttle
                self.global_cooldown_until = max(self.global_cooldown_until, now + 5.0)
            
            self.cooldown_keys[key] = now + penalty

    def _report_success(self, key: str):
        with self.lock:
            if self.key_strikes[key] > 0:
                self.key_strikes[key] = 0

    def _build_system_prompt(self) -> str:
        return """You are an Arabic document classification expert analyzing scanned housing files from the Bahrain/Gulf region.

You are receiving a scanned page IMAGE. Read the page directly using your vision capabilities and classify it.

Classify this page into exactly ONE of the following 13 categories:

1. basic_details — البيانات الأساسية (Basic resident information, ID cards, civil records)
2. personal_details — البيانات الشخصية (Personal information forms, family details)
3. amar_takhsees — أمر تخصيص (Allocation orders for people assigned but not residing. CRITICAL: If the document contains the exact words 'أمر تخصيص' prominently, it MUST be classified as amar_takhsees, even if it looks like a notification.)
4. key_handover_form — نموذج تسليم المفتاح (Key handover/receipt forms)
5. contract — العقد (Rental or housing contracts)
6. ewa_related_letters — رسائل الكهرباء والماء (EWA electricity/water letters)
7. rent_deduction — خصم الإيجار (Rent deduction notices or records)
8. allowance_deduction — خصم العلاوة (Allowance deduction notices)
9. notifications — الإشعارات (General notifications, warnings. Do NOT use this for allocation orders / amar_takhsees.)
10. maintenance — الصيانة (Maintenance requests, reports, work orders)
11. pictures — الصور (Photographs of the property)
12. modifications — التعديلات (Modification requests or approvals)
13. other_letters — رسائل أخرى (Any letters that don't fit the above)

NAME EXTRACTION RULES (CRITICAL):
- Arabic names typically have 4 to 5 parts. Extract ALL parts of the name.
- If a document states a person's relationship (e.g., Wife - زوجة, Son - ابن), append it to their name in parentheses, e.g., "آمنة (زوجة)".
- If a document is addressed to MULTIPLE people, extract ALL of their names as a list of strings.
- Do NOT return an empty list or ["NONE"] unless you are absolutely certain there is no name anywhere on the page. Most documents DO contain a name.
- Only return ["NONE"] for categories where no resident is expected: amar_takhsees, pictures, or other_letters with no addressee.

DATE EXTRACTION RULES:
- Find any visible date on the document.
- Normalize the date to YYYY-MM-DD format (e.g., 2008-05-14).
- If it's a Hijri date, format as YYYY-MM-DD using the Hijri year (e.g., 1429-05-14).
- If no date is visible anywhere, return "NONE".

SPECIAL RULES:
- "basic_details" is ALWAYS just a single-page form filling out the main tenant's details.
- "personal_details" contains ID cards, civil records, passports, and family member details. Do NOT confuse basic_details with personal_details.
- For general house letters and "Amar Takhsees" documents that are NOT tied to a specific resident, set resident to "NONE".
- Normalize Arabic names intelligently: group variations like "محمد" and "المحمد" as the same person.
- Tolerate OCR noise and imperfect text in scanned documents.

Return a JSON object with: house_number, residents (list of strings), category, date."""

    def classify_page(self, image_bytes: bytes) -> PageClassification:
        system_prompt = self._build_system_prompt()
        user_prompt = "Classify this scanned document page."
        
        attempts = 0
        max_attempts = max(7, len(self.api_keys) * 2)
        
        while attempts < max_attempts:
            attempts += 1
            client, key = self._get_client_and_key()
            
            try:
                response = client.models.generate_content(
                    model='gemma-4-26b-a4b-it',
                    contents=[
                        system_prompt,
                        user_prompt,
                        types.Part.from_bytes(data=image_bytes, mime_type='image/png')
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=PageClassification,
                        temperature=0
                    )
                )

                if response.parsed is not None:
                    result = response.parsed
                else:
                    try:
                        data = json.loads(response.text)
                        result = PageClassification(**data)
                    except (json.JSONDecodeError, Exception) as parse_err:
                        raise InvalidResponseError(f"Failed to parse LLM response: {type(parse_err).__name__}")

                if ((not result.residents or result.residents == ["NONE"])
                        and result.category.value not in self.NONE_EXPECTED_CATEGORIES):
                    try:
                        retry_prompt = (
                            "Classify this scanned document page.\n\n"
                            "WARNING: You previously returned NONE for the resident name, "
                            "but this document category usually has a named person. "
                            "Look VERY carefully at every part of the page — headers, "
                            "footers, address blocks, body text, stamps, and signatures — "
                            "for any Arabic or English name. Extract the FULL name with "
                            "all 4-5 parts if possible."
                        )

                        retry_response = client.models.generate_content(
                            model='gemma-4-26b-a4b-it',
                            contents=[
                                system_prompt,
                                retry_prompt,
                                types.Part.from_bytes(data=image_bytes, mime_type='image/png')
                            ],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=PageClassification,
                                temperature=0
                            )
                        )
                        if retry_response.parsed is not None:
                            retry_result = retry_response.parsed
                        else:
                            retry_data = json.loads(retry_response.text)
                            retry_result = PageClassification(**retry_data)

                        if retry_result.residents and retry_result.residents != ["NONE"]:
                            result = retry_result
                    except Exception:
                        pass

                self._report_success(key)
                time.sleep(self.delay_between_pages)
                return result

            except Exception as e:
                error_str = str(e).lower()
                is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str
                is_invalid = "invalidresponseerror" in error_str or isinstance(e, InvalidResponseError)
                
                print(f"[Retry {attempts}/{max_attempts}] LLM call failed: {e}")
                
                if is_429 or is_5xx or is_invalid:
                    self._report_failure(key, is_429=is_429)
                    if attempts == max_attempts:
                        raise RateLimitError(f"Max retries reached. Last error: {error_str}")
                    continue
                else:
                    if attempts == max_attempts:
                        raise e
                    self._report_failure(key, is_429=False)
                    continue

    def resolve_entities(self, raw_pages_log: str) -> dict[str, str]:
        system_prompt = (
            "You are an Arabic document classification expert analyzing a chronological log of documents "
            "[Category, Name, Date] for a single house.\n\n"
            "1. Identify the Primary Tenants (Head of Household).\n"
            "2. Map all English/Arabic/abbreviated variations into one Canonical Name.\n"
            "3. Identify family members (wives, children) who appear in the log, and map them to their respective Primary Tenant.\n"
            "CRITICAL RULES:\n"
            "- You MUST return a mapping for EVERY SINGLE exact raw string found in the log, character-for-character.\n"
            "- Even OCR errors like 'آمنة الله ببة بببض' or 'زوبة' must be explicitly mapped to the Primary Tenant's canonical name if they are family.\n"
            "- ALL English transliterations (like 'MOHD SAYED IBRAHIM' or 'MOHAMMED') MUST be mapped to the primary Arabic name!\n"
            "Return the JSON mapping using the EntityResolutionMapping schema."
        )
        user_prompt = f"Here is the document log:\n{raw_pages_log}\n\nPlease resolve the entities."
        
        attempts = 0
        max_attempts = max(7, len(self.api_keys) * 2)
        
        while attempts < max_attempts:
            attempts += 1
            client, key = self._get_client_and_key()

            try:
                response = client.models.generate_content(
                    model='gemma-4-31b-it',
                    contents=[system_prompt, user_prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=EntityResolutionMapping,
                        temperature=0
                    )
                )

                if response.parsed is not None:
                    result = response.parsed
                else:
                    try:
                        data = json.loads(response.text)
                        result = EntityResolutionMapping(**data)
                    except (json.JSONDecodeError, Exception) as parse_err:
                        raise InvalidResponseError(f"Failed to parse LLM response: {type(parse_err).__name__}")

                self._report_success(key)
                time.sleep(self.delay_between_pages)
                return {item.raw_name: item.canonical_name for item in result.mapping_list}

            except Exception as e:
                error_str = str(e).lower()
                is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str
                is_invalid = "invalidresponseerror" in error_str or isinstance(e, InvalidResponseError)
                
                print(f"[Retry {attempts}/{max_attempts}] LLM resolution call failed: {e}")
                
                if is_429 or is_5xx or is_invalid:
                    self._report_failure(key, is_429=is_429)
                    if attempts == max_attempts:
                        raise RateLimitError(f"Max retries reached. Last error: {error_str}")
                    continue
                else:
                    if attempts == max_attempts:
                        raise e
                    self._report_failure(key, is_429=False)
                    continue
