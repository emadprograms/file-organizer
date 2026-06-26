import concurrent.futures
import os
import time
import json
from typing import Optional, Any, Dict, List, Deque

import re
import random
import threading
import logging
import base64
import openai
from collections import deque
from google import genai
from google.genai import types

from src.schemas import (
    PageClassification,
    EntityResolutionMapping,
    Category,
    BulkSemanticMatchResult,
    DateOutlierDetectionResult
)

log = logging.getLogger(__name__)

# Telemetry Logger setup
telemetry_logger = logging.getLogger("telemetry")
telemetry_logger.setLevel(logging.INFO)
# Ensure we don't duplicate handlers
if not telemetry_logger.handlers:
    fh = logging.FileHandler("telemetry.log", encoding="utf-8")
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            return json.dumps(record.msg)
    fh.setFormatter(JsonFormatter())
    telemetry_logger.addHandler(fh)

class LLMFailureError(Exception):
    pass

class InvalidResponseError(Exception):
    pass

class GemmaClient:

    TPM_LIMIT = 30000
    RPM_LIMIT = 5
    
    global_rpm_tracker: deque[float] = deque()
    global_cooldown_until = 0.0

    def __init__(self, api_keys: Optional[list[str]] = None, delay_between_pages: float = 5.0, telemetry_queue: Any = None, use_local_llm: bool = True) -> None:
        self.use_local_llm = use_local_llm
        if not api_keys:
            keys_str = os.getenv("GEMINI_API_KEYS")
            if not keys_str:
                raise ValueError("No API keys provided and GEMINI_API_KEYS not found in environment.")
            self.api_keys = [k.strip() for k in keys_str.split(',') if k.strip()]
            if not self.api_keys:
                raise ValueError("GEMINI_API_KEYS environment variable is empty or invalid.")
        else:
            self.api_keys = api_keys

        self.global_rpm_limit = 15
        self.clients = {key: genai.Client(api_key=key) for key in self.api_keys}
        
        self.cooldown_keys: dict[str, float] = {}  # key -> release_time
        self.key_strikes = {key: 0 for key in self.api_keys}
        self.current_key_idx = 0
        
        self.delay_between_pages = delay_between_pages
        self.lock = threading.Lock()
        self.last_request_time = {key: 0.0 for key in self.api_keys}
        
        # Trackers
        self.tpm_trackers: dict[str, deque[list[Any]]] = {key: deque() for key in self.api_keys}
        self.rpm_trackers: dict[str, deque[float]] = {key: deque() for key in self.api_keys}
        
        self.telemetry_queue = telemetry_queue
        self.total_requests = {key: 0 for key in self.api_keys}

        local_base_url = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
        self.local_client = openai.OpenAI(base_url=local_base_url, api_key="ollama")

        state_file = ".rate_limit_state.json"
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    GemmaClient.global_rpm_tracker = deque(state.get("global_rpm_tracker", []))
                    GemmaClient.global_cooldown_until = state.get("global_cooldown_until", 0.0)
            except Exception:
                pass

    def should_use_local_fallback(self) -> bool:
        if not self.use_local_llm:
            return False
        with self.lock:
            now = time.time()
            while GemmaClient.global_rpm_tracker and now - GemmaClient.global_rpm_tracker[0] > 65.0:
                GemmaClient.global_rpm_tracker.popleft()
            
            if now < GemmaClient.global_cooldown_until:
                return True
            if len(GemmaClient.global_rpm_tracker) >= self.global_rpm_limit:
                return True
            return False

    def activate_cooldown(self) -> None:
        with self.lock:
            now = time.time()
            GemmaClient.global_cooldown_until = max(GemmaClient.global_cooldown_until, now + 65.0)
            self._save_state()
            self._push_telemetry()

    def _save_state(self) -> None:
        state = {
            "global_rpm_tracker": list(GemmaClient.global_rpm_tracker),
            "global_cooldown_until": GemmaClient.global_cooldown_until
        }
        try:
            with open(".rate_limit_state.json", "w") as f:
                json.dump(state, f)
        except Exception:
            pass

    def _push_telemetry(self) -> None:
        if self.telemetry_queue:
            state: dict[str, list[dict[str, Any]]] = {
                "keys": []
            }
            now = time.time()
            for i, key in enumerate(self.api_keys):
                tpm = sum(cost for t, cost in self.tpm_trackers[key] if now - t <= 60)
                rpm = sum(1 for t in self.rpm_trackers[key] if now - t <= 60)
                status = "Active"
                if key in self.cooldown_keys and self.cooldown_keys[key] > now:
                    if self.cooldown_keys[key] == float('inf'):
                        status = "Exhausted"
                    else:
                        status = f"Cooldown ({int(self.cooldown_keys[key] - now)}s)"
                state["keys"].append({
                    "id": f"Key_{i}",
                    "total_reqs": self.total_requests[key],
                    "rpm": rpm,
                    "tpm": tpm,
                    "strikes": self.key_strikes[key],
                    "status": status
                })
            try:
                self.telemetry_queue.put(state, block=False)
            except Exception:
                pass

    def _prune_trackers(self, key: str, now: float) -> None:
        while self.tpm_trackers[key] and now - self.tpm_trackers[key][0][0] > 60:
            self.tpm_trackers[key].popleft()
        while self.rpm_trackers[key] and now - self.rpm_trackers[key][0] > 60:
            self.rpm_trackers[key].popleft()

    def _get_client_and_key(self, estimated_tokens: int = 3000, no_wait: bool = False):
        while True:
            sleep_time = 0.0
            with self.lock:
                now = time.time()
                
                while GemmaClient.global_rpm_tracker and now - GemmaClient.global_rpm_tracker[0] > 65.0:
                    GemmaClient.global_rpm_tracker.popleft()
                
                # Global IP Throttle
                if now < GemmaClient.global_cooldown_until:
                    sleep_time = GemmaClient.global_cooldown_until - now
                elif len(GemmaClient.global_rpm_tracker) >= self.global_rpm_limit:
                    sleep_time = GemmaClient.global_rpm_tracker[0] + 65.0 - now
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
                                GemmaClient.global_rpm_tracker.append(self.last_request_time[key])
                                self._save_state()
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
                if no_wait:
                    return None
                if sleep_time < 0.1: sleep_time = 0.5
                print(f"[Rate Limit Guard] Staggering... Thread sleeping for {sleep_time:.1f}s...")
                time.sleep(sleep_time)

    def _reconcile_usage(self, key: str, reserve_time: float, actual_tokens: int) -> None:
        with self.lock:
            for item in self.tpm_trackers[key]:
                if item[0] == reserve_time:
                    item[1] = actual_tokens
                    break
            self._push_telemetry()

    def _report_failure(self, key: str, is_429: bool, is_token_limit: bool = False) -> None:
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
                
            if is_429:
                # Task 3: explicit cooldown state tracking
                penalty = max(penalty, 65.0) 
            
            self.cooldown_keys[key] = now + penalty
            # CRITICAL FIX: Google tracks the IP for all errors (429s, 503s, Timeouts).
            # We must enforce the penalty globally to let the IP flush before picking the next key.
            GemmaClient.global_cooldown_until = max(GemmaClient.global_cooldown_until, now + penalty)
            self._save_state()
            self._push_telemetry()

    def _report_success(self, key: str) -> None:
        with self.lock:
            if self.key_strikes[key] > 0:
                self.key_strikes[key] = 0
            self._push_telemetry()

    def _route_llm_call(self, model: str, contents: list, response_schema: type, log_prefix: str = "Retry", max_attempts: Optional[int] = None) -> Any:
        attempts = 0
        if max_attempts is None:
            max_attempts = max(7, len(self.api_keys) * 2)
        invalid_retries = 0
        
        while attempts < max_attempts:
            attempts += 1
            client, key, reserve_time = self._get_client_and_key(estimated_tokens=3000)
            start_time = time.time()
            used_tokens = 0
            
            try:
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                future = executor.submit(
                    client.models.generate_content,
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0
                    )
                )
                try:
                    response = future.result(timeout=90)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError("LLM API call hung and timed out after 90 seconds.")
                finally:
                    # Do not wait for the hung thread
                    executor.shutdown(wait=False)

                latency_ms = int((time.time() - start_time) * 1000)
                used_tokens = 3000
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    used_tokens = response.usage_metadata.total_token_count
                
                self._reconcile_usage(key, reserve_time, used_tokens)
                
                if response.parsed is not None:
                    result = response.parsed
                else:
                    try:
                        text = response.text.strip()
                        json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
                        if json_match:
                            text = json_match.group(1)
                        data = json.loads(text)
                        result = response_schema(**data)
                    except (json.JSONDecodeError, Exception) as parse_err:
                        raw_preview = ""
                        try:
                            if hasattr(response, "text") and response.text:
                                raw_preview = response.text[:200]
                            elif hasattr(response, "candidates") and response.candidates and response.candidates[0].finish_reason:
                                raw_preview = f"<Finish reason: {response.candidates[0].finish_reason}>"
                        except ValueError:
                            raw_preview = "<ValueError reading response.text>"
                        
                        print(f"JSON PARSE ERROR. Raw text preview: {raw_preview}")
                        raise InvalidResponseError(raw_preview)

                telemetry_logger.info({
                    "timestamp": time.time(),
                    "key_index": self.api_keys.index(key),
                    "latency_ms": latency_ms,
                    "tokens_used": used_tokens,
                    "status_code": 200,
                    "error_type": "none"
                })

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
                
                print(f"[{log_prefix} {attempts}/{max_attempts}] LLM call failed: {e}")
                
                if is_invalid:
                    invalid_retries += 1
                    if invalid_retries >= 2:
                        raise InvalidResponseError(raw_preview)
                
                if is_429 or is_5xx or is_invalid:
                    self._report_failure(key, is_429=is_429, is_token_limit=is_token_limit)
                    if attempts == max_attempts:
                        raise LLMFailureError(f"Max retries reached. Last error: {error_str}")
                    time.sleep(7.5)
                    continue
                else:
                    if attempts == max_attempts:
                        raise e
                    self._report_failure(key, is_429=False)
                    continue
        raise RuntimeError("LLM routing failed")

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
            print(f"[Name Clustering] Failed to cluster names using LLM: {e}")
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

