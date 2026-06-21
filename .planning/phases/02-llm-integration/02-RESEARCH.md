# Phase 2: LLM Integration — Research

**Completed:** 2026-06-21
**Status:** Research complete — ready for planning

---

## 1. Google Gen AI SDK for Gemma 4 31b

### Findings

- **Model identifier**: `gemma-4-31b-it` (instruction-tuned variant) is the correct model string for the Google AI Studio API.
- **SDK**: The project already uses `google-genai` (Python). The `genai.Client(api_key=...)` pattern in the existing `llm.py` is correct.
- **Native structured output is confirmed**: Gemma 4 31b supports `response_mime_type: "application/json"` and `response_schema` through the Google AI Studio API. This uses constrained decoding at the model level — the output is guaranteed to match the schema.
- **Pydantic integration**: You can pass a Pydantic `BaseModel` directly as `response_schema`. The SDK returns `response.parsed` as an already-instantiated Pydantic object — no manual JSON parsing needed.
- **Context window**: 256K tokens (~256–384 pages of standard text). More than sufficient for a 200-page housing document.
- **Multimodal**: Gemma 4 supports both text and image inputs. The current code sends page images directly to the model. However, since Phase 1 already extracts text via OCR, we should send the extracted text (not images) to reduce token usage and improve reliability.

### Recommended Approach

```python
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class Category(str, Enum):
    BASIC_DETAILS = "basic_details"
    PERSONAL_DETAILS = "personal_details"
    AMAR_TAKHSEES = "amar_takhsees"
    KEY_HANDOVER = "key_handover_form"
    CONTRACT = "contract"
    EWA_LETTERS = "ewa_related_letters"
    RENT_DEDUCTION = "rent_deduction"
    ALLOWANCE_DEDUCTION = "allowance_deduction"
    NOTIFICATIONS = "notifications"
    MAINTENANCE = "maintenance"
    PICTURES = "pictures"
    MODIFICATIONS = "modifications"
    OTHER_LETTERS = "other_letters"

class PageClassification(BaseModel):
    house_number: str = Field(description="The house number mentioned in the document")
    resident: str = Field(description="The resident name, or 'NONE' for general house letters and Amar Takhsees")
    category: Category = Field(description="The document category")
    is_continuation: bool = Field(description="True if this page continues the same topic as the previous page")

client = genai.Client(api_key="...")

response = client.models.generate_content(
    model="gemma-4-31b-it",
    contents="...",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=PageClassification,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        temperature=0,
    ),
)
result: PageClassification = response.parsed
```

### Risks
- **Thinking mode interference**: Gemma 4 has a "thinking" capability that generates internal reasoning tokens before the JSON output. This can break structured output parsing. **Mitigation**: Set `thinking_budget=0` in `ThinkingConfig` to disable thinking entirely when requesting structured JSON.
- **Complex schemas**: Very deep JSON schemas with `$ref`/`$defs` can occasionally cause issues. **Mitigation**: Keep the schema flat (single-level Pydantic model). The `PageClassification` schema above is simple enough.

---

## 2. Structured JSON Output

### Findings

- **Constrained decoding is native**: When `response_mime_type="application/json"` and `response_schema` are both provided, the Google API uses constrained decoding to restrict token selection at every generation step. The output is guaranteed to be valid JSON matching the schema.
- **No fallback needed**: Decision D-02 anticipated needing a "fallback to strict system prompt engineering." Based on research, native JSON mode is confirmed for Gemma 4 — the fallback is unlikely to be needed but should still be coded defensively.
- **Property ordering**: The API preserves the field ordering defined in the Pydantic model. Use `propertyOrdering` if strict field order matters for chain-of-thought prompting.
- **Enum constraints**: Using Python `Enum` types in the Pydantic model constrains the category field to exactly the 13 valid values. The model cannot output an invalid category.

### Recommended Approach

1. **Primary**: Use native `response_schema` with Pydantic models + `response_mime_type="application/json"`.
2. **Defensive fallback**: If `response.parsed` is `None` (edge case), fall back to `json.loads(response.text)` with Pydantic validation.
3. **Retry on failure**: If both fail, retry the prompt (per D-07). Use `tenacity` with max 3 retries.

