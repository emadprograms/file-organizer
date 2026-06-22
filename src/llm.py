import os
import time
import json
from google import genai
from google.genai import types
from tenacity import retry, wait_exponential, wait_random, stop_after_attempt, retry_if_exception_type

from src.schemas import PageClassification


class RateLimitError(Exception):
    pass


class InvalidResponseError(Exception):
    pass


class GemmaClient:
    def __init__(self, api_keys: list[str] = None, delay_between_pages: float = 1.0):
        if not api_keys:
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("No API keys provided and GEMINI_API_KEY not found in environment.")
            self.api_keys = [key]
        else:
            self.api_keys = api_keys

        self.current_key_idx = 0
        self.delay_between_pages = delay_between_pages
        self._configure_client()

    def _configure_client(self):
        self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])

    def switch_key(self):
        if len(self.api_keys) > 1:
            self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
            self._configure_client()

    # Categories where NONE is a valid/expected resident value
    NONE_EXPECTED_CATEGORIES = {'amar_takhsees', 'pictures', 'other_letters'}

    def _build_system_prompt(self) -> str:
        """Returns the classification system prompt for scanned Arabic housing documents."""
        return """You are an Arabic document classification expert analyzing scanned housing files from the Bahrain/Gulf region.

You are receiving a scanned page IMAGE. Read the page directly using your vision capabilities and classify it.

Classify this page into exactly ONE of the following 13 categories:

1. basic_details — البيانات الأساسية (Basic resident information, ID cards, civil records)
2. personal_details — البيانات الشخصية (Personal information forms, family details)
3. amar_takhsees — أمر تخصيص (Allocation orders for people assigned but not residing)
4. key_handover_form — نموذج تسليم المفتاح (Key handover/receipt forms)
5. contract — العقد (Rental or housing contracts)
6. ewa_related_letters — رسائل الكهرباء والماء (EWA electricity/water letters)
7. rent_deduction — خصم الإيجار (Rent deduction notices or records)
8. allowance_deduction — خصم العلاوة (Allowance deduction notices)
9. notifications — الإشعارات (General notifications, warnings)
10. maintenance — الصيانة (Maintenance requests, reports, work orders)
11. pictures — الصور (Photographs of the property)
12. modifications — التعديلات (Modification requests or approvals)
13. other_letters — رسائل أخرى (Any letters that don't fit the above)

NAME EXTRACTION RULES (CRITICAL):
- Arabic names typically have 4 to 5 parts (e.g., محمد السيد ابراهيم جمعه محمد). Extract ALL parts of the name, not just 2 or 3.
- Names may appear in Arabic OR English on the document. Always prefer the longest/most complete version you can find.
- Look for names in ALL areas of the page: headers, footers, address blocks, body text, stamps, and signatures.
- Do NOT return "NONE" for the resident unless you are absolutely certain there is no name anywhere on the page. Most documents DO contain a name.
- Only return "NONE" for categories where no resident is expected: amar_takhsees (general allocation), pictures, or other_letters with no addressee.

CONTINUATION GROUPING RULES (CRITICAL):
- If you are told there is a currently active document group with a specific category, and this page has the SAME category AND appears to be part of the same topic/letter/form, set is_continuation to true.
- Multiple consecutive pages of the same category (e.g., several "basic_details" pages in a row) are very likely continuations of the same document group.
- Only set is_continuation to false when you are confident this page starts an entirely NEW and unrelated document or letter, even if it shares the same category.

SPECIAL RULES:
- For general house letters and "Amar Takhsees" documents that are NOT tied to a specific resident, set resident to "NONE".
- Normalize Arabic names intelligently: group variations like "محمد" and "المحمد" as the same person.
- Tolerate OCR noise and imperfect text in scanned documents.

Return a JSON object with: house_number, resident, category, is_continuation."""

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=60) + wait_random(0, 2),
        stop=stop_after_attempt(7),
        retry=retry_if_exception_type((RateLimitError, InvalidResponseError))
    )
    def classify_page(self, image_bytes: bytes, previous_summary: str = "", active_summary: str = "") -> PageClassification:
        """
        Classifies a scanned page image using Gemma 4 31b multimodal vision.
        Returns a PageClassification with house_number, resident, category, is_continuation.
        Includes active group context for better continuation detection
        and retries once if resident is NONE for categories that should have a name.
        """
        system_prompt = self._build_system_prompt()

        user_prompt = "Classify this scanned document page."
        if active_summary:
            user_prompt += f"\n\nCurrently active document group: {active_summary}\nIs this page a continuation of the active group? If same category and related content, set is_continuation to true."
        if previous_summary:
            user_prompt += f"\n\nPrevious closed group: {previous_summary}"

        try:
            response = self.client.models.generate_content(
                model='gemma-4-31b-it',
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

            # Try native parsed response first
            if response.parsed is not None:
                result = response.parsed
            else:
                # Fallback: parse JSON text manually
                try:
                    data = json.loads(response.text)
                    result = PageClassification(**data)
                except (json.JSONDecodeError, Exception) as parse_err:
                    raise InvalidResponseError(
                        f"Failed to parse LLM response as PageClassification: {type(parse_err).__name__}"
                    )

            # Name retry: if resident is NONE but category expects a name, retry once
            if (result.resident == "NONE"
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
                    if active_summary:
                        retry_prompt += f"\n\nCurrently active document group: {active_summary}"
                    if previous_summary:
                        retry_prompt += f"\n\nPrevious closed group: {previous_summary}"

                    time.sleep(self.delay_between_pages)
                    retry_response = self.client.models.generate_content(
                        model='gemma-4-31b-it',
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

                    # Use the retry result only if it found a name
                    if retry_result.resident != "NONE":
                        result = retry_result
                except Exception:
                    pass  # Keep original result if retry fails

            time.sleep(self.delay_between_pages)
            return result

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str or "quota" in error_str.lower() or "Resource exhausted" in error_str:
                self.switch_key()
                raise RateLimitError(f"Rate limited: {error_str}")
            if isinstance(e, (RateLimitError, InvalidResponseError)):
                raise
            raise InvalidResponseError(f"Unexpected error: {error_str}")
