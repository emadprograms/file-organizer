---
objective: "Wire CLI to execute Pass 2 Grouping and Routing"
wave: 7
depends_on: [6]
files_modified:
  - src/organize.py
autonomous: true
requirements:
  - GRP-11
must_haves:
  truths:
    - src/organize.py successfully executes Pass 2 (Grouping and Routing) after Pass 1 Document Cleaning
    - src/organize.py calls FileOrganizer to generate the final split PDFs
    - The entry point correctly bridges the PageData output of cleaning.py to the pipeline's Grouping/Routing logic
  artifacts:
    - none
---

# Plan 7: Wire CLI to execute Pass 2 Grouping and Routing

## Objective
The UAT for Phase 3 identified a critical gap: the pipeline integration was done inside `src/processing/pipeline.py` but the new CLI entry point for this post-processor tool (`src/organize.py`) only executes Pass 1 (Document Cleaning) and stops. This plan will wire `src/organize.py` to execute Pass 2 and physically generate the PDFs using `FileOrganizer`.

## Tasks

```xml
<task>
  <files>
    - src/organize.py
  </files>
  <read_first>
    - src/organize.py
    - src/processing/pipeline.py
    - src/processing/organizer.py
  </read_first>
  <action>
    Modify `main()` in `src/organize.py` to run Pass 2 Grouping and Routing after Pass 1 completes.
    
    After `cleaned_pages` is successfully generated and logged:
    1. Import `Pipeline` from `src.processing.pipeline` and `FileOrganizer` from `src.processing.organizer`.
    2. Format `cleaned_pages` for the pipeline by constructing `raw_pages = [(p.original_index, p) for p in cleaned_pages]`.
    3. Instantiate a dummy `Pipeline(api_key=os.getenv("GEMINI_API_KEY"))` and override its `client` with the existing `llm_client` (to preserve error counters and rate limit tracking).
    4. Call `pipeline._group_pages_into_documents(raw_pages, None)` to get the `list[DocumentGroup]`.
    5. Find the source PDF path (from `args.target_dir.glob("*_categorized.pdf")`).
    6. Define `output_dir = args.target_dir / "output" / house_id` (so it creates the house-level directory inside output/).
    7. Instantiate `FileOrganizer()` and call `organizer.organize(documents, str(pdf_path), output_dir, None)`.
    8. Log the final summary mapping (number of PDFs generated and the output directory).
  </action>
  <acceptance_criteria>
    - `src/organize.py` imports `Pipeline` and `FileOrganizer`
    - `pipeline._group_pages_into_documents(raw_pages, None)` is successfully called with the mapped list of tuples
    - `organizer.organize(...)` is successfully called with the correct `output_dir` ending in the `house_id`
    - Execution does not crash when processing a standard categorized PDF and JSON report pair
  </acceptance_criteria>
</task>
```

## Verification
- Run `python src/organize.py [path_to_directory]` on a valid directory and ensure it completes both Pass 1 and Pass 2, outputting PDFs in the `output/` directory.

## Artifacts this phase produces
- Modified `src/organize.py` CLI script behavior.