### Risks
- **Schema too rigid**: If the LLM can't fit the data into the schema (e.g., no house number visible on a page), it may hallucinate a value. **Mitigation**: Make fields like `house_number` optional or include a "UNKNOWN" sentinel value. Alternatively, use a system prompt that instructs the model to use the house number from the accumulated context if not visible on the current page.

---

## 3. Dynamic Sliding Window for Document Continuation

### Findings

- **Decision D-03 specifies**: Accumulate pages into the context window until the LLM flags a topic change.
- **256K context is generous**: At ~750 tokens per OCR page, 200 pages ≈ 150K tokens. This fits within the 256K window with room for the system prompt and output.
- **However, "lost-in-the-middle" is real**: LLMs can lose attention to content in the middle of very long prompts. Sending 100+ pages at once may degrade accuracy.
- **Best pattern — Incremental Accumulation**:
  1. Start with Page 1. Send it to the LLM. Get classification.
  2. Send Page 1 + Page 2. Ask: "Is page 2 a continuation of the same topic?"
  3. If yes, send Page 1 + Page 2 + Page 3. Repeat.
  4. If no, the previous group (Pages 1–N) is a complete document. Start a new group with the current page.
  5. For older context, replace verbatim pages with a brief summary to save tokens.

### Recommended Approach

```
Architecture: Sequential Page Accumulator

State maintained between calls:
  - current_group_pages: list[str]  # verbatim text of pages in current topic
  - current_group_metadata: dict    # house, resident, category from first page
  - previous_summary: str           # summary of previously completed groups

Per-page flow:
  1. Append new page text to current_group_pages
  2. Build prompt with:
     [SYSTEM]: classification instructions + 13 categories
     [CONTEXT]: previous_summary (if any)
     [CURRENT PAGES]: all pages in current_group_pages
     [QUESTION]: Classify and determine if this is a continuation
  3. Send to LLM
  4. If is_continuation=true: continue accumulating
  5. If is_continuation=false:
     - Emit completed document (start_page..end_page, metadata)
     - Reset current_group_pages to [current_page_only]
     - Update previous_summary
```

### Context Window Budget

| Component | Estimated Tokens |
|-----------|-----------------|
| System prompt + categories | ~1,000 |
| Previous summary | ~500 |
| Accumulated pages (worst case: 20 pages) | ~15,000 |
| Output | ~200 |
| **Total per call** | **~17,000** |
| **Available (256K)** | **~256,000** |

Even with 50+ continuation pages, we stay well within limits.

### Risks
- **Very long continuation sequences (50+ pages)**: Unlikely but possible. If accumulated text exceeds ~100K tokens, switch to summary+latest strategy. **Mitigation**: Set a configurable `MAX_ACCUMULATION_TOKENS` threshold (e.g., 100K). Beyond that, summarize older pages.
- **Topic detection accuracy**: The LLM may occasionally miss a topic boundary or false-flag one. **Mitigation**: Include clear examples of topic changes vs. continuations in the system prompt (few-shot).

---

## 4. Arabic Text Processing with LLMs

### Findings

- **Gemma 4 supports 140+ languages** including Arabic natively. No fine-tuning needed.
- **Arabic name normalization challenges**:
  - "Al-" (ال) prefix: can be a definite article or part of a clan name (Āl Saud). Must be handled contextually.
  - "Ibn/Bin" (ابن/بن): "son of" — often omitted or abbreviated.
  - Alef variations: أ, إ, آ, ا — different Unicode forms of the same character.
  - Transliteration inconsistency: Mohammed vs Muhammad vs Mohamad.
- **Per D-06**: The LLM should handle normalization intelligently, not code-level preprocessing.
- **OCR noise**: Scanned Arabic text may have character recognition errors (e.g., ع confused with غ). The LLM should be instructed to interpret noisy text charitably.

### Recommended Approach

1. **System prompt instruction for name normalization**:
   ```
   When extracting resident names, normalize Arabic names to a canonical form:
   - Remove the definite article "ال" (Al-) unless it is part of a family/clan name
   - Standardize "ابن" and "بن" to "بن"
   - If the same person is referred to by different name variations across pages, 
     use the most complete version of the name consistently
   - Output names in Arabic script, not transliterated
   ```

