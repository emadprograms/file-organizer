---
wave: 1
depends_on: []
files_modified:
  - tests/test_providers.py
  - tests/test_llm.py
  - tests/test_pipeline.py
  - tests/test_fallback_chain.py
autonomous: true
requirements:
  - TEST-01
---

# Phase 05: Testing - Execution Plan

## Artifacts this phase produces
- `tests/test_providers.py`: New test file containing tests for `GeminiProvider`, `OpenRouterProvider`, and `GroqProvider`.
- `tests/test_fallback_chain.py`: New test file for fallback chain integration.
- Updated `tests/test_llm.py`: Existing file updated with `LLMClient` unit tests.
- Updated `tests/test_pipeline.py`: Existing file updated with orchestration and cache tests.

## Verification
### must_haves
```yaml
must_haves:
  truths:
    - "Unit tests for LLMClient, LLMProviders, and Pipeline are implemented and pass via pytest."
    - "Integration test for the API fallback chain uses live invalid keys to verify fail-fast and mocks for 500 failovers."
    - "TEST-01 is fully satisfied."
    - "Integration test for fail-fast abort explicitly asserts secondary provider generate methods are never called."
    - "Test for 429 rate limit correctly mocks time.sleep and asserts 3 retries before failover."
    - "Pipeline cache hit test uses a real test-specific JSON cache file instead of mocking the Cache class."
  prohibitions:
    - statement: "Do not enforce a specific test coverage threshold or setup automated CI runs."
      status: "resolved"
      verification: "GitHub Actions directory (.github/workflows) is unmodified and no coverage thresholds are enforced in pytest configs."
    - statement: "Do not write tests for local model execution."
      status: "resolved"
      verification: "No local model testing logic is present in the new test files."
```

## Tasks

```xml
<task>
  <read_first>
    - src/providers.py
    - tests/test_providers.py
  </read_first>
  <action>
    Create `tests/test_providers.py`.
    Add unit tests for `GeminiProvider`, `OpenRouterProvider`, and `GroqProvider`.
    For each provider, mock the respective client (e.g. `google.genai.Client`, `openai.Client`) and verify the `generate()` method constructs the correct prompt content payload. Specifically, verify `GeminiProvider` passes `types.Part.from_bytes` intact, and `OpenRouterProvider`/`GroqProvider` convert byte data using base64 encoding with `data:{mime_type};base64,{b64}`. Verify the provider correctly parses the returned JSON string into the provided Pydantic `BaseModel` (use a dummy `PageClassification` schema for testing) even if the output is surrounded by markdown blocks.
  </action>
  <acceptance_criteria>
    `pytest tests/test_providers.py` runs successfully, reporting 0 failures.
  </acceptance_criteria>
</task>
```

```xml
<task>
  <read_first>
    - src/llm.py
    - tests/test_llm.py
  </read_first>
  <action>
    Update `tests/test_llm.py` to test the updated `LLMClient` implementation and remove obsolete `GemmaClient` references.
    Add `test_llm_auth_error_fails_fast`: Use `unittest.mock.patch.object` on `GeminiProvider.generate` to simulate an Exception containing "401" and verify `LLMClient._route_llm_call` raises the exact exception immediately without routing to the next provider.
    Add `test_llm_429_retry_and_failover`: Mock the primary provider's `generate` method to raise a 429 Rate Limit error. Critically, mock `time.sleep` to prevent actual waiting. Verify that it retries the provider up to 3 times before failing over to the next provider (mock the next provider to succeed and verify it returns a valid payload).
    Add `test_llm_fallback_chain_on_5xx`: Use `unittest.mock.patch.object` on providers' `generate` methods to simulate a 500 error from the first provider (Gemini), a 500 from the second (OpenRouter), and return a valid mocked model from the third (Groq). Verify the client returns the valid payload and doesn't raise an error.
    Add `test_llm_exhaustion`: Simulate all providers' `generate` methods failing with a 500 error, verifying it raises `RuntimeError("LLM routing failed across all providers")`.
  </action>
  <acceptance_criteria>
    `pytest tests/test_llm.py` runs successfully and tests verify fail-fast on 401, 429 retry behavior without actual sleep, failover on 500, and exhaustion error strings.
  </acceptance_criteria>
</task>
```

```xml
<task>
  <read_first>
    - src/pipeline.py
    - tests/test_pipeline.py
  </read_first>
  <action>
    Update `tests/test_pipeline.py` to test `Pipeline` orchestration.
    Update `test_pipeline_fails_fast_on_classification_error` to patch `LLMClient.classify_page_direct` instead of the old direct API caller.
    Add `test_pipeline_cache_hit`: Use a test-specific `.cache.json` file populated with test data containing `category` and `resident`. Configure the pipeline to use this file (e.g., via config or path override). Assert that `Pipeline.process_pdf` correctly loads the cached page and avoids calling the `VisionExtractor` or `CloudExtractor`, without mocking the cache class itself (record/replay approach).
    Add `test_pipeline_interpolate_dates`: Test the internal `Pipeline._interpolate_dates` function by passing a list of mocked `raw_pages` with some missing `"NONE"` dates and assert the holes are filled correctly based on surrounding valid dates.
  </action>
  <acceptance_criteria>
    `pytest tests/test_pipeline.py` runs successfully, proving the real cache file is utilized for integration testing cache hits.
  </acceptance_criteria>
</task>
```

```xml
<task>
  <read_first>
    - src/llm.py
    - tests/test_fallback_chain.py
    - .planning/phases/05-testing/05-RESEARCH.md
  </read_first>
  <action>
    Create `tests/test_fallback_chain.py` to test D-02 (API fallback chain).
    Write `test_live_fallback_invalid_key_fail_fast`: Instantiate `LLMClient` with `api_key="invalid_gemini_key"`, and mock `os.environ` to set `"OPENROUTER_API_KEY"="invalid_or_key"` and `"GROQ_API_KEY"="invalid_groq_key"`. Spy/mock the secondary providers' (OpenRouter and Groq) `generate` methods to ensure they are never called. Call `client.cluster_names(["test"])` and assert that it raises an Exception containing "400" or "api key not valid" (verifying the live fail-fast behavior) AND verify the secondary providers were NOT invoked.
    Write `test_mocked_fallback_chain_integration`: Use `unittest.mock.patch.object` on `GeminiProvider.generate`, `OpenRouterProvider.generate`, and `GroqProvider.generate`. Configure Gemini to raise `Exception("503 Service Unavailable")`, OpenRouter to raise `Exception("500 Internal Error")`, and Groq to return a valid mapping. Call `LLMClient.cluster_names(["test"])` and assert the fallback routed correctly to Groq and returned the expected value.
  </action>
  <acceptance_criteria>
    `pytest tests/test_fallback_chain.py` passes, proving fail-fast aborts explicitly without calling fallbacks, and falls back correctly on 500 errors.
  </acceptance_criteria>
</task>
```
