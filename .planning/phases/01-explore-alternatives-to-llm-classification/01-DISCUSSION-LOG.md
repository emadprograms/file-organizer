# Phase 1: explore-alternatives-to-llm-classification - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-29
**Phase:** 01-explore-alternatives-to-llm-classification
**Areas discussed:** Scope of LayoutLM testing, OpenCV technique focus, Evaluation Metrics, Integration Path

---

## Scope of LayoutLM testing

| Option | Description | Selected |
|--------|-------------|----------|
| Zero-shot evaluation only | Focus on speed/feasibility without training overhead | |
| Fine-tuning on small sample | Requires building a dataset first, higher accuracy | |
| You decide | | |

**User's choice:** Start with zero-shot, fallback to fine-tuning if inaccurate.
**Notes:** User inquired about the fine-tuning process. We agreed to start lightweight and escalate effort only if the accuracy is subpar.

---

## OpenCV technique focus

| Option | Description | Selected |
|--------|-------------|----------|
| Structural elements | Detecting lines, boxes, and grids | |
| Text density & whitespace heuristics | Using PyMuPDF to analyze text distribution | |
| A hybrid of both | Combining structure and density | ✓ |
| You decide | | |

**User's choice:** Hybrid approach.
**Notes:** User explicitly stated that accuracy is the goal since a working baseline already exists.

---

## Evaluation Metrics

**User's choice:** Accuracy.
**Notes:** This was determined organically during the discussion of OpenCV hybrid vs single-method techniques. The user emphasized they already have a working program and want accurate results above all else.

---

## Integration Path

| Option | Description | Selected |
|--------|-------------|----------|
| Replace the LLM entirely | Full replacement if accurate enough | ✓ |
| Triage/Pre-filter | Handle obvious cases, fallback to LLM for edge cases | ✓ |
| You decide | | |

**User's choice:** Test both scenarios.
**Notes:** Since this is pure research to figure out what to implement, the user requested that we investigate and evaluate both a full replacement and a triage/fallback architecture. Additionally, they placed a strict constraint that all code changes remain within the `scratch` folder.

---

## the agent's Discretion

None

## Deferred Ideas

None
