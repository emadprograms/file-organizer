# Phase 1: explore-alternatives-to-llm-classification - Context

**Gathered:** 2026-06-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement and evaluate the `qwen3-vl` 4b model as a local alternative to the current LLM API classification method on the `scratch/classify_559.py` script.
This phase delivers a proof-of-concept implementation and evaluation of the `qwen3-vl` 4b model for vision-based document classification.

</domain>

<decisions>
## Implementation Decisions

### Approach
- **D-01:** Discard previous local options (LayoutLM, OpenCV heuristics, rule-based) as they proved ineffective.
- **D-02:** Implement a new approach using the **qwen3-vl 4b model**.

### Scope
- **D-03:** Restrict all implementation and testing strictly to the `scratch/` folder. Do not touch core application folders.

### Evaluation Metrics
- **D-04:** Accuracy remains the primary optimization goal.

### Integration Path
- **D-05:** Evaluate the `qwen3-vl 4b` model as a full local replacement for the current LLM API classification.

### the agent's Discretion
None

### Folded Todos
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core Scripts
- `scratch/classify_559.py` — The script we are using as a baseline for comparing classification methods.

### Strategy / Project Context
- `.planning/ROADMAP.md` — Defines phase goals and success criteria.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/schemas.py`: Ensure any classification script output aligns with `PageClassification` schema or maps easily to it.

### Established Patterns
- The current implementation heavily relies on cloud LLMs (Gemini -> OpenRouter -> Groq cascade). This research explores viable offline/lighter alternatives.

### Integration Points
- `src/pipeline.py`: The `Pass 1` vision extraction where documents are classified. While no code modifications will happen here during Phase 1 (restricted to `scratch/`), understanding this integration point is vital.

</code_context>

<specifics>
## Specific Ideas

- "I already have a program that works. I want it to be accurate." — The user places a high premium on matching or exceeding the current implementation's accuracy.
- "restricted only to the scratch folder. that is it. no other folder should be touched." — Strict boundary for Phase 1 code.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-explore-alternatives-to-llm-classification*
*Context gathered: 2026-06-29*
