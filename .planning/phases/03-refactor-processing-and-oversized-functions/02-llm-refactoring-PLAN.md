---
wave: 2
depends_on:
  - 01-exceptions-and-sys-exit-PLAN.md
files_modified:
  - src/llm/llm.py
  - src/llm/mock.py
autonomous: true
---

# Plan: LLM Refactoring

## Requirements
- REF-03

## Context
Refactor `src/llm/llm.py` to use `tenacity` for backoff instead of hardcoded `time.sleep()`. Also, extract the `--skip-llm` mock logic out of production routing code and into a dedicated `MockLLMProvider`.

## Tasks

<task>
<read_first>
- src/llm/llm.py
- src/llm/providers.py
</read_first>
<action>
Create `src/llm/mock.py`. Define a `MockLLMProvider` class that implements the `LLMProvider` interface. Move the mock schema logic currently in `_route_llm_call` into the `generate` method of `MockLLMProvider`. Ensure the mock logic is resilient to dynamically injected schemas by checking `response_schema.__name__` first, and if the schema is unknown, attempt to instantiate it using default values or mock fields (e.g., using `response_schema.model_construct()` or similar reflection) rather than crashing. 
In `src/llm/llm.py`, if `self.skip_llm` is True, inject `MockLLMProvider` as the only provider into `self.providers`.
</action>
<acceptance_criteria>
- `MockLLMProvider` handles the mock generation logic.
- `MockLLMProvider` can safely return mock instances for dynamically defined schemas without hard-crashing.
- `src/llm/llm.py` no longer contains schema-specific string matching for `--skip-llm`.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/llm/llm.py
</read_first>
<action>
Refactor `_route_llm_call` in `src/llm/llm.py` to use `tenacity.retry` for exponential backoff on 429 and 5xx errors instead of manual `time.sleep(65)` and `time.sleep(7.5)`. Ensure the fallback logic to next providers is preserved (e.g., using a fallback sequence or wrapping the tenacity retry inside the provider loop).
Remove `time.sleep(7.0 - elapsed)` for standard calls.
</action>
<acceptance_criteria>
- `src/llm/llm.py` uses `tenacity.retry` for retrying failed API calls.
- Hardcoded `time.sleep` calls for rate limits are removed.
</acceptance_criteria>
</task>

## Artifacts this phase produces
- `src/llm/mock.py` file
- `MockLLMProvider` class

## Must Haves
### truths
- D-02: Refactor `src/llm/llm.py` to use tenacity and separate mock logic.
- The codebase uses `tenacity` for backoff logic in LLM API calls.

### prohibitions
- `time.sleep` is not used for API backoff.
- Mock logic is not mixed with production routing logic in `_route_llm_call`.
