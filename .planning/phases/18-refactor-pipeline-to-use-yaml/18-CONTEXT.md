# Phase 18: Refactor Pipeline to use YAML - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate YAML-driven configuration into the pipeline to replace anchor logic for tenant extraction and routing. Support a dual-mode execution strategy (Initial Discovery vs. Incremental Update) to automate tenant discovery while allowing manual YAML overrides for one-off document routing.
</domain>

<decisions>
## Implementation Decisions

### 1. File Safety & Organization (Pipeline Finalization)
- **D-01:** The `*_categorized.pdf` file remains in the root target directory instead of being moved to `source_files/`.
- **D-02:** The `source_files` directory is renamed to `.source_files` to hide it.
- **D-03:** Only the `*_report.json` and the `.run_cache` JSON checkpoints are moved into `.source_files/`.

### 2. YAML Structure & Generation
- **D-04:** `tenants.yaml` resides in the root directory for easy manual editing.
- **D-05:** Format must be a list of tenant objects with `name`, `start_date`, and `end_date` (can be `"present"` for the latest).
- **D-06:** **Initial Discovery (No YAML):** Pass 1 runs the current strict Anchor Logic (>=1 anchor, >=5 pages). After extracting timelines, it automatically generates `tenants.yaml` with discovered tenant names, their earliest date as `start_date`, and their latest date as `end_date` (or `"present"`).

### 3. Name Cleaning Workflow (Incremental Update via YAML)
- **D-07:** When `tenants.yaml` exists, the LLM is explicitly provided the tenant names from the YAML. It maps any raw OCR names strictly to these known identities.
- **D-08:** **Anchor Logic Bypassed:** If YAML exists, the 1-anchor/5-page rule is skipped entirely, validating any manually added tenants immediately.

### 4. Missing Tenant Handling (Timeline Fallback)
- **D-09:** For documents where the LLM cannot extract any tenant name (or no name is mentioned), Pass 1 uses the timelines strictly from `tenants.yaml`.
- **D-10:** **Has Date, No Name:** Assign to the tenant whose YAML timeline covers the document's date. If the date falls into an overlapping period between multiple tenants, assign it to the **latest** tenant in that overlap.
- **D-11:** **No Date, No Name (e.g., Pictures):** Assign to the latest tenant overall (the one marked with `end_date: "present"`).

### Claude's Discretion
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & Requirements
- `.planning/PROJECT.md` — Defines the Logic-Based Modular Refactoring constraints

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/tenant_config/tenants.py` — Contains current anchor logic that needs to be conditionally bypassed.
- `src/timeline/phase.py` — Contains `process_cleaning_phase` where the dual YAML mode logic (Initial vs Incremental) will be orchestrated.
- `src/main.py` — Handles file movement (modifications needed for PDF placement and `.source_files`).

### Established Patterns
- LLM prompt manipulation inside `canonicalize_with_llm` to inject dynamic constraints (YAML names).

### Integration Points
- `src/main.py` must use the hidden `.source_files` directory.
- `src/timeline/phase.py` must check for the presence of `tenants.yaml` before proceeding with `canonicalize_with_llm`.

</code_context>

<specifics>
## Specific Ideas
- Overlapping timeline fallback strategy resolves cleanly to the newest tenant.
- YAML acts as the supreme source of truth for both tenant identity and timelines when present.

</specifics>

<deferred>
## Deferred Ideas
None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-Refactor Pipeline to use YAML*
*Context gathered: 2026-07-15*
