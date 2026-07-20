# Phase 24: FS-UI Orchestration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-20T20:38:14+03:00
**Phase:** 24-FS-UI Orchestration
**Areas discussed:** Watcher strategy, Rejection handling, State persistence, Finalization feedback

---

## Watcher strategy

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Simple polling loop (`time.sleep(1)`) - Simplest, no extra dependencies. | ✓ |
| 2 | OS-level events (`watchdog` library) - More efficient but requires dependency. | |
| 3 | You decide | |

**User's choice:** Simple polling loop

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Every 1-2 seconds (Fast feedback, low overhead) | ✓ |
| 2 | Every 5-10 seconds (Lower overhead, slightly delayed UI feedback) | |
| 3 | You decide | |

**User's choice:** (Recommended) Every 1-2 seconds (Fast feedback, low overhead)

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Wait until file size is stable between polls before processing. | ✓ |
| 2 | Try to open exclusively, wait if locked. | |
| 3 | You decide | |

**User's choice:** (Recommended) Wait until file size is stable between polls before processing.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Yes, run in the foreground blocking the terminal (until Ctrl+C). | ✓ |
| 2 | Run in background as a daemon. | |
| 3 | You decide | |

**User's choice:** Foreground
**Notes:** User requested explanation of foreground vs daemon. After explanation, selected foreground.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Check if the process ID (PID) inside the lockfile is still alive. If not, auto-recover and overwrite the lock. | ✓ |
| 2 | Fail and require the user to manually delete the lockfile. | |
| 3 | You decide | |

**User's choice:** (Recommended) Check if the process ID (PID) inside the lockfile is still alive. If not, auto-recover and overwrite the lock.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Keep it simple and constant (1-2s). | ✓ |
| 2 | Adaptive (e.g. slow down to 5s if empty for >10 mins, speed up on new files). | |
| 3 | You decide | |

**User's choice:** (Recommended) Keep it simple and constant (1-2s).

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) No, just print once at startup and then only on events (file found, moved) to avoid console spam. | ✓ |
| 2 | Yes, every minute so the user knows it's alive. | |
| 3 | You decide | |

**User's choice:** (Recommended) No, just print once at startup and then only on events (file found, moved) to avoid console spam.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Create it automatically using `os.makedirs`. | ✓ |
| 2 | Exit with an error telling the user to create it. | |
| 3 | You decide | |

**User's choice:** (Recommended) Create it automatically using `os.makedirs`.

---

## Rejection handling

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Move the file to a `Failed` or `Rejected` folder and strip the `_Proposed` text. | |
| 2 | Revert the filename to its original state and ignore it going forward. | |
| 3 | You decide | |

**User's choice:** "the user will have no reject option. if he doesnt like the proposed option. he will hvhave have to manually edit the filename again. and again the loop will start as if it jis is a fresh file."

**User's choice:** Confirmed that any file lacking `_Proposed` and ` OK` is treated as a fresh file.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Append `_Failed` or `_Error` to the filename so the user knows it needs manual intervention (prevents infinite loops). | ✓ |
| 2 | Leave the filename as is and just print an error to the console (could cause infinite loop). | |
| 3 | You decide | |

**User's choice:** (Recommended) Append `_Failed` or `_Error` to the filename so the user knows it needs manual intervention (prevents infinite loops).

---

## State persistence

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Just leave them as `_Proposed` and wait for the user to append ` OK` or edit them. | ✓ |
| 2 | Re-run the parsing/inference and re-propose them just in case. | |
| 3 | You decide | |

**User's choice:** (Recommended) Just leave them as `_Proposed` and wait for the user to append ` OK` or edit them.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) No, it should be completely stateless. The filename itself (e.g. `_Proposed`, `_Failed`, ` OK`) is the only state. | ✓ |
| 2 | Yes, keep a set of "seen" files in memory to avoid redundant processing checks. | |
| 3 | You decide | |

**User's choice:** (Recommended) No, it should be completely stateless. The filename itself (e.g. `_Proposed`, `_Failed`, ` OK`) is the only state.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Finalize them immediately as if they were just approved. | ✓ |
| 2 | Ignore them, assuming they were already processed. | |
| 3 | You decide | |

**User's choice:** (Recommended) Finalize them immediately as if they were just approved.

---

## Finalization feedback

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) No, it disappears silently. The absence of the file means it's been filed. | ✓ |
| 2 | Yes, leave a 0-byte `.txt` file or log in the Inbox so the user knows where it went. | |
| 3 | You decide | |

**User's choice:** (Recommended) No, it disappears silently. The absence of the file means it's been filed.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Abort the move, keep the ` OK` filename, and print an error to the console. | ✓ |
| 2 | Strip the ` OK` and append `_Failed` so the user knows an error occurred. | |
| 3 | You decide | |

**User's choice:** (Recommended) Abort the move, keep the ` OK` filename, and print an error to the console.
**Notes:** User questioned why keep ` OK`. Explained that this avoids re-running inference on transient OS errors (e.g. disk full), letting it retry successfully once the issue is fixed. User agreed.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) User-friendly error with the cause (e.g. "Disk full"), but log the full trace to a file. | ✓ |
| 2 | Print the full Python stack trace to the console. | |
| 3 | You decide | |

**User's choice:** (Recommended) User-friendly error with the cause (e.g. "Disk full"), but log the full trace to a file.

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | (Recommended) Append a timestamp or counter to the filename to avoid overwriting the existing file. | ✓ |
| 2 | Overwrite the existing file. | |
| 3 | Abort the move, strip ` OK`, and append `_Failed`. | |
| 4 | You decide | |

**User's choice:** (Recommended) Append a timestamp or counter to the filename to avoid overwriting the existing file.

---

## the agent's Discretion

None

## Deferred Ideas

None