Return a JSON object with: house_number, residents (list of strings), category, date, summary (string), and is_form (boolean)."""


    def extract_page(self, image_bytes: bytes) -> str:
        """Extracts Arabic text from an image using the local Qwen-VL model with retries."""
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        local_model = os.getenv("LOCAL_MODEL_NAME", "qwen2.5vl:7b")
        
        last_error: Optional[Exception] = None
        for qwen_attempt in range(2):
            try:
                response = self.local_client.chat.completions.create(
                    model=local_model,
                    messages=[
                        {"role": "system", "content": "Transcribe all Arabic text from the image verbatim. If the main content of the image is a photograph of a property, room, or inspection site, explicitly write '[PHOTOGRAPH OF PROPERTY]' at the beginning of your response, even if there are watermarks, disclaimers, or minor text visible. Do not attempt to classify or summarize otherwise."},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.0
                )
                res = response.choices[0].message.content
                if res is not None:
                    return res
                last_error = ValueError("Returned None")
            except Exception as e:
                last_error = e
        raise Exception(f"Failed to extract text after 2 attempts. Last error: {last_error}")

    def classify_extracted_page(self, text: str, extracted_footer: Optional[str] = None) -> PageClassification:
        """Classifies an extracted text page using a local LLM with structured output and heuristics."""
        system_prompt = self._build_system_prompt()
        user_prompt = f"Classify this scanned document page based on the following extracted text.\n\nExtracted Text:\n{text}"
        if extracted_footer:
            user_prompt += f"\n\nExtracted Footer Text: {extracted_footer}"
        
        local_model = os.getenv("LOCAL_TEXT_MODEL_NAME", "qwen2.5:14b")
        
        last_error: Optional[Exception] = None
        for text_attempt in range(3):
            try:
                response = self.local_client.beta.chat.completions.parse(
                    model=local_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=PageClassification,
                    temperature=0.0,
                    extra_body={"options": {"num_ctx": 8192}}
                )
                
                if response.choices[0].message.parsed:
                    parsed_result = response.choices[0].message.parsed
                else:
                    raise openai.OpenAIError("Parsed response is None")
                
                # Heuristic Override: Local models struggle with complex negative constraints.
                if getattr(parsed_result, "is_form", False) and parsed_result.category.value == "Allocation Order":
                    print("[Heuristic Override] Local model selected Allocation Order for a FORM. Forcing Basic Details Form.")
                    parsed_result.category = Category.BASIC_DETAILS
                    
                return parsed_result
            except Exception as e:
                last_error = e
        
        if last_error:
            raise last_error
        else:
            raise RuntimeError("Failed after 3 text classification attempts")

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
        
        attempts = 1 if self.use_local_llm else 100
        result = self._route_llm_call(
            model='gemma-4-26b-a4b-it',
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
                model='gemma-4-26b-a4b-it',
                contents=[system_prompt, user_prompt],
                response_schema=DateOutlierDetectionResult,
                log_prefix="DateOutlierDetection"
            )
            return result.outlier_page_indices # type: ignore
        except Exception as e:
            print(f"[DateOutlierDetection] Error during LLM call: {e}")
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
        
        use_local = self.should_use_local_fallback()
        
        if not use_local:
            try:
                print(" Running bulk semantic grouping using Cloud Model...")
                contents = [
                    system_prompt,
                    user_prompt
                ]
                attempts = 1 if self.use_local_llm else 100
                result = self._route_llm_call(
                    model='gemma-4-26b-a4b-it',
                    contents=contents,
                    response_schema=BulkSemanticMatchResult,
                    log_prefix="BulkSemanticCloud",
                    max_attempts=attempts
                )
                return result
            except Exception as e:
                print(f"WARNING: Direct Cloud bulk grouping failed: {e}")
                print("  [Transition] Triggering Rate Limit Cooldown. Falling back to local model...")
                self.activate_cooldown()
                use_local = True

        if use_local:
            local_model = os.getenv("LOCAL_TEXT_MODEL_NAME", "qwen2.5:14b")
            try:
                print(f" Running bulk semantic grouping using Local Model ({local_model})...")
                response = self.local_client.beta.chat.completions.parse(
                    model=local_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=BulkSemanticMatchResult,
                    temperature=0.0,
                    extra_body={"options": {"num_ctx": 32768}}
                )
                if response.choices[0].message.parsed:
                    return response.choices[0].message.parsed
                else:
                    raise openai.OpenAIError("Parsed response is None")
            except Exception as e:
                print(f"[Local Inference Failed] bulk semantic grouping failed. Error: {e}")
                raise
        raise RuntimeError("Unexpected control flow")



