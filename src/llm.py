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

SPECIAL RULES:
- For general house letters and "Amar Takhsees" documents that are NOT tied to a specific resident, set resident to "NONE".
- Normalize Arabic names intelligently: group variations like "محمد" and "المحمد" as the same person.
- Tolerate OCR noise and imperfect text in scanned documents.
- If a page is a continuation of the previous page's document/letter, set is_continuation to true.

Return a JSON object with: house_number, resident, category, is_continuation."""

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=60) + wait_random(0, 2),
        stop=stop_after_attempt(7),
        retry=retry_if_exception_type((RateLimitError, InvalidResponseError))
    )
    def classify_page(self, image_bytes: bytes, previous_summary: str = "") -> PageClassification:
        """
        Classifies a scanned page image using Gemma 4 31b multimodal vision.
        Returns a PageClassification with house_number, resident, category, is_continuation.
        """
        system_prompt = self._build_system_prompt()

        user_prompt = "Classify this scanned document page."
        if previous_summary:
            user_prompt += f"\n\nContext from previous pages:\n{previous_summary}"

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
