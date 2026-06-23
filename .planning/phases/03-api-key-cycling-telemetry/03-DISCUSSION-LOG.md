# Phase 3: API Key Cycling & Telemetry - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-23
**Phase:** 3-API Key Cycling & Telemetry
**Areas discussed:** Key Storage & Loading, Cycling Trigger, Telemetry Output, Diagnostic Metrics

---

## Key Storage & Loading

| Option | Description | Selected |
|--------|-------------|----------|
| A separate `keys.txt` file (one key per line) | Separate text file for keys | |
| A comma-separated list in `.env` (`GEMINI_API_KEYS=key1,key2...`) | CSV in environment variables | ✓ |
| Let the user paste them into the Tkinter GUI (and save to settings) | Paste in Tkinter GUI | |
| Multiple variables in `.env` (`GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc.) | Numbered variables in .env | |

**User's choice:** A comma-separated list in `.env` (`GEMINI_API_KEYS=key1,key2...`)
**Notes:** Decided for ease of configuration within existing environment files.

---

## Cycling Trigger

| Option | Description | Selected |
|--------|-------------|----------|
| Track Requests-Per-Minute (RPM) per key and switch before hitting the limit | Count requests | |
| Track Tokens-Per-Minute (TPM) per key and switch before hitting the limit | Estimate tokens to prevent exhaustion | ✓ |
| Switch after every single request | Pure round-robin | |

**User's choice:** Track Tokens-Per-Minute (TPM) per key and switch before hitting the limit, as documents are large.
**Notes:** Better accounts for large context documents and avoids TPM starvation.

---

## Telemetry Output

| Option | Description | Selected |
|--------|-------------|----------|
| Write to a dedicated `telemetry.log` file | File output only | |
| Add a new "Diagnostics/Telemetry" tab or panel in the Tkinter GUI | GUI only | |
| Both a `telemetry.log` file and a summary in the Tkinter GUI | File + GUI Summary | ✓ |
| Just print to the console/terminal | Console only | |

**User's choice:** Both a `telemetry.log` file and a summary in the Tkinter GUI.
**Notes:** Provides a persistent log for debugging and an accessible dashboard for users.

---

## Diagnostic Metrics

| Option | Description | Selected |
|--------|-------------|----------|
| Track Token usage (TPM), Requests (RPM), request latency, and granular error details | Detailed tracing of capacities | ✓ |
| Track Token usage (TPM), Requests (RPM), error counts (429 vs 500), and key switch events | Standard metrics | |
| Track only errors and when a key switch occurs | Minimal tracking | |

**User's choice:** Track Token usage (TPM), Requests (RPM), request latency, and granular error details (token limit vs request limit).
**Notes:** Needed to clearly distinguish failure reasons as per HARD-03.

---
