---
phase: 50
phase_name: "Cross-House Contamination Immunity"
project: "file-organizer"
generated: "2026-08-01"
counts:
  decisions: 1
  lessons: 1
  patterns: 1
  surprises: 1
missing_artifacts:
  - ".planning/STATE.md"
  - "50-UAT.md"
---

# Phase 50 Learnings: Cross-House Contamination Immunity

## Decisions

### Ignore External Shortcuts Completely
External shortcuts pointing outside the current house's `.source_files` directory are treated as foreign objects and filtered out.

**Rationale:** To prevent cross-house state contamination without adding complicated logic like UUID parsing or quarantining.
**Source:** 50-CONTEXT.md

---

## Lessons

### Simplicity over Complexity
We learned that complicated cross-house tracking is unnecessary when a simple root directory path check suffices.

**Context:** The user emphasized not caring if a file is from a different house, just whether it is an external shortcut.
**Source:** 50-CONTEXT.md

---

## Patterns

### Absolute Path Prefix Checking
Using the absolute path of the target directory to verify whether a resolved shortcut `.lnk` points inside the current workspace.

**When to use:** When gathering physical assets and ensuring they belong to the current processing domain.
**Source:** PLAN.md

---

## Surprises

### Fast Verification
Test suite was able to easily mock the foreign vault PDF and test this without side effects, reaching 100% success.

**Impact:** CI guarantees correctness without manual testing.
**Source:** 50-VERIFICATION.md
