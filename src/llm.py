import concurrent.futures
import os
import time
import json
import re
import random
import threading
import logging
import base64
import openai
import requests
import pydantic
import functools
from collections import deque
from google import genai
from google.genai import types

from src.schemas import PageClassification, EntityResolutionMapping, Category, NameMatchResult

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
    NONE_EXPECTED_CATEGORIES = {'amar_takhsees', 'pictures'}
    GLOBAL_RPM_LIMIT = 10
    TPM_LIMIT = 30000
    RPM_LIMIT = 30
    
    global_rpm_tracker = deque()
    global_cooldown_until = 0.0

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
        self.last_request_time = {key: 0.0 for key in self.api_keys}
        
        # Trackers
        self.tpm_trackers = {key: deque() for key in self.api_keys}
        self.rpm_trackers = {key: deque() for key in self.api_keys}
        
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

    def _save_state(self):
        state = {
            "global_rpm_tracker": list(GemmaClient.global_rpm_tracker),
            "global_cooldown_until": GemmaClient.global_cooldown_until
        }
        try:
            with open(".rate_limit_state.json", "w") as f:
                json.dump(state, f)
        except Exception:
            pass

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
                
                while GemmaClient.global_rpm_tracker and now - GemmaClient.global_rpm_tracker[0] > 65.0:
                    GemmaClient.global_rpm_tracker.popleft()
                
                # Global IP Throttle
                if now < GemmaClient.global_cooldown_until:
                    sleep_time = GemmaClient.global_cooldown_until - now
                elif len(GemmaClient.global_rpm_tracker) >= self.GLOBAL_RPM_LIMIT:
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
                
            self.cooldown_keys[key] = now + penalty
            # CRITICAL FIX: Google tracks the IP for all errors (429s, 503s, Timeouts).
            # We must enforce the penalty globally to let the IP flush before picking the next key.
            GemmaClient.global_cooldown_until = max(GemmaClient.global_cooldown_until, now + penalty)
            self._save_state()
            self._push_telemetry()

    def _report_success(self, key: str):
        with self.lock:
            if self.key_strikes[key] > 0:
                self.key_strikes[key] = 0
            self._push_telemetry()

    def _route_llm_call(self, model: str, contents: list, response_schema: type, log_prefix: str = "Retry", max_attempts: int = None) -> any:
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

    def _build_system_prompt(self) -> str:
        return """You are an Arabic document classification expert analyzing scanned housing files from the Bahrain/Gulf region.

You are receiving a scanned page IMAGE. Read the page directly using your vision capabilities and classify it.

CRITICAL FIRST STEP: ALWAYS analyze the subject (الموضوع) of the letter or document first before looking at the body text.

Classify this page into exactly ONE of the following 13 categories:

1. basic_details — البيانات الأساسية (Strictly forms about the person. If it is not a form, it cannot be classified as basic details.)
2. personal_details — البيانات الشخصية (Pictures of identity cards, passports, and other non-form documents related to the person and his family. Anything related to the person and his family that is NOT a form goes into personal details.)
3. amar_takhsees — أمر تخصيص (Allocation orders. STRICT DEFINITION: An allocation order (amar takhsees) is STRICTLY an order from a higher authority or someone important claiming or telling to give the person (primary tenant) a place to stay. Do NOT classify random documents as allocation orders. Strong pattern: Exact subject 'الموضوع : الوحدات السكنية' or mentions 'تمديد الإقامة / السكن'.)
4. key_handover_form — نموذج تسليم المفتاح (Key handover/receipt forms. Strong pattern: Contains 'استمارة تسليم الوحدات السكنية التابعة لوزارة الداخلية'.)
5. contract — العقد (Rental or housing contracts)
6. ewa_related_letters — رسائل الكهرباء والماء (EWA electricity/water letters. Strong pattern: Contains a meter number, such as 'الوحدة السكنية رقم' or similar.)
7. rent_deduction — خصم الإيجار (Rent deduction notices or records. STRICT DEFINITION: Rent deduction letters will ALWAYS contain "30 bd" or "60 bd". Use this presence/absence to strictly disambiguate from Allowance Deduction.)
8. allowance_deduction — خصم العلاوة (Allowance deduction notices. Strong pattern: Subject is 'الموضوع: وقف استقطاع بدل الانتفاع'. Will NOT have "30 bd" or "60 bd" written on it.)
9. notifications — الإشعارات (General notifications, warnings. Strong pattern: Contains the word 'إشعار' or 'اشعار'. Do NOT use this for allocation orders.)
10. maintenance — الصيانة (Maintenance requests, reports, work orders. Strong pattern: Sender or receiver is 'إدارة الأشغال' (idara ashgal), or it is a yellow paper with inspection details, or ANY mention of "inspection" goes to maintenance.)
11. pictures — الصور (Photographs of the property)
12. modifications — التعديلات (Modification requests or approvals. Strong pattern: Subject contains 'طلب' (talab) and mentions modifying the house.)
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
- Normalize Arabic names intelligently: group variations like "محمد" and "المحمد" as the same person.
- Tolerate OCR noise and imperfect text in scanned documents.

FALLBACK INSTRUCTION (CRITICAL):
- If NO subject (الموضوع) is found AND none of the strong patterns above match, set `needs_gemma_fallback = true` and do NOT guess blindly. However, if you are the fallback model doing a retry, do your absolute best to categorize.

Return a JSON object with: house_number, residents (list of strings), category, date, and needs_gemma_fallback."""

    def classify_page(self, image_bytes: bytes) -> PageClassification:
        system_prompt = self._build_system_prompt()
        user_prompt = "Classify this scanned document page."
        
        local_model = os.getenv("LOCAL_MODEL_NAME", "qwen2.5vl:7b")
        try:
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            response = self.local_client.beta.chat.completions.parse(
                model=local_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format=PageClassification,
                temperature=0.0
            )
            if response.choices[0].message.parsed:
                parsed_result = response.choices[0].message.parsed
                if getattr(parsed_result, "needs_gemma_fallback", False):
                    print("[Local Inference Refused] No subject/strong pattern found. Falling back to gemini-4-26b.")
                    raise ValueError("Local Inference Refused via needs_gemma_fallback flag")
                return parsed_result
            else:
                raise openai.OpenAIError("Parsed response is None")
        except (openai.OpenAIError, requests.exceptions.RequestException, pydantic.ValidationError, ValueError) as e:
            print(f"[Local Inference Failed/Refused] Falling back to gemini-4-26b. Error: {e}")
            contents = [
                system_prompt,
                user_prompt,
                types.Part.from_bytes(data=image_bytes, mime_type='image/png')
            ]
            
            result = self._route_llm_call(
                model='gemini-4-26b',
                contents=contents,
                response_schema=PageClassification,
                log_prefix="Fallback"
            )
            return result

    @functools.lru_cache(maxsize=1024)
    def check_name_match(self, name_current: str, name_candidate: str, category: str) -> bool:
        """Semantically compare two names to determine if they refer to the same primary tenant."""
        if not name_current or not name_candidate:
            return False
            
        system_prompt = (
            f"You are an Arabic name matching expert analyzing names from a '{category}' housing document.\n\n"
            "CRITICAL RULES:\n"
            "1. Ignore common Arabic prefixes like 'ال' (Al-) and titles like 'السيد' (Mr.), 'المرحوم' (The late), 'ورثة' (Heirs).\n"
            "2. Tolerate slight spelling variations or missing middle names (e.g., 'محمد علي أحمد' and 'محمد أحمد' might be the same person).\n"
            "3. If one name is clearly a completely different person, return false.\n"
            "4. Provide a structured JSON response with 'is_match' (boolean) and 'reason' (string explaining why).\n"
        )
        user_prompt = f"Name 1: {name_current}\nName 2: {name_candidate}\n\nDo these names semantically refer to the same person?"
        
        local_model = os.getenv("LOCAL_MODEL_NAME", "qwen2.5vl:7b")
        try:
            response = self.local_client.beta.chat.completions.parse(
                model=local_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=NameMatchResult,
                temperature=0.0
            )
            if response.choices[0].message.parsed:
                return response.choices[0].message.parsed.is_match
            else:
                raise openai.OpenAIError("Parsed response is None")
        except (openai.OpenAIError, requests.exceptions.RequestException, pydantic.ValidationError, ConnectionError, TimeoutError) as e:
            print(f"[Local Inference Failed] Falling back to gemini-4-26b for name match. Error: {e}")
            contents = [
                system_prompt,
                user_prompt
            ]
            try:
                result = self._route_llm_call(
                    model='gemini-4-26b',
                    contents=contents,
                    response_schema=NameMatchResult,
                    log_prefix="NameMatch Fallback",
                    max_attempts=3
                )
                return result.is_match
            except Exception as gemini_err:
                print(f"[Gemini Fallback Failed] {gemini_err}")
                return False

    def resolve_entities(self, raw_pages_log: str) -> dict[str, str]:
        system_prompt = (
            "You are an Arabic document classification expert analyzing a chronological log of documents "
            "[Category, Name, Date] for a single house.\n\n"
            "Your task is to resolve ALL unique tenant/resident names mentioned across the files into canonical 'Primary Resident' names.\n"
            "There may be multiple generations (father, then son inherits) or multiple separate rentals over time.\n\n"
            "CRITICAL RULES:\n"
            "1. Identify the 'Primary Tenants' who signed the contracts or handover forms.\n"
            "2. Group all variations of a name (e.g., 'محمد علي' and 'المرحوم محمد علي') under the most complete canonical name.\n"
            "3. Spouses and children (e.g., 'آمنة (زوجة)') MUST be mapped to the Primary Tenant of their era! Do NOT make them their own separate entity.\n"
            "4. Return a JSON object mapping EVERY EXACT RAW NAME to its canonical Primary Tenant name.\n\n"
            "Example Output:\n"
            "{\n"
            "  \"محمد علي أحمد\": \"محمد علي أحمد\",\n"
            "  \"محمد علي\": \"محمد علي أحمد\",\n"
            "  \"آمنة (زوجة)\": \"محمد علي أحمد\",\n"
            "  \"أحمد محمد علي\": \"أحمد محمد علي\"\n"
            "}"
        )
        user_prompt = f"Resolve the following document log:\n\n{raw_pages_log}"
        system_prompt += "\n\nCRITICAL: Output valid JSON exactly in this structure: {\"mapping_list\": [{\"raw_name\": \"...\", \"canonical_name\": \"...\"}]}"
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise Exception("DEEPSEEK_API_KEY not found in environment!")
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        
        import requests
        import json
        
        for attempt in range(1, 10):
            try:
                response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                
                mapping_dict = {}
                for item in parsed.get("mapping_list", []):
                    mapping_dict[item["raw_name"]] = item["canonical_name"]
                return mapping_dict
            except Exception as e:
                print(f"[DeepSeek Retry {attempt}/10] Failed: {e}")
                time.sleep(5)
                
        raise Exception("DeepSeek failed after 10 attempts.")

