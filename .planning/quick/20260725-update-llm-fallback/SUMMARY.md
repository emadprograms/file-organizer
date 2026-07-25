---
status: complete
---

# Summary: Update LLM Fallback and Models

- Changed `gemini-3-flash` to `gemini-3-flash-preview` in `src/grouping/core.py` and `src/llm/llm.py`.
- Changed default model from `gemini-3.1-flash-lite` to `gemini-3.5-flash-lite` in:
  - `README.md`
  - `docs/API.md`
  - `docs/CONFIGURATION.md`
  - `src/core/config.py`
- Updated LLM fallback list in `src/grouping/core.py` and `src/llm/llm.py` to the requested sequence.
- Updated CLI argument choices in `src/main.py` to include the new models.
- Updated `STATE.md` with the completed quick task.
