# Phase 12: Finalize Conditional LLM Folder Routing and Folder Renaming - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-10
**Phase:** 12-finalize-conditional-llm-folder-routing-and-folder-renaming
**Areas discussed:** Edge Case Verification, Prompt Tuning, Consistency Audit / Mapping Analysis

---

## Edge Case Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Edge Case Verification | Verify specific edge cases for routing. | ✓ |
| Prompt Tuning | Fine-tune prompts for precision. | |
| Consistency Audit | Audit folder references for Arabic name consistency. | |

**User's choice:** Focus exclusively on routing-step ambiguities. User corrected the approach to focus on folder-to-folder routing rather than pre-routing categorization.
**Notes:** User explicitly warned against over-specifying prompts as it can confuse the AI.

---

## Prompt Tuning

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as is | Current precision is sufficient. | ✓ |
| Add guidelines | Add detailed differentiation guidelines to the prompts. | |

**User's choice:** Keep as is.
**Notes:** User prefers to keep prompts small and let the AI decide.

---

## Consistency Audit / Mapping Analysis

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as bridge | Helpful abstraction; keep it. | ✓ |
| Unify to Arabic | Confusing; unify everything to Arabic. | |
| Analyze friction first | Analyze current friction before deciding. | |

**User's choice:** Keep it as is.
**Notes:** After analysis, the user decided the minimal English-to-Arabic mapping in `router.py` is acceptable and does not create significant friction.

---

## Claude's Discretion

None.

## Deferred Ideas

None.
