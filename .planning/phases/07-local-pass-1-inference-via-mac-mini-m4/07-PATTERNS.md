# Phase 7 Patterns: Local Pass 1 Inference via Mac Mini M4

## 1. `src/llm.py`
- **Role:** LLM Integration and Data Pipeline. Handles requests to the LLM backend for image classification.
- **Data Flow:**
  - `classify_page` takes `image_bytes`, builds a prompt, and will now first route the request to the local LM Studio endpoint (running Qwen2.5-VL-7B-Instruct) using the `openai` Python client.
  - If the local inference fails (hangs, connection error, invalid schema), it falls back to Google Gemini APIs (specifically using `gemma-4-26b-a4b-it` or `gemini-4-26b`).
  - The fallback mechanism must remove paths for `gemini-4-31b` and `gemini-2.5-flash`.
- **Closest Existing Analog:** The existing `_route_llm_call` logic currently handles rotation and retries for Gemini. We will adapt or wrap this mechanism to introduce a local-first logic layer.
- **Concrete Code Excerpt:**
  ```python
  def classify_page(self, image_bytes: bytes) -> PageClassification:
      # ... prompt building ...
      # Needs to attempt local openai client first before falling back
      result = self._route_llm_call(
          model='gemma-4-26b-a4b-it', # Use gemini-4-26b
          contents=contents,
          response_schema=PageClassification,
          log_prefix="Retry"
      )
  ```

## 2. `src/schemas.py`
- **Role:** Schema Definition and Data Validation.
- **Data Flow:** Converts the raw JSON text or structured objects returned by the `openai` client into validated Pydantic models.
- **Closest Existing Analog:** Existing `PageClassification` schema used for `genai` structured outputs.
- **Concrete Code Excerpt:**
  ```python
  class PageClassification(BaseModel):
      """Structured output schema for per-page document classification."""
      house_number: str = Field(...)
      residents: list[str] = Field(...)
      category: Category = Field(...)
      date: str = Field(...)
      is_continuation: bool = Field(...)
  ```

## 3. `tests/test_llm.py`
- **Role:** Unit & Integration Testing for LLM integrations.
- **Data Flow:** Simulates calls to the Local Server and Fallbacks. Mocks `openai` and `genai` clients to verify logic flows cleanly.
- **Closest Existing Analog:** Existing tests testing fallback retries and rate limiting in `test_llm.py`.
- **Concrete Code Excerpt:**
  We will add test cases to simulate a timeout/500 from the local LM Studio model and assert that the request correctly reroutes to `gemini-4-26b` and strictly bypasses `gemini-4-31b` and `gemini-2.5-flash`.
