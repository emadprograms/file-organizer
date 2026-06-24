# Phase 7: Local Pass 1 Inference via Mac Mini M4 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-24
**Phase:** 07-local-pass-1-inference-via-mac-mini-m4
**Areas discussed:** Local server stack, Fallback strategy, Client integration approach

---

## Local Server Stack

| Option | Description | Selected |
|--------|-------------|----------|
| LM Studio | GUI makes it easy to test vision, built-in OpenAI API server | ✓ |
| Ollama | CLI-based, runs as a background service | |
| Direct llama.cpp | Maximum performance, but requires manual setup | |

**User's choice:** Let's use lm studio but is qwen2.5-vl-7b-instruct the best for our use case?
**Notes:** Clarified that Qwen2.5-VL-7B-Instruct is best. User confirmed: "Stick with Qwen2.5-VL-7B-Instruct (Best for our use case)".

---

## Fallback Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid | Fallback to Gemini 4 31b or 2.5 Flash if the local model fails/hangs | ✓ (Modified) |
| Strict Local | Retry locally, but eventually fail the document if the local model can't handle it | |

**User's choice:** fallback to gemini 4 26b. we are retiring both gemini 4 31b and gemini 2.5 flash.
**Notes:** User inquired about DeepSeek V4 Flash. Explained that it is text-primarily and Gemini 4 26b natively supports image inputs. User agreed to use Gemini 4 26b as the fallback.

---

## Client Integration Approach

| Option | Description | Selected |
|--------|-------------|----------|
| `openai` package | Robust, clean API, handles schemas and retries well | ✓ |
| `requests` package | Zero extra dependencies, but requires manual handling of OpenAI's API format | |

**User's choice:** (Recommended) `openai` package: Robust, clean API, handles schemas and retries well
**Notes:** None.

---

## the agent's Discretion

None

## Deferred Ideas

None
