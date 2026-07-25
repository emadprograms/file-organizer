# Plan: Update LLM Fallback and Models

1. Change `gemini-3-flash` to `gemini-3-flash-preview` in `src/grouping/core.py` and `src/llm/llm.py`.
2. Change default model from `gemini-3.1-flash-lite` to `gemini-3.5-flash-lite` in:
   - `README.md`
   - `docs/API.md`
   - `docs/CONFIGURATION.md`
   - `src/core/config.py`
3. Update LLM fallback list in `src/grouping/core.py` and `src/llm/llm.py` to:
   - gemini-3.5-flash-lite
   - gemini-3.1-flash-lite
   - gemini-3.6-flash
   - gemini-3.5-flash
   - gemini-3-flash-preview
   - gemini-2.5-flash
4. Update CLI argument choices in `src/main.py` to include the new models.
5. Update `STATE.md` with the completed quick task.
6. Create `SUMMARY.md` in this directory.
7. Commit changes automatically.
