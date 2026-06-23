import os
import time
import json
import random
import threading
import logging
from collections import deque
from google import genai
from google.genai import types

from src.schemas import PageClassification, EntityResolutionMapping

log = logging.getLogger(__name__)

# Telemetry Logger setup
telemetry_logger = logging.getLogger("telemetry")
telemetry_logger.setLevel(logging.INFO)
# Ensure we don't duplicate handlers
if not telemetry_logger.handlers:
    fh = logging.FileHandler("telemetry.log", encoding="utf-8")
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            return json.dumps(record.msg)
    fh.setFormatter(JsonFormatter())
    telemetry_logger.addHandler(fh)

class LLMFailureError(Exception):
    pass

class InvalidResponseError(Exception):
    pass

class GemmaClient:
    NONE_EXPECTED_CATEGORIES = {'amar_takhsees', 'pictures', 'other_letters'}
    GLOBAL_RPM_LIMIT = 15
    TPM_LIMIT = 30000
    RPM_LIMIT = 30

    def __init__(self, api_keys: list[str] = None, delay_between_pages: float = 5.0, telemetry_queue=None):
        if not api_keys:
            keys_str = os.getenv("GEMINI_API_KEYS")
            if not keys_str:
                raise ValueError("No API keys provided and GEMINI_API_KEYS not found in environment.")
            self.api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
            if not self.api_keys:
                raise ValueError("GEMINI_API_KEYS environment variable is empty or invalid.")
        else:
            self.api_keys = api_keys

        self.clients = {key: genai.Client(api_key=key) for key in self.api_keys}
        
        self.cooldown_keys = {}  # key -> release_time
        self.key_strikes = {key: 0 for key in self.api_keys}
        self.current_key_idx = 0
        
        self.delay_between_pages = delay_between_pages
        self.lock = threading.Lock()
        self.global_cooldown_until = 0.0
        self.last_request_time = {key: 0.0 for key in self.api_keys}
        
        # Trackers
        self.global_rpm_tracker = deque()
        self.tpm_trackers = {key: deque() for key in self.api_keys}
        self.rpm_trackers = {key: deque() for key in self.api_keys}
        
        self.telemetry_queue = telemetry_queue
        self.total_requests = {key: 0 for key in self.api_keys}

    def _push_telemetry(self):
        if self.telemetry_queue:
            state = {
                "keys": []
            }
            now = time.time()
            for i, key in enumerate(self.api_keys):
                tpm = sum(cost for t, cost in self.tpm_trackers[key] if now - t <= 60)
                rpm = sum(1 for t in self.rpm_trackers[key] if now - t <= 60)
                status = "Active"
                if key in self.cooldown_keys and self.cooldown_keys[key] > now:
                    status = f"Cooldown ({int(self.cooldown_keys[key] - now)}s)"
                state["keys"].append({
                    "id": f"Key_{i}",
                    "total_reqs": self.total_requests[key],
                    "rpm": rpm,
                    "tpm": tpm,
                    "strikes": self.key_strikes[key],
                    "status": status
                })
            self.telemetry_queue.put(state)

    def _prune_trackers(self, key: str, now: float):
        while self.tpm_trackers[key] and now - self.tpm_trackers[key][0][0] > 60:
            self.tpm_trackers[key].popleft()
        while self.rpm_trackers[key] and now - self.rpm_trackers[key][0] > 60:
            self.rpm_trackers[key].popleft()

    def _get_client_and_key(self, estimated_tokens: int = 3000):
        while True:
            sleep_time = 0.0
            with self.lock:
                now = time.time()
                
                while self.global_rpm_tracker and now - self.global_rpm_tracker[0] > 60:
                    self.global_rpm_tracker.popleft()
                
                # Global IP Throttle
                if now < self.global_cooldown_until:
                    sleep_time = self.global_cooldown_until - now
                elif len(self.global_rpm_tracker) >= self.GLOBAL_RPM_LIMIT:
                    sleep_time = self.global_rpm_tracker[0] + 60 - now
                else:
                    released = [k for k, t in self.cooldown_keys.items() if now >= t]
                    for k in released:
                        del self.cooldown_keys[k]

                    available_keys = []
                    for key in self.api_keys:
                        if key not in self.cooldown_keys:
                            self._prune_trackers(key, now)
                            current_tpm = sum(cost for t, cost in self.tpm_trackers[key])
                            current_rpm = len(self.rpm_trackers[key])
                            
                            if current_tpm + estimated_tokens >= self.TPM_LIMIT or current_rpm + 1 >= self.RPM_LIMIT:
                                # Need cooldown. Calculate when oldest token falls off
                                if self.tpm_trackers[key] and current_tpm + estimated_tokens >= self.TPM_LIMIT:
                                    oldest_time = self.tpm_trackers[key][0][0]
                                    self.cooldown_keys[key] = oldest_time + 60
                                elif self.rpm_trackers[key]:
                                    oldest_time = self.rpm_trackers[key][0]
                                    self.cooldown_keys[key] = oldest_time + 60
                            elif now - self.last_request_time[key] < 1.0:
                                # Per-key stagger to prevent API bursting
                                pass
                            else:
                                available_keys.append(key)

                    if available_keys:
                        # Pick next available via round-robin
                        for _ in range(len(self.api_keys)):
                            self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                            key = self.api_keys[self.current_key_idx]
                            if key in available_keys:
                                self.last_global_request_time = time.time()
                                self.last_request_time[key] = self.last_global_request_time
                                self.tpm_trackers[key].append([self.last_request_time[key], estimated_tokens])
                                self.rpm_trackers[key].append(self.last_request_time[key])
                                self.global_rpm_tracker.append(self.last_request_time[key])
                                self.total_requests[key] += 1
                                self._push_telemetry()
                                return self.clients[key], key, self.last_request_time[key]
                        
                    # If ALL keys are in cooldown
                    if not sleep_time:
                        if self.cooldown_keys:
                            earliest_release = min(self.cooldown_keys.values())
                            if earliest_release == float('inf'):
                                raise RuntimeError("All API keys exhausted permanently")
                            sleep_time = earliest_release - now
                        else:
                            sleep_time = 1.0 # Should not happen if everything is calculated right

            if sleep_time > 0:
                if sleep_time < 0.1: sleep_time = 0.5
                print(f"[Rate Limit Guard] Staggering... Thread sleeping for {sleep_time:.1f}s...")
                time.sleep(sleep_time)

    def _reconcile_usage(self, key: str, reserve_time: float, actual_tokens: int):
        with self.lock:
            for item in self.tpm_trackers[key]:
                if item[0] == reserve_time:
                    item[1] = actual_tokens
                    break
            self._push_telemetry()

    def _report_failure(self, key: str, is_429: bool, is_token_limit: bool = False):
        with self.lock:
            self.key_strikes[key] += 1
            strikes = self.key_strikes[key]
            now = time.time()
            
            if strikes >= 10:
                telemetry_logger.critical({
                    "timestamp": now,
                    "key_index": self.api_keys.index(key),
                    "status_code": 429 if is_429 else 500,
                    "error_type": "key_exhausted"
                })
                print(f"[Rate Limit Guard] Key permanently exhausted (Strike {strikes}).")
                self.cooldown_keys[key] = float('inf')
                self._push_telemetry()
                return

            base_penalty = min(15 * (2 ** (strikes - 1)), 300)
            penalty = base_penalty * (0.5 + random.random())
            
            if is_429:
                if is_token_limit:
                    print(f"[Rate Limit Guard] Key penalized for {penalty:.1f}s due to Token Limit (Strike {strikes}).")
                else:
                    print(f"[Rate Limit Guard] Key penalized for {penalty:.1f}s due to 429/RequestLimit (Strike {strikes}).")
            else:
                print(f"[Rate Limit Guard] Key penalized for {penalty:.1f}s due to Server Error (Strike {strikes}).")
                
            self.global_cooldown_until = max(self.global_cooldown_until, now + penalty)
            self.cooldown_keys[key] = now + penalty
            self._push_telemetry()

    def _report_success(self, key: str):
        with self.lock:
            if self.key_strikes[key] > 0:
                self.key_strikes[key] = 0
            self._push_telemetry()

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
        invalid_retries = 0
        
        while attempts < max_attempts:
            attempts += 1
            client, key, reserve_time = self._get_client_and_key(estimated_tokens=3000)
            start_time = time.time()
            used_tokens = 0
            
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

                latency_ms = int((time.time() - start_time) * 1000)
                used_tokens = 3000
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    used_tokens = response.usage_metadata.total_token_count
                
                self._reconcile_usage(key, reserve_time, used_tokens)
                
                if response.parsed is not None:
                    result = response.parsed
                else:
                    try:
                        data = json.loads(response.text)
                        result = PageClassification(**data)
                    except (json.JSONDecodeError, Exception) as parse_err:
                        raw_preview = ""
                        try:
                            if hasattr(response, "text") and response.text:
                                raw_preview = response.text[:200]
                            elif hasattr(response, "candidates") and response.candidates and response.candidates[0].finish_reason:
                                raw_preview = f"<Finish reason: {response.candidates[0].finish_reason}>"
                        except ValueError:
                            raw_preview = "<ValueError reading response.text>"
                        
                        print(f"JSON PARSE ERROR (classify). Raw text preview: {raw_preview}")
                        raise InvalidResponseError(raw_preview)

                telemetry_logger.info({
                    "timestamp": time.time(),
                    "key_index": self.api_keys.index(key),
                    "latency_ms": latency_ms,
                    "tokens_used": used_tokens,
                    "status_code": 200,
                    "error_type": "none"
                })

                if ((not result.residents or result.residents == ["NONE"])
                        and result.category.value not in self.NONE_EXPECTED_CATEGORIES):
                    retry_prompt = (
                        "Classify this scanned document page.\n\n"
                        "WARNING: You previously returned NONE for the resident name, "
                        "but this document category usually has a named person. "
                        "Look VERY carefully at every part of the page — headers, "
                        "footers, address blocks, body text, stamps, and signatures — "
                        "for any Arabic or English name. Extract the FULL name with "
                        "all 4-5 parts if possible."
                    )
                    
                    retry_client, retry_key, retry_reserve_time = self._get_client_and_key(estimated_tokens=3000)
                    retry_start = time.time()
                    try:
                        retry_response = retry_client.models.generate_content(
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
                        retry_used_tokens = 3000
                        if hasattr(retry_response, "usage_metadata") and retry_response.usage_metadata:
                            retry_used_tokens = retry_response.usage_metadata.total_token_count
                            
                        self._reconcile_usage(retry_key, retry_reserve_time, retry_used_tokens)
                        
                        telemetry_logger.info({
                            "timestamp": time.time(),
                            "key_index": self.api_keys.index(retry_key),
                            "latency_ms": int((time.time() - retry_start) * 1000),
                            "tokens_used": retry_used_tokens,
                            "status_code": 200,
                            "error_type": "none"
                        })

                        if retry_response.parsed is not None:
                            retry_result = retry_response.parsed
                        else:
                            retry_data = json.loads(retry_response.text)
                            retry_result = PageClassification(**retry_data)

                        if retry_result.residents and retry_result.residents != ["NONE"]:
                            result = retry_result
                            
                        self._report_success(retry_key)
                    except Exception as e:
                        error_str = str(e).lower()
                        is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                        is_token_limit = "token" in error_str and is_429
                        is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str
                        is_invalid = "invalidresponseerror" in error_str or isinstance(e, InvalidResponseError)
                        
                        error_type = "unknown"
                        if is_429:
                            error_type = "token_limit" if is_token_limit else "request_limit"
                        elif is_5xx:
                            error_type = "server_error"
                        elif is_invalid:
                            error_type = "invalid_response"
                        
                        telemetry_logger.error({
                            "timestamp": time.time(),
                            "key_index": self.api_keys.index(retry_key),
                            "latency_ms": int((time.time() - retry_start) * 1000),
                            "tokens_used": 0,
                            "status_code": 429 if is_429 else (500 if is_5xx else 400),
                            "error_type": error_type
                        })
                        
                        if is_429 or is_5xx or is_invalid:
                            self._report_failure(retry_key, is_429=is_429, is_token_limit=is_token_limit)
                        else:
                            self._report_failure(retry_key, is_429=False)

                self._report_success(key)
                return result

            except Exception as e:
                error_str = str(e).lower()
                is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                is_token_limit = "token" in error_str and is_429
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str
                is_invalid = "invalidresponseerror" in error_str or isinstance(e, InvalidResponseError)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                error_type = "unknown"
                if is_429:
                    error_type = "token_limit" if is_token_limit else "request_limit"
                elif is_5xx:
                    error_type = "server_error"
                elif is_invalid:
                    error_type = "model_refusal"
                
                raw_preview = str(e) if is_invalid else ""
                
                log_payload = {
                    "timestamp": time.time(),
                    "key_index": self.api_keys.index(key),
                    "latency_ms": latency_ms,
                    "tokens_used": used_tokens if is_invalid else 0,
                    "status_code": 429 if is_429 else (500 if is_5xx else 400),
                    "error_type": error_type
                }
                if is_invalid:
                    log_payload["raw_preview"] = raw_preview
                    
                telemetry_logger.error(log_payload)
                
                print(f"[Retry {attempts}/{max_attempts}] LLM call failed: {e}")
                
                if is_invalid:
                    invalid_retries += 1
                    if invalid_retries >= 2:
                        telemetry_logger.info({
                            "timestamp": time.time(),
                            "key_index": self.api_keys.index(key),
                            "latency_ms": latency_ms,
                            "tokens_used": 0,
                            "status_code": 200,
                            "error_type": "fallback_classification"
                        })
                        return PageClassification(
                            category=Category.OTHER_LETTERS,
                            residents=["NONE"],
                            date="NONE",
                            house_number="UNKNOWN"
                        )
                
                if is_429 or is_5xx or is_invalid:
                    self._report_failure(key, is_429=is_429, is_token_limit=is_token_limit)
                    if attempts == max_attempts:
                        raise LLMFailureError(f"Max retries reached. Last error: {error_str}")
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
            "- You MUST return a mapping for EVERY UNIQUE exact raw string found in the log, character-for-character.\n"
            "- Do NOT output duplicate mappings for the same raw string. Output the JSON mapping once per UNIQUE raw name.\n"
            "- Even OCR errors like 'آمنة الله ببة بببض' or 'زوبة' must be explicitly mapped to the Primary Tenant's canonical name if they are family.\n"
            "- ALL English transliterations (like 'MOHD SAYED IBRAHIM' or 'MOHAMMED') MUST be mapped to the primary Arabic name!\n"
            "Return the JSON mapping using the EntityResolutionMapping schema."
        )
        user_prompt = f"Here is the document log:\n{raw_pages_log}\n\nPlease resolve the entities."
        
        attempts = 0
        max_attempts = max(7, len(self.api_keys) * 2)
        
        while attempts < max_attempts:
            attempts += 1
            client, key, reserve_time = self._get_client_and_key(estimated_tokens=5000)
            start_time = time.time()

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
                
                latency_ms = int((time.time() - start_time) * 1000)
                used_tokens = 5000
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    used_tokens = response.usage_metadata.total_token_count
                
                self._reconcile_usage(key, reserve_time, used_tokens)
                
                telemetry_logger.info({
                    "timestamp": time.time(),
                    "key_index": self.api_keys.index(key),
                    "latency_ms": latency_ms,
                    "tokens_used": used_tokens,
                    "status_code": 200,
                    "error_type": "none"
                })

                if response.parsed is not None:
                    result = response.parsed
                else:
                    try:
                        data = json.loads(response.text)
                        result = EntityResolutionMapping(**data)
                    except (json.JSONDecodeError, Exception) as parse_err:
                        print(f"JSON PARSE ERROR (resolve_entities). Raw text was: {response.text}")
                        raise InvalidResponseError(f"Failed to parse LLM response: {type(parse_err).__name__}")

                self._report_success(key)
                return {item.raw_name: item.canonical_name for item in result.mapping_list}

            except Exception as e:
                error_str = str(e).lower()
                is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                is_token_limit = "token" in error_str and is_429
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str
                is_invalid = "invalidresponseerror" in error_str or isinstance(e, InvalidResponseError)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                error_type = "unknown"
                if is_429:
                    error_type = "token_limit" if is_token_limit else "request_limit"
                elif is_5xx:
                    error_type = "server_error"
                elif is_invalid:
                    error_type = "invalid_response"
                
                telemetry_logger.error({
                    "timestamp": time.time(),
                    "key_index": self.api_keys.index(key),
                    "latency_ms": latency_ms,
                    "tokens_used": 0,
                    "status_code": 429 if is_429 else (500 if is_5xx else 400),
                    "error_type": error_type
                })
                
                print(f"[Retry {attempts}/{max_attempts}] LLM resolution call failed: {e}")
                
                if is_429 or is_5xx or is_invalid:
                    self._report_failure(key, is_429=is_429, is_token_limit=is_token_limit)
                    if attempts == max_attempts:
                        raise LLMFailureError(f"Max retries reached. Last error: {error_str}")
                    continue
                else:
                    if attempts == max_attempts:
                        raise e
                    self._report_failure(key, is_429=False)
                    continue
