# Phase 22: Configuration and CLI Modes - Context

**Gathered:** 2026-07-20T11:38:00+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Create `config.yaml` and setup explicit CLI commands (`create` and `append`). This phase delivers the configuration structure and CLI hooks, but defers the actual FS-UI listener behavior (parsing filenames, LLM inference, the rename/approval loop) to Phase 23/24.
</domain>

<decisions>
## Implementation Decisions

### Configuration Management
- **D-01:** `config.yaml` will store `inbox_path`, `areas_root_path`, and `area_mappings`.
- **D-02:** `.env` remains strictly for secrets (API keys) and is not replaced by `config.yaml`.
- **D-03:** Load and validate `config.yaml` using a Pydantic Settings class.

### Missing Directories Handling
- **D-04:** If `inbox_path` or `areas_root_path` do not exist on disk when the system starts, the script will automatically create them (`mkdir -p`) rather than failing.

### `create <path>` Execution Boundaries
- **D-05:** Strict path constraint: The `<path>` passed to the `create` command MUST be located inside the `areas_root_path` defined in `config.yaml`. The system will throw an error if the path is outside this boundary.
- **D-06:** The `create` mode initializes the standard history-building logic by parsing the raw PDF inside the given path, creating the `.source_files/` directory, and physically generating the split PDFs.

### `append` Mode Concurrency (The Listener)
- **D-07:** Implement a `.inbox.lock` lockfile mechanism in the inbox directory. If a second `append` listener tries to start, it will gracefully exit, ensuring only one listener runs at a time.
- **D-08:** In this phase, running `append` will simply take the lock and print a stub message (e.g. "Listener started..."). The actual listening loop is deferred.

### the agent's Discretion
- CLI framework: Use Python's standard `argparse` as specified in STACK.md for subparsers (`create`, `append`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture and Requirements
- `.planning/REQUIREMENTS.md` — Defines CONF-01, CONF-02, and CONF-03.
- `.planning/codebase/ARCHITECTURE.md` — Explains the existing functional pipeline which `create` mode wraps.
- `.planning/codebase/CONVENTIONS.md` — Highlights the current use of `.env` for secrets and Pydantic for validation.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/main.py`: Currently handles CLI execution; it will need to be refactored to support the explicit `argparse` subcommands.
- `src/core/schemas.py`: Existing Pydantic models are used for data validation; `config.yaml` parsing should follow this convention (e.g., using a Pydantic model for Settings).

### Established Patterns
- Separation of concerns: Configuration handling should reside in `src/core/` (e.g. `src/core/config.py`).
- Functional pipeline orchestration: `main.py` currently orchestrates the pipeline, and the `create` subcommand should neatly wrap this existing execution flow.

### Integration Points
- `src/main.py` needs an `argparse.ArgumentParser` with `add_subparsers()` to support `create` and `append`.

</code_context>

<specifics>
## Specific Ideas

- The user emphasized understanding the exact role of `create` mode: It requires just a PDF inside a house folder. It is the program itself that generates the `.source_files/` folder and splits the PDFs during the run.

</specifics>

<deferred>
## Deferred Ideas

- Inbox filename parsing and LLM inference syntax (Deferred to Phase 23).
- The actual File-System UI orchestrator loop (appending `_Proposed`, waiting for ` OK`, and finalizing) (Deferred to Phase 24).

</deferred>

---

*Phase: 22-configuration-and-cli-modes*
*Context gathered: 2026-07-20T11:38:00+03:00*
