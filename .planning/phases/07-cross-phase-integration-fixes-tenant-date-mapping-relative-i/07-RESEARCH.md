# Phase 07 Research: Cross-Phase Integration Fixes

## Overview
This phase addresses critical cross-phase integration gaps identified in the v1.0 Milestone Audit. The focus is on fixing tenant identity mapping between Pass 1 and Pass 2, standardizing 0-indexed page boundaries internally while surfacing 1-indexed boundaries externally, implementing fallback routing, and adding CLI flags for better debuggability and testing.

## Identified Gaps to Resolve
Based on `.planning/v1.0-MILESTONE-AUDIT.md`, the following gaps must be addressed:
1. **GRP-01 / Phase 2 -> Phase 3 Integration**: `Pipeline._group_and_route_documents()` incorrectly reads `residents` instead of `canonical_tenant`.
2. **OUT-02**: Tenant identities resolving to `None` causes the creation of `UNKNOWN` folders instead of correctly mapping them.
3. **LOG-04**: Internal 0-indexed page bounds are bleeding into the UI/Logging, causing confusing output. They must be converted to 1-indexed for display.
4. **LLM-08 & GRP-10**: Lack of CLI mock flags (`--skip-llm`) to quickly verify routing and fallbacks E2E without real LLM latency.

## Key Implementation Decisions
From `07-CONTEXT.md`:
1. **0-Indexing Internally**: The core engine, PyMuPDF, and logic boundaries must uniformly operate on 0-indexed arrays. Only logging and UI will present 1-indexed values (D-01).
2. **Concise Dry-Run**: `--dry-run` output should be clean, showing just a tree of folders and files, suppressing LLM verbosity (D-02).
3. **Fallback Routing**: Any unresolvable documents should safely land in an `Unassigned` folder to guarantee pipeline completion, flagging it in the logs (D-03).
4. **CLI Flags**: Introduction of `--verbose` (output full LLM prompt/responses and verbose logs) and `--skip-llm` (mock LLM responses for faster layout/routing testing) alongside `--dry-run` (D-04).

## Existing Code Context
- `Pipeline`: Needs updating to pass `canonical_tenant` correctly and apply the 'Unassigned' fallback logic for unresolvable mapping.
- `cli.py` / `organize.py`: Argument parsers need `--verbose` and `--skip-llm` wired into logging and the LLM client configuration.
- `llm_client.py` / `models.py`: Needs to intercept calls when `--skip-llm` is active and return mock structured responses.
- `pdf_utils.py` and UI logs: Confirm PyMuPDF slicing uses 0-indexed rules appropriately and ensure logging converts indices to 1-indexed cleanly.

## Validation Architecture
- **Tenant Mapping Verification**: Unit and integration tests must assert that Pass 2 consumes `canonical_tenant` and never reads the raw `residents` list, ensuring no `UNKNOWN` folders are created from valid tenant data.
- **Indexing Consistency**: Tests must assert that boundary models store 0-indexed values, but all console logs and output reports render exactly `internal_index + 1`.
- **Dry-Run & CLI Mocking**: End-to-end tests using `--skip-llm` and `--dry-run` to assert that the console renders a clean file tree without executing real network calls.
- **Fallback Verification**: Inject an unresolvable page and assert it is routed to the `Unassigned` folder, avoiding pipeline crashes or missing pages.
