# Phase 08: "True Until Proven Guilty" Grouping Logic - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-08
**Phase:** 08-True Until Proven Guilty Grouping Logic
**Areas discussed:** Topic Shift Threshold, Implicit Continuation Cues, Prompt Management, Verification Strategy

---

## Topic Shift Threshold & Implicit Continuation Cues

| Option | Description | Selected |
|--------|-------------|----------|
| Content-Based Reasoning | LLM reads content_explanation to find boundaries | |
| Subject-Based Matching | LLM compares `subject` fields for central theme continuity | ✓ |

**User's choice:** Subject-Based Matching for letters.
**Notes:** User highlighted that letters are often correspondence chains (stories). Tables often trigger false splits. The central theme is the key. Use the `subject` field from JSON to reduce cognitive load on the LLM.

---

## Prompt Management

| Option | Description | Selected |
|--------|-------------|----------|
| Hard-coded in core.py | Keep prompts as constants in the logic file | |
| Config-based | Move prompts to a separate config file for easier tuning | ✓ |

**User's choice:** Config-based.
**Notes:** Agreed to move prompts to a config file to allow iteration without changing code.

---

## Verification Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Regression Testing | Ensure old cases still work | |
| Targeted Continuity Tests | New golden cases for subject-theme continuity and hard-coded rules | ✓ |

**User's choice:** Targeted Continuity Tests.
**Notes:** Focus on verifying "central theme" grouping for letters and the non-LLM rules for Contracts/IDs/Bills.

---

## Claude's Discretion

- **The "Others" Category**: Implementation of "chunks of 2" for categories that don't have hard rules.

## Deferred Ideas

None.
