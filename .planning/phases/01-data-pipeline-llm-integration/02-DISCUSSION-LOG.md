# Phase 2: LLM Integration - Discussion Log

**Date:** 2026-06-21

This log captures the raw discussion that led to the decisions in `02-CONTEXT.md`.
It is for human reference only. Downstream agents should read `02-CONTEXT.md` instead.

## 1. API Provider and Schema
- **Options presented:** Local Ollama, Groq, Together vs Google API. Schema enforcement libraries.
- **Selection:** Google API key
- **Notes:** User is using a Google API key. Unsure if JSON schema enforcement works natively on this endpoint; instructed to try native first, fallback to prompt engineering if needed.

## 2. Page Context Strategy
- **Options presented:** Independent pages vs sliding window vs accumulating window.
- **Selection:** Accumulating sliding window
- **Notes:** User stated independent processing gave horrible results. The window will dynamically accumulate pages until the LLM indicates a topic change.

## 3. Rate Limiting & Concurrency
- **Options presented:** Sequential processing vs parallel processing.
- **Selection:** Sequential
- **Notes:** User prefers sequential processing because it's slower but safer and more correct, guaranteeing proper context accumulation.

## 4. Arabic Name Normalization
- **Options presented:** Exact extraction vs intelligent normalization.
- **Selection:** Intelligent normalization
- **Notes:** Since all letters are in Arabic, the AI should group variations like "Al Muhammad" and "Muhammad" together.

## 5. Fallback Behavior
- **Options presented:** Retry prompt vs drop to Uncategorized folder.
- **Selection:** Retry prompt
- **Notes:** User explicitly instructed to retry and not to drop pages.

## 6. House Generic Letters
- **Options presented:** Standard output vs specific constant for generic letters.
- **Selection:** Specific constant
- **Notes:** LLM will output `"Resident": "NONE"` for Amar Takhsees and generic house letters.
