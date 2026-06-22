# Phase 3: Graphical User Interface - Context

**Gathered:** 2026-06-22
**Status:** Ready for planning
**Source:** User explicitly requested fastest GUI

<domain>
## Phase Boundary

This phase delivers a Tkinter-based Graphical User Interface that wraps the existing CLI logic. It will allow users to select the input PDF, choose an output directory, and execute the file categorization process.
</domain>

<decisions>
## Implementation Decisions

### Technical Stack
- Build the GUI using Python's built-in `tkinter` to minimize external dependencies and development time.
- The GUI must invoke the existing `FileOrganizer` logic in `src/main.py`.

### UI Layout
- Add a "Browse" button and text field for selecting the input PDF.
- Add a "Browse" button and text field for selecting the output directory.
- Add a "Run" button to execute the pipeline.
- Include a scrolled text area to display progress logs.

### Execution
- Ensure the pipeline execution doesn't freeze the GUI. The processing should either be quick enough or run in a separate thread.
</decisions>

<canonical_refs>
## Canonical References
No external specs — requirements fully captured in decisions above
</canonical_refs>

<specifics>
## Specific Ideas
Use `tkinter.filedialog` for the Browse buttons.
</specifics>

<deferred>
## Deferred Ideas
None
</deferred>