2. **No code-level Arabic preprocessing**: Let the LLM handle it. The 31B model is large enough for nuanced Arabic understanding.

3. **Validation**: After processing all pages, build a name deduplication step that groups similar names (this is a Phase 3 concern but should be considered in the schema design).

### Risks
- **OCR quality**: Very poor OCR output may confuse the LLM. **Mitigation**: Use the highest quality OCR settings from Phase 1. Consider sending page images alongside text for ambiguous cases (Gemma 4 supports multimodal).
- **Name consistency across pages**: The LLM processes pages independently (despite context accumulation). Different calls may normalize the same name differently. **Mitigation**: Include previously seen names in the context/summary so the LLM can be consistent.

---

## 5. Rate Limiting & Retry Patterns

### Findings

- **Google AI Studio rate limits (per project)**:

  | Tier | RPM | TPM | RPD |
  |------|-----|-----|-----|
  | Free | 5–30 | 250K–1M | 250–1,500 |
  | Paid (Tier 1+) | 150–4,000+ | 1M–20M+ | Scalable |

- **For a 200-page document processed sequentially**: 200 API calls. At free tier (5 RPM), this takes ~40 minutes. At paid tier (150 RPM), ~1.3 minutes.
- **Existing code uses `tenacity`** (already in `requirements.txt`) — this is the correct library.
- **Current retry config**: `wait_exponential(multiplier=1, min=2, max=10)`, `stop_after_attempt(5)` — reasonable but max wait is too low for rate limits. Google recommends waiting 30–60 seconds for quota recovery.
- **Multi-key rotation**: Existing code supports multiple API keys with round-robin switching on rate limit errors — good pattern, keep it.

### Recommended Approach

```python
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import random

@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60) + wait_random(0, 2),  # jitter
    stop=stop_after_attempt(7),
    retry=retry_if_exception_type((RateLimitError, InvalidResponseError)),
)
async def classify_page(self, ...):
    ...
```

1. **Exponential backoff with jitter**: Base delay 4s, max 60s, random jitter 0–2s.
2. **Max 7 attempts**: Generous enough for transient rate limits.
3. **Key rotation**: On 429, switch to next API key before retrying.
4. **Proactive pacing**: Add a configurable `DELAY_BETWEEN_PAGES` (e.g., 1–2 seconds) to stay under RPM limits without hitting 429.
5. **Separate retry for invalid JSON** (D-07): If `response.parsed` returns `None` or validation fails, retry with the same prompt (different from rate limit retry).

### Risks
- **Free tier is very restrictive**: 5 RPM = 40 minutes for 200 pages. **Mitigation**: Document this for the user; recommend paid tier or multiple API keys for production.
- **Daily quota exhaustion**: 250 RPD on free tier won't finish a 200-page doc if any retries happen. **Mitigation**: Track remaining quota; warn user before starting.

---

## 6. 13-Category Classification

### Findings

The 13 categories (from PROJECT.md) are:
1. `basic_details` — بيانات أساسية
2. `personal_details` — بيانات شخصية
3. `amar_takhsees` — أمر تخصيص
4. `key_handover_form` — نموذج تسليم مفاتيح
5. `contract` — عقد
6. `ewa_related_letters` — رسائل متعلقة بالكهرباء والماء
7. `rent_deduction` — خصم إيجار
8. `allowance_deduction` — خصم بدل
9. `notifications` — إخطارات
10. `maintenance` — صيانة
11. `pictures` — صور
12. `modifications` — تعديلات
13. `other_letters` — رسائل أخرى

