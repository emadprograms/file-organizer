# Phase 08 Summary: "True Until Proven Guilty" Grouping Logic

## Goal
Transition the document grouping logic from a generic, single-prompt approach to a category-aware hybrid routing system. The primary objective was to prevent over-splitting of correspondence (letters) and implement high-reliability deterministic paths for specific document categories.

## Implementation Details

### 1. Prompt Infrastructure
- Created `src/processing/grouping/config.py` to decouple prompts from logic.
- Defined three specialized prompt templates:
    - `LETTER_PROMPT`: Implements the "True Until Proven Guilty" philosophy. It instructs the LLM to assume pages are part of the same "Correspondence Story" unless a definitive "Hard Reset" in subject is detected. It explicitly forbids splitting on un-headered tables or appendices.
    - `FORM_PROMPT`: Standard boundary detection for generic forms.
    - `OTHER_PROMPT`: High-precision, low-chunk-size detection for miscellaneous content.

### 2. Core Logic Refactoring (`src/processing/grouping/core.py`)
- **`_process_chunk`**: Refactored to accept a `prompt_template` and a `content_field`. It now dynamically extracts text from the specified field (e.g., `subject` for letters) with a fallback to `content_explanation`.
- **`process_with_shrink` (Hybrid Routing)**:
    - **Deterministic Bypass**: 
        - `contract`, `id_cards`: Automatically grouped into a single `DocumentGroup`.
        - `utility_bills`: Automatically split into one `DocumentGroup` per page.
        - These paths bypass the LLM entirely, ensuring 100% reliability and reducing token cost.
    - **Dynamic LLM Routing**: 
        - `others`: Routes to `OTHER_PROMPT` with a strict `CHUNK_SIZE` of 2.
        - `letters`: Routes to `LETTER_PROMPT` using the `subject` field for context.
        - `default`: Routes to `FORM_PROMPT`.

## Outcomes
- **Increased Precision**: Letters are less likely to be fragmented by tables or appendices.
- **Improved Performance**: Deterministic paths remove LLM latency and cost for the most common stable categories.
- **Flexibility**: The system can now be tuned per-category by simply updating the config file without touching core logic.

## Deviations
None. The implementation strictly followed the plan defined in `08-01-PLAN.md`.
