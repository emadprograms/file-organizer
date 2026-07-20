# Phase 21: System Unification - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-19T21:35:25+03:00
**Phase:** 21-system-unification
**Areas discussed:** Module Placement, LLM Client Integration, OCR Integration Strategy, Bypass Logic (CAT-02)

---

## Module Placement

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) New `src/categorization/categorization.py` | Runs before `cleaning.py`, keeps `main.py` lean and preserves functional pipeline | ✓ |
| Inside `src/main.py` | Simpler, but might bloat the entry point | |
| Inside `src/cleaning.py` | Piggyback on Pass 1, though it mixes file analysis with entity resolution | |
| You decide | | |

**User's choice:** (Recommended) New `src/categorization/categorization.py`
**Notes:** None

---

## LLM Client Integration

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Adapt to use existing `LLMClient` wrapper | Maintains consistency, retry logic, and JSON schema enforcement | ✓ |
| Keep standalone API calls | Less refactoring of the ported code, but duplicates API logic | |
| You decide | | |

**User's choice:** (Recommended) Adapt to use existing `LLMClient` wrapper
**Notes:** None

---

## OCR Integration Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| PyMuPDF text first with OCR fallback | Use PyMuPDF text first; if empty, fallback to Gemini 3.1 Flash multimodal (no new local dependencies) | |
| Integrate a local OCR library | Integrate a local OCR library like Tesseract/pdf2image (More robust but heavier setup) | |
| You decide | | |
| (Other) | Port `image_processing.py` and `ai_classification.py` exactly as they are without text-based OCR fallbacks. | ✓ |

**User's choice:** Port `image_processing.py` and `ai_classification.py` exactly as they are without text-based OCR fallbacks. Render pages to high-res images, use OpenCV cleaning pipeline, and send optimized images directly to Gemini's vision endpoint.
**Notes:** User emphasized that the pipeline in `../file-categorizer` was perfected over 100 commits and does not use PyMuPDF for text extraction. It relies solely on a robust OpenCV image processing pipeline + Gemini vision endpoint.

---

## Bypass Logic (CAT-02)

| Option | Description | Selected |
|--------|-------------|----------|
| (Recommended) Co-located with the PDF | E.g., `document.pdf` checks for `document_report.json` in the same directory (Simpler and keeps data together) | ✓ |
| Dedicated reports folder | E.g., `.reports/document_report.json` (Keeps the inbox clean, but separates related files) | |
| You decide | | |

**User's choice:** (Recommended) Co-located with the PDF (in the same directory).
**Notes:** Explained that the JSON report must be in the exact same directory as the PDF to be detected.

---

## the agent's Discretion

None

## Deferred Ideas

None
