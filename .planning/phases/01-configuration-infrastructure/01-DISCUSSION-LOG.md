# Phase 1: Configuration Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-01
**Phase:** 1-Configuration Infrastructure
**Areas discussed:** Config File Discovery, Validation Strategy, Invalid Config Handling, Sample Config Distribution

---

## Config File Discovery

| Option | Description | Selected |
|--------|-------------|----------|
| Look for a default `config.yaml` in current directory, but allow a `--config` flag to override. | Standard and flexible CLI behavior. | ✓ |
| Require a `--config` flag explicitly; fail if not provided. | Strict behavior. | |
| Look for a default `config.yaml`; if not found, silently fall back to existing hardcoded behavior. | Implicit fallback, might cause confusion. | |

**User's choice:** Look for a default `config.yaml` in current directory, but allow a `--config` flag to override.
**Notes:** 

---

## Validation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Use strict Pydantic models (already in `src/schemas.py`) to validate the schema before any processing begins. | Leverages existing stack for robust validation. | ✓ |
| Perform basic dictionary/type checks for required fields without pulling in Pydantic for config. | Simpler but less robust. | |

**User's choice:** Use strict Pydantic models (already in `src/schemas.py`) to validate the schema before any processing begins.
**Notes:** 

---

## Invalid Config Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Fail immediately with a clear error message (Fail-fast). | Predictable and avoids partial/incorrect runs. | ✓ |
| Warn the user and silently fall back to the existing hardcoded tenant/real-estate behavior. | Implicit fallback, might cause confusion. | |

**User's choice:** Fail immediately with a clear error message (Fail-fast).
**Notes:** 

---

## Sample Config Distribution

| Option | Description | Selected |
|--------|-------------|----------|
| Keep it simple — just add a static `sample-config.yaml` file in the repository root. | Very simple and obvious to users looking at the repo. | ✓ |
| Add an `init` or `--generate-config` CLI command that dynamically writes the sample to their working directory. | Slightly more ergonomic but more complex to implement. | |

**User's choice:** Keep it simple — just add a static `sample-config.yaml` file in the repository root.
**Notes:** 

---

## the agent's Discretion

None

## Deferred Ideas

None
