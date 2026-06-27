# Phase 03 Discussion Log

## 1. Fallback Triggers
**Options presented:**
- Exhaust Gemini retries first
- Fall back immediately
- Hybrid: Retry on 429, fall back on 500/503

**Selected:**
Hybrid: Retry on 429, fall back on 500/503

**Notes:**
User clarified: fall back when seeing error 500 or 503 instead of waiting the 15 seconds. Don't fall back on 429, just wait it out.

## 2. Model Selection
**Options presented:**
- Equivalent "Flash" / fast models
- "Pro" / large models
- Open-Source models only

**Selected:**
Custom

**Notes:**
User specified: on OpenRouter same gemma-4-26b-a4b-it model that is already used. On Groq use qwen3.6-27b model.

## 3. Fallback Logging
**Options presented:**
- Add `"provider"` field to JSON cache
- Log to stdout only
- Log to a separate `fallbacks.log` file

**Selected:**
Log to stdout only. Keep the JSON schema clean; just print a message like "Failed over to OpenRouter" during execution.