Special routing:
- **Amar Takhsees** (people who got orders but didn't live there) → root-level folder
- **Generic house letters** (not about a specific person) → `resident: "NONE"`

### Recommended Prompt Structure

```
SYSTEM PROMPT:
You are an Arabic document classification expert analyzing scanned housing files 
from Bahrain/Gulf region. Each page belongs to a specific house and may relate to 
a specific resident or be a general house document.

CATEGORIES (select exactly one):
1. basic_details — Basic resident information, ID documents, civil records
2. personal_details — Personal correspondence, family details
3. amar_takhsees — Housing allocation orders
4. key_handover_form — Key handover/delivery forms
5. contract — Rental or housing contracts
6. ewa_related_letters — Electricity & Water Authority correspondence
7. rent_deduction — Rent deduction notices or records
8. allowance_deduction — Allowance/benefit deduction documents
9. notifications — Official notifications and announcements
10. maintenance — Maintenance requests, reports, work orders
11. pictures — Photographs or visual documentation
12. modifications — Building modification requests or approvals
13. other_letters — Any letters not fitting the above categories

SPECIAL RULES:
- If the document is a general house letter (not about a specific resident), 
  set resident to "NONE"
- If the document is an "Amar Takhsees" for someone who was allocated but 
  never lived in the house, set resident to "NONE"
- Normalize Arabic names consistently across pages
- Use the house number from context if not explicitly on this page

CONTEXT FROM PREVIOUS PAGES:
{previous_summary}

PAGES TO ANALYZE:
{accumulated_pages}

Classify the latest page. Is it a continuation of the previous topic?
```

### Recommended Approach

1. **Enum-constrained categories**: Use the Pydantic `Enum` to restrict the model to exactly 13 values.
2. **Bilingual category descriptions**: Provide both English identifiers and Arabic descriptions in the system prompt so the model can match Arabic document content to categories.
3. **Few-shot examples**: Include 2–3 examples of each special case (NONE resident, continuation detection) in the system prompt for the first few pages.
4. **Confidence field (optional)**: Consider adding a `confidence: float` field to the schema. Low-confidence classifications can be flagged for manual review.

### Risks
- **Category ambiguity**: Some documents may fit multiple categories (e.g., a maintenance notification). **Mitigation**: The system prompt should prioritize the most specific category. Add a `reasoning` field for debugging.
- **"Pictures" category**: The LLM processes text, not images. If a page contains mostly images with little text, OCR output will be sparse. **Mitigation**: If OCR text is very short (< 50 chars), consider using multimodal input (send the image directly to Gemma 4) for that specific page.

---

## Existing Code Gap Analysis

The current codebase needs significant changes for Phase 2:

| File | Current State | Required Changes |
|------|--------------|-----------------|
| `src/llm.py` | Uses `gemini-2.5-flash`, image input, regex JSON parsing | Change to `gemma-4-31b-it`, text input, native JSON schema, add `ThinkingConfig` |
| `src/pipeline.py` | Parallel `ThreadPoolExecutor`, simple continuation flag | Sequential processing, sliding window accumulation, context management |
| `src/ingest.py` | Extracts page images only | Must also provide extracted text per page (or add a text extraction step) |
| `src/main.py` | Basic output filenames | Will need deeper integration with Phase 3 folder structure |

### Critical Architecture Decision

The existing `ingest.py` only extracts page images. Phase 1 should also extract OCR text. Two options:
1. **Text-only to LLM**: Extract text in Phase 1, send text to Gemma 4. Lower token cost, faster.
2. **Image-only to LLM**: Send page images directly to Gemma 4 (multimodal). Higher accuracy for visual documents but much higher token cost.
3. **Hybrid**: Send text for most pages, fall back to images for pages with very short OCR output.

**Recommendation**: Option 1 (text-only) as default, with Option 3 as an enhancement. This aligns with the Phase 1 → Phase 2 pipeline design.

---

## Validation Architecture Notes

### Test Strategies

1. **Unit Tests**:
   - Schema validation: Ensure Pydantic model accepts all valid category combinations
   - Retry logic: Mock 429 errors, verify exponential backoff behavior
   - Name normalization: Test with known Arabic name variations

2. **Integration Tests**:
   - Single-page classification: Send a known Arabic document page, verify correct category
   - Continuation detection: Send 2–3 related pages, verify `is_continuation` accuracy
   - Edge cases: Empty OCR text, "NONE" resident, Amar Takhsees routing

3. **End-to-End Tests**:
   - Process a small sample PDF (5–10 pages) through the full pipeline
   - Verify document grouping (continuation merging)
   - Verify correct house/resident/category extraction

4. **Manual Verification Dataset**:
   - Create a "golden set" of 20–30 manually classified pages
   - Run the pipeline and compare against ground truth
   - Track accuracy metrics per category
