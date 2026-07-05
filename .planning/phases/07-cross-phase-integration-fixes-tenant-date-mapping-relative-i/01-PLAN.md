---
wave: 1
depends_on: []
requirements: [GRP-01, OUT-02, LOG-04, LLM-08, GRP-10]
files_modified:
  - src/processing/pipeline.py
  - src/processing/grouping.py
  - src/processing/organizer.py
  - src/organize.py
  - src/logger.py
  - src/llm/llm.py
autonomous: true
---

# Phase 07: Cross-Phase Integration Fixes

## Requirements Addressed
- GRP-01: Pre-split page sequence by category (Pass 2 reads canonical_tenant)
- OUT-02: Create tenant-level directories with timeline in name (No UNKNOWN folders)
- LOG-04: Reconciliation report / CLI logs (Exposes internal 0-indexed bounds)
- LLM-08 & GRP-10: Missing CLI mock flags to verify fallback robustness E2E

## Tasks

<task>
<read_first>
- src/processing/grouping.py
- src/processing/pipeline.py
</read_first>
<action>
In `src/processing/pipeline.py` `_group_and_route_documents()`, update the pre-split logic to use `canonical_tenant` instead of `residents`.
Replace `res_0 = getattr(pages_only[0], "residents", [])` and `current_resident = res_0[0] if res_0 else None` with `current_resident = getattr(pages_only[0], "canonical_tenant", None)`.
Replace `res = getattr(page, "residents", [])` and `resident = res[0] if res else None` with `resident = getattr(page, "canonical_tenant", None)`.

In `src/processing/grouping.py` `process_with_shrink()`, update the `primary_tenant` extraction.
Replace `res = getattr(g_pages[0], "residents", [])` and `primary_tenant = res[0] if res else "UNKNOWN"` with `primary_tenant = getattr(g_pages[0], "canonical_tenant", "Unassigned")`.
If `primary_tenant` resolves to `"Unassigned"`, add a `logger.warning` explicitly flagging that the tenant could not be resolved and is falling back to "Unassigned" for this group.
</action>
<acceptance_criteria>
- `pipeline.py` pre-split checks `canonical_tenant` and doesn't read the `residents` array.
- `grouping.py` groups set `primary_tenant` to `canonical_tenant` with a default of `"Unassigned"`.
- A warning log is emitted whenever a document's tenant falls back to `"Unassigned"`.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/processing/organizer.py
</read_first>
<action>
In `src/processing/organizer.py` `organize()`:
1. Find the logger lines that output extraction bounds. Change 0-indexed to 1-indexed: `logger.info(f"  → {filename} (pages {doc.start_page + 1}-{doc.end_page + 1})")`.
2. For the `--dry-run` output, build and display a `rich.tree.Tree` instead of flat logs. Construct the tree to reflect the planned folders (Tenant -> Category) and the files within them (displaying the 1-indexed page bounds). Use `rich.console.Console` to print the tree and remove the old flat `[DRY RUN]` logger lines.
</action>
<acceptance_criteria>
- `organizer.py` logs 1-indexed page bounds (by adding 1) for regular console logs.
- `organizer.py` generates and displays a structured `rich.tree.Tree` showing the planned folder hierarchy and files for the `--dry-run` output.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/logger.py
- src/organize.py
</read_first>
<action>
In `src/logger.py` `setup_logging()`, add a `verbose: bool = False` argument.
Configure the `stream_handler` level to `logging.DEBUG` if `verbose` is `True`, otherwise `logging.INFO`. (The file handler can remain `logging.DEBUG`).

In `src/organize.py`:
Add `--verbose` (action="store_true") and `--skip-llm` (action="store_true") arguments to the CLI parser.
Pass `verbose=args.verbose` to `setup_logging()`.
After creating `llm_client`, set `llm_client.skip_llm = args.skip_llm` and `llm_client.verbose = args.verbose`.
</action>
<acceptance_criteria>
- `organize.py` CLI parser accepts `--verbose` and `--skip-llm`.
- `setup_logging` dynamically changes the stream handler's logging level based on the `--verbose` flag.
</acceptance_criteria>
</task>

<task>
<read_first>
- src/llm/llm.py
</read_first>
<action>
In `src/llm/llm.py`:
In the `LLMClient._route_llm_call` method, inject mock behavior at the top if `getattr(self, "skip_llm", False)` is True.
Return mocked schema objects depending on `response_schema.__name__`:
- If `GroupingResponse`: parse the chunk bounds from the `contents` string (e.g., using `re.search(r'Chunk range: Page (\d+) to Page (\d+)', contents_str)`). Return a `GroupingResponse` with a single group spanning those bounds, `reason="mock skip-llm"`, and `brief_arabic_title="عنوان تجريبي"`. If parsing fails, default to 0-0.
- If `RoutingResponse`: Return a `RoutingResponse(selected_folder="13_others")`.
- If `response_schema` is None: return `"mock plain text response"`.

Additionally, if `getattr(self, "verbose", False)` is True, add `log.debug` statements in `_route_llm_call` to print the prompt and the generated response (just before returning).
</action>
<acceptance_criteria>
- If `skip_llm` is True, `_route_llm_call` returns valid mocked schemas without network calls.
- Mocked `GroupingResponse` parses the bounds correctly from the prompt so that chunk boundaries match and don't fail verification.
- If `verbose` is True, `_route_llm_call` logs prompts and outputs using `log.debug`.
</acceptance_criteria>
</task>

## Verification
- `pytest` on existing tests should pass.
- `--skip-llm` enables e2e tests without real API keys, generating correct mocked outputs.
- No `UNKNOWN` folder is created for missing residents, defaulting safely to "Unassigned".

## must_haves
```yaml
truths:
  - src/processing/pipeline.py contains "canonical_tenant"
  - src/processing/organizer.py contains "doc.start_page + 1"
  - src/organize.py contains "--skip-llm"
  - src/organize.py contains "--verbose"
```

## Artifacts this phase produces
- CLI flags: `--verbose`, `--skip-llm`
- Object properties: `LLMClient.skip_llm`, `LLMClient.verbose`
