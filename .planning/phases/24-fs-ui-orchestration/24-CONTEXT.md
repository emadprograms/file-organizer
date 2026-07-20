# Phase 24: FS-UI Orchestration - Context

**Gathered:** 2026-07-20T20:38:14+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

The File-System UI listener loop. This phase wires up the `append` mode to watch the Inbox, renames files to propose actions (e.g. appending `_Proposed`), waits for user approval (appending ` OK`), and triggers the finalization pipeline to move the file to `.source_files/` and update the target history.
</domain>

<decisions>
## Implementation Decisions

### Watcher Strategy
- **D-01:** Implement a simple polling loop (1-2s interval) running in the foreground blocking the terminal (until Ctrl+C).
- **D-02:** Wait until a file's size is stable between polls before processing to handle files that are actively being copied/written.
- **D-03:** Auto-create the `inbox_path` using `os.makedirs` if it doesn't exist when the listener starts.
- **D-04:** Check if the process ID (PID) inside `.inbox.lock` is still alive. If not, auto-recover and overwrite the stale lock.
- **D-05:** Do not print periodic heartbeats (e.g., "Listening...") to avoid console spam. Print only once at startup and subsequently only on actual events (e.g., file found, moved, or error).

### Rejection Handling
- **D-06:** No explicit reject keyword is needed. If the user disagrees with the proposal, they manually edit the filename. The system will treat any file that lacks both `_Proposed` and ` OK` suffixes as a fresh file and restart the loop.
- **D-07:** If the parser/LLM fails to infer missing data, append `_Failed` or `_Error` to the filename to signal the user for manual intervention and to prevent infinite inference loops.

### State Persistence
- **D-08:** The listener must be completely stateless. It relies entirely on the filename (`_Proposed`, `_Failed`, ` OK`) for state. It must not use internal memory (dictionaries/sets) to track processed files.
- **D-09:** On restart, if the listener finds files already marked `_Proposed`, it leaves them alone and waits for user action (approval or edit).
- **D-10:** On restart, if the listener finds files marked ` OK`, it immediately processes and finalizes them.

### Finalization Feedback
- **D-11:** Finalized files disappear silently from the Inbox. No trace or log file is left behind in the Inbox.
- **D-12:** If the OS move fails (e.g., disk full, permissions issue), abort the move but keep the ` OK` filename. Print a user-friendly error to the console (and log the full trace to a file). This allows the system to retry automatically once the issue is resolved without wasting LLM calls.
- **D-13:** If a file with the exact same name already exists in the destination folder, append a timestamp or counter to the filename to avoid overwriting.

### the agent's Discretion
None — all options were explicitly chosen.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture and Requirements
- `.planning/REQUIREMENTS.md` — Defines FSUI-04, FSUI-05, and FSUI-06 requirements.
- `.planning/codebase/ARCHITECTURE.md` — Explains the existing functional pipeline and how finalization routes the documents.
- `.planning/codebase/CONVENTIONS.md` — Outlines standard error handling, logging, and architectural separation of concerns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/main.py`: The `append` subcommand handler (created in Phase 22) will be expanded to invoke the new watcher logic.
- `src/llm/client.py`: Used for LLM inference syntax parsing (from Phase 23).
- `src/core/schemas.py`: Used for data validation when mapping filenames to house structures.

### Established Patterns
- **Class-based orchestration:** Requirement FSUI-06 dictates that the listener should be encapsulated in a class to separate state from the functional pipeline.
- **Graceful Error Handling:** Console outputs should be user-friendly, with full stack traces redirected to log files.

### Integration Points
- `src/main.py`: The `append` subparser needs to invoke the new File-System UI listener class.
- `src/processing/pipeline.py`: Needs to be called or triggered when a file is marked ` OK` to actually run the pipeline over the document.

</code_context>

<specifics>
## Specific Ideas

- The user emphasized that there is no explicit rejection option; manual editing of the filename is the standard flow, treating the edited file as fresh.
- Keeping the ` OK` suffix on a system move error is critical so that the orchestrator can automatically retry the move when the user fixes the system issue without re-running LLM inference.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 24-FS-UI Orchestration*
*Context gathered: 2026-07-20T20:38:14+03:00*
