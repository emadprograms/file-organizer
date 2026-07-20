# Phase 23: inbox-parsing-and-syntax - Context

**Gathered:** 2026-07-20T17:45:00+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Building the space-separated syntax parser for the File-System UI (FS-UI) and implementing the logic for inferring missing data (the 'U' flag). This phase handles the filename parsing and logic resolution, while the actual File-System UI orchestration loop (renaming and waiting for approval) is deferred to Phase 24.
</domain>

<decisions>
## Implementation Decisions

### Syntax Strictness & Title Override
- **D-01:** The parser expects exactly 5 space-separated positional arguments: `[AREA] [HOUSE] [TENANT_HINT] [GROUP] [DATE]`.
- **D-02:** Any trailing text after the 5th token is captured and used as the document's Title. This completely bypasses the need to ask the LLM for a title during the grouping phase.
- **D-03:** If a file does not match the 5-part space-separated format at all, it is considered invalid and renamed with an `_Error_Invalid_Format` suffix immediately.

### Inferring Missing Data ('U')
- **D-04:** Missing data is inferred by running the standard categorization pipeline (`categorization.py`) to generate `_report.json`.
- **D-05:** House and Date are inferred by extracting the values from `_report.json` and using a majority-vote logic across all pages of the document.

### Group Parameter Logic (`[GROUP]`)
- **D-06:** The group parameter can ONLY be a number (`1` to `13`), `G`, or `U`.
- **D-07:** If `[GROUP]` is a number (`1` to `13`), the file is treated as pre-grouped and pre-routed. These numbers correspond directly to the 13 standard subfolders inside each tenant's directory. The pipeline skips both grouping and routing, and places the document in the specified folder (updating `.source_files/` accordingly), resolving any timeline conflicts by giving the latest tenant priority.
- **D-08:** If `[GROUP]` is `G`, the file is pre-grouped (do not split) but the topic is unknown. The pipeline skips grouping but runs routing.
- **D-09:** If `[GROUP]` is `U`, the file is treated as a raw monolith. The pipeline runs BOTH grouping and routing.

### Area Conflicts
- **D-10:** Area is not extracted in `_report.json`. The system scans the areas defined in `config.yaml` to find the inferred House number.
- **D-11:** If the inferred House number exists in multiple areas, the parser refuses to process it and proposes a rename showing the conflict (e.g., `saf/uh 1273 U U 2026 - please choose area.pdf`), forcing the user to resolve it manually.

### Tenant Override
- **D-12:** If the user provides a `TENANT_HINT` (e.g., `Ali`), the system uses the Pass 1 LLM canonicalization logic to match the hint against the existing canonical tenants for that house. If the user does not want to override the tenant, they use `U` and rely on standard timeline logic.

### the agent's Discretion
None — User made specific choices for syntax logic.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture and Requirements
- `.planning/REQUIREMENTS.md` — Defines FSUI-01, FSUI-02, FSUI-03.
- `.planning/codebase/ARCHITECTURE.md` — Explains the separation of Pass 1 (cleaning/canonicalization) and Pass 2 (grouping/routing) which the parser must interact with.
- `.planning/codebase/CONVENTIONS.md` — Highlights use of `pydantic` schemas which should be used to build the parser output model.

### Prior Phase Context
- `.planning/phases/21-system-unification/21-CONTEXT.md` — Explains `categorization.py` generating `_report.json` which is heavily relied upon for 'U' field inference.
- `.planning/phases/22-configuration-and-cli-modes/22-CONTEXT.md` — Details `config.yaml` and the `append` CLI hook that this parser will run under.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/categorization/categorization.py` — Must be called to generate `_report.json` for inferring 'U' fields.
- `src/cleaning.py` — Pass 1 LLM canonicalization logic should be reused/adapted for resolving the `TENANT_HINT` to an exact folder name.

### Established Patterns
- Pydantic models in `src/core/schemas.py`: The parser should output a validated Pydantic model representing the parsed 5-part filename and the parsed Title.

### Integration Points
- `src/main.py`: The `append` subcommand handler (created in Phase 22) will invoke this parser on files found in the inbox.
</code_context>

<specifics>
## Specific Ideas

- The user specifically requested that trailing text be used as the document title to bypass the LLM title generation in grouping.
- The `[GROUP]` logic (`1-13` = skip both, `G` = skip grouping, `U` = run both) is a very specific implementation detail provided by the user that overrides any generic pipeline assumptions.

</specifics>

<deferred>
## Deferred Ideas

- The actual FS-UI orchestrator loop that watches the inbox, proposes filenames (e.g. appending `_Proposed`), waits for ` OK`, and finalizes the files is deferred to Phase 24.
</deferred>

---

*Phase: 23-inbox-parsing-and-syntax*
*Context gathered: 2026-07-20T17:45:00+03:00*
