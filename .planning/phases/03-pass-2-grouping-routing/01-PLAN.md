---
wave: 1
depends_on: []
files_modified:
  - src/core/schemas.py
autonomous: true
---

# Phase 3 - Plan 1: Core Schemas and Data Models

## Requirements
- GRP-04: LLM reasoning field
- GRP-05: Strict JSON response with start/end page, reason, title

## Review Feedback Incorporation
- **Schema Consistency (Gemini - LOW)**: Converted `DocumentGroup` from `@dataclass` to Pydantic `BaseModel` to align with the rest of the project and ensure robust validation of new fields.
- **Single-Match Filename Gap (Antigravity - MEDIUM)**: Added `is_direct_routed: bool = False` to `DocumentGroup` so downstream naming logic knows when to drop the `{brief_arabic_title}`.

## Tasks

```xml
<task>
  <action>Refactor `DocumentGroup` to Pydantic `BaseModel` and add new fields</action>
  <read_first>
    - src/core/schemas.py
  </read_first>
  <acceptance_criteria>
    - `DocumentGroup` inherits from `BaseModel` instead of using `@dataclass`.
    - `DocumentGroup` includes `reason: str | None = None`.
    - `DocumentGroup` includes `brief_arabic_title: str | None = None`.
    - `DocumentGroup` includes `folder_path: str | None = None`.
    - `DocumentGroup` includes `is_direct_routed: bool = False`.
  </acceptance_criteria>
</task>

<task>
  <action>Create `GroupEntry` and `GroupingResponse` Pydantic schemas</action>
  <read_first>
    - src/core/schemas.py
  </read_first>
  <acceptance_criteria>
    - `GroupEntry` is a `BaseModel` with `start_page: int`, `end_page: int`, `reason: str`, and `brief_arabic_title: str`.
    - Field descriptions are provided for `GroupEntry` fields indicating 0-indexed values for pages.
    - `GroupingResponse` is a `BaseModel` with `groups: list[GroupEntry]`.
  </acceptance_criteria>
</task>
```

## Verification
- Run `pytest` to ensure schema changes do not break existing tests that rely on `DocumentGroup` initialization.

## Must Haves
- `DocumentGroup` must be a Pydantic `BaseModel`.
- `is_direct_routed` flag must be present on `DocumentGroup`.

## Artifacts this phase produces
- `DocumentGroup` (Modified Class)
- `GroupEntry` (New Class)
- `GroupingResponse` (New Class)
