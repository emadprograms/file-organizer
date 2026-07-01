# Phase 2: Pipeline Adaptation (Extraction & Cleaning) - Discussion Log

**Date:** 2026-07-01

## 1. Prompt Templating Strategy
**Options presented:**
- Just the rules — Pipeline handles the AI prompting wrapper, user just lists what they want.
- Full control — User writes the entire prompt, giving them maximum flexibility.

**Selected:** Full control (Option B). User writes the prompt exactly how they want it sent to the AI.

## 2. Dynamic Schema Extraction
**Options presented:**
- Option A (Strict Schema) — The user defines the fields and types (string, date, boolean) in the YAML config. We dynamically build a Pydantic model so the AI is forced to return perfectly typed data.
- Option B (Flexible JSON) — We just ask the AI to return a JSON dictionary. The pipeline passes whatever the AI returns to the next stage without strict type checking.

**Selected:** Option A (Strict Schema). Pipeline strictly checks types and retries if the AI hallucinate bad formats.

## 3. Cleaning Rules Definition (Pass 1.5)
**Options presented:**
- Option A (LLM Cleaning) — The user writes a prompt (e.g., "Fill missing dates, group aliases") and we pass the whole dataset to the LLM to clean it, replacing the hardcoded Python logic entirely.
- Option B (Python Scripting) — The user provides a path to their own Python script to do this kind of complex timeline logic themselves.
- Option C (Provide Both) — The config lets the user choose whether to use an LLM prompt or a custom Python script for their cleaning pass.

**Selected:** Option C (Provide Both).

## Deferred Ideas
None.
