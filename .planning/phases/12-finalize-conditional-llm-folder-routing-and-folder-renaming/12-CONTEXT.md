# Phase 12: Finalize Conditional LLM Folder Routing and Folder Renaming - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Finalize the Conditional LLM Folder Routing and Folder Renaming implementation. This phase focuses on final polish, ensuring the routing logic is production-ready, and verifying the consistency of the Arabic folder naming across the system. It is a "closure" phase for the routing feature set.

</domain>

<decisions>
## Implementation Decisions

### Edge Case Verification
- **D-01:** Focus exclusively on routing-step ambiguities (folder-to-folder) rather than categorization.
- **D-02:** Avoid over-specifying prompts to allow the LLM to remain creative and flexible in its routing decisions.

### Prompt Tuning
- **D-03:** Keep existing prompts as is; current precision is sufficient.

### Folder Mapping
- **D-04:** Keep the current minimal English-to-Arabic mapping bridge in `router.py` as it is isolated and does not introduce systemic complexity.

### Claude's Discretion
No specific areas deferred to Claude's discretion.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Routing Configuration
- `.planning/phases/11-conditional-llm-folder-routing-and-folder-renaming/11-CONTEXT.md` — Defines the routing constraints and requirements for the feature.
- `src/processing/routing/config.py` — The single source of truth for Arabic folder names and their meanings.
- `src/processing/routing/router.py` — The current implementation of the routing logic and double-check flow.

### Project Guidelines
- `.planning/PROJECT.md` — Project-level goals and constraints.
- `.planning/REQUIREMENTS.md` — Milestone v1.3 objectives.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `RoutingResponse` Pydantic model in `router.py` for schema-enforced LLM responses.
- `double_check_others` function in `router.py` for handling miscellaneous documents.

### Established Patterns
- Constrained routing (Forms vs Letters) using `FORM_FOLDERS` and `LETTER_FOLDERS`.
- Two-step verification for 'Others' category to reduce hallucinations.
- Direct routing bypass for specific high-confidence categories.

### Integration Points
- `src/processing/organizer/core.py` — Where the routing result is applied to move files.
- `src/logger.py` — Used for `log_decision_trace` to audit routing decisions.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly emphasized that the AI should not be constrained by overly specific prompts in the routing step to maintain its effectiveness.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 12-Finalize Conditional LLM Folder Routing and Folder Renaming*
*Context gathered: 2026-07-10*
