---
wave: 1
depends_on: "Phase 4"
files_modified:
  - "src/utils.py"
  - "src/organizer.py"
  - "src/llm.py"
  - "src/pipeline.py"
autonomous: true
requirements: []
must_haves:
  truths:
    - "D-01: Separate the orchestration logic in pipeline.py into distinct class-based extractors (e.g., VisionExtractor, CloudExtractor) instead of functional decomposition within a single massive process_pdf method."
    - "D-02: Use the Strategy Pattern with separate Provider classes (e.g., GeminiProvider, OpenRouterProvider, GroqProvider) in llm.py to handle provider-specific logic, extracting the retry and fallback routing out of the monolithic _route_llm_call."
    - "D-03: Extract the date parsing, string normalization, and filename sanitization logic from organizer.py into a new dedicated utils.py module to keep the Organizer focused strictly on file operations."
---

# Plan: Refactor Core Modules

## Threat Model
<threat_model>
asvs_level: 1
block_on: "high"
description: "Refactoring phase with no new capabilities. Focus on avoiding security regressions in cloud API logic."
</threat_model>

## Artifacts this phase produces
- **File paths**: `src/utils.py`
- **Classes**: 
  - `GeminiProvider` (in `src/llm.py`)
  - `OpenRouterProvider` (in `src/llm.py`)
  - `GroqProvider` (in `src/llm.py`)
  - `VisionExtractor` (in `src/pipeline.py`)
  - `CloudExtractor` (in `src/pipeline.py`)
  - `LLMProvider` (in `src/llm.py`)
  - `LLMClient` (in `src/llm.py`)
- **Functions**:
  - `sanitize_filename` (in `src/utils.py`)
  - `normalize_date` (in `src/utils.py`)
  - `parse_datetime_str` (in `src/utils.py`)

## Tasks

### Wave 1

<task id="task_1">
<read_first>
- src/organizer.py
- .planning/phases/04.1-refactor-core-modules-refactor-llm-py-pipeline-py-and-organi/04.1-PATTERNS.md
</read_first>
<action>
Extract `_sanitize_filename`, `_normalize_date`, and `_parse_datetime_str` from `FileOrganizer` in `src/organizer.py` into a new file `src/utils.py` as standalone functions `sanitize_filename`, `normalize_date`, and `parse_datetime_str`.
Update `src/organizer.py` to import these functions from `src/utils.py`.
Modify `FileOrganizer._generate_pdf_name` and any other calling methods to use `utils.sanitize_filename`, `utils.normalize_date`, and `utils.parse_datetime_str` instead of `self._sanitize_filename`, `self._normalize_date`, and `self._parse_datetime_str`.
</action>
<acceptance_criteria>
- `grep "def sanitize_filename(" src/utils.py` returns a match.
- `grep "def normalize_date(" src/utils.py` returns a match.
- `grep "import" src/organizer.py` includes `utils`.
- `grep "def _sanitize_filename(" src/organizer.py` returns no matches.
</acceptance_criteria>
</task>

<task id="task_2">
<read_first>
- src/llm.py
- src/schemas.py
- .planning/phases/04.1-refactor-core-modules-refactor-llm-py-pipeline-py-and-organi/04.1-PATTERNS.md
</read_first>
<action>
In `src/llm.py`, define an `LLMProvider` protocol or base class.
Rename `GemmaClient` to `LLMClient` and update any codebase references.
Create `GeminiProvider`, `OpenRouterProvider`, and `GroqProvider` classes in `src/llm.py` that implement the `LLMProvider` interface.
Move the provider-specific logic from `LLMClient._route_llm_call` into the respective provider classes.
Refactor `LLMClient._route_llm_call` to delegate calls to the appropriate provider class. Ensure the Provider classes are instantiated once during `LLMClient` initialization rather than re-instantiated on every call.
</action>
<acceptance_criteria>
- `grep "class GeminiProvider" src/llm.py` returns a match.
- `grep "class OpenRouterProvider" src/llm.py` returns a match.
- `grep "class GroqProvider" src/llm.py` returns a match.
- `grep "def _route_llm_call" src/llm.py` still exists but delegates to providers.
</acceptance_criteria>
</task>

### Wave 2

<task id="task_3">
<read_first>
- src/pipeline.py
- src/llm.py
- .planning/phases/04.1-refactor-core-modules-refactor-llm-py-pipeline-py-and-organi/04.1-PATTERNS.md
</read_first>
<action>
In `src/pipeline.py`, create `VisionExtractor` and `CloudExtractor` classes to handle the classification logic.
Inject `SimpleCache` (which must remain in `src/pipeline.py`) into the `__init__` methods of these Extractor classes.
Refactor `Pipeline.process_pdf` to instantiate `VisionExtractor` and `CloudExtractor` and call their methods to process the PDF, replacing the inline classification logic.
</action>
<acceptance_criteria>
- `grep "class VisionExtractor" src/pipeline.py` returns a match.
- `grep "class CloudExtractor" src/pipeline.py` returns a match.
- `grep "class SimpleCache" src/pipeline.py` returns a match.
- `grep "Extractor(" src/pipeline.py` returns a match to verify `process_pdf` delegates to the extractors.
</acceptance_criteria>
</task>
