# Project Research Summary

## Key Findings

### Stack Additions
- **`pylnk3` (v0.4.2+):** Pure Python library for Windows `.lnk` shortcut creation/reading. Critical choice — it works on macOS dev environment unlike `pywin32`/`winshell` which require Windows.
- **`uuid` (stdlib):** `uuid4()` for generating immutable vault document IDs. No external dependency.
- **`pathlib` (stdlib):** For bidirectional filesystem scanning and Arabic-safe path manipulation.
- **Atomic writes:** `tempfile` + `os.fsync` + `os.replace` pattern for crash-safe `state.json` updates.

### Feature Table Stakes
| Feature | Table Stakes | Differentiators |
|---------|-------------|-----------------|
| Vault Storage | Immutable flat storage, UUID-based naming | Content-addressing for dedup, integrity verification |
| Windows Shortcuts | Valid `.lnk` files opening vault targets, correct path resolution | Multi-axis categorization (same doc in multiple folders) |
| Bidirectional Sync | Detect moved/deleted shortcuts, update state to match reality | Graceful offline handling, copy vs move detection |
| Timeline View | Chronological zero-padded numbering, auto-regeneration | Month/year sub-grouping for large collections |
| User Pinning | `user_locked: true` flag in state, AI skips locked docs | Pinned overrides as few-shot examples for future LLM runs |

### Architecture Impact
- **Untouched:** `src/categorization/`, `src/grouping/`, `report.json` generation
- **Modified:** `src/pipeline/runner.py`, `src/timeline/core.py`, `src/main.py`, `src/reconcile/core.py`
- **Replaced:** Multi-JSON checkpoints → unified `state.json`; `finalized.pdf` → `00_Timeline_View/`
- **New modules:** `src/vault/` (vault manager), `src/utils/shortcuts.py` (`.lnk` generator), `src/core/state.py` (unified state manager)

### Watch Out For
1. **Arabic + Windows paths:** Use `pathlib` consistently, normalize Unicode with `NFC`, prepend `\\?\` for long paths
2. **Vault orphans:** Two-phase commit (`.tmp` → rename) prevents orphaned files on crash
3. **Sync loops:** "User-wins" pinning strategy prevents infinite reconciliation loops
4. **`state.json` corruption:** Atomic write pattern (write to `.tmp`, `fsync`, `os.replace`) is mandatory
5. **Migration risk:** Must scan *current* folder structure and pin existing user organization, not reset to LLM defaults

## Implications for Roadmap

### Suggested Build Order (from Architecture Research)
1. **Unified State Foundation** — Refactor pipeline to use single `state.json` (highest risk, must stabilize first)
2. **Vault Core & Shortcut Utility** — Build `src/vault/` and `.lnk` generator with unit tests
3. **FileOrganizer Migration** — Modify generation pass to use vault + shortcuts, drop `finalized.pdf`
4. **Bidirectional Reconciliation** — Rewrite `reconcile/core.py` for bidirectional sync with user pinning
5. **Prepend Mode & Polish** — Rename append → prepend, adapt watcher package

### Key Dependency Chain
```
state.json (STATE) → Vault (VAULT) → Shortcuts (LNK) → Timeline View (TIMELINE)
                                                      → Reconciliation (RECON)
                                                      → Prepend Mode (PREPEND)
```

The unified state must be built first because every other feature reads from or writes to it. The vault must exist before shortcuts can point to it. Reconciliation and prepend mode are leaf nodes that depend on everything else.

## Sources
- Stack: `.planning/research/STACK.md`
- Features: `.planning/research/FEATURES.md`
- Architecture: `.planning/research/ARCHITECTURE.md`
- Pitfalls: `.planning/research/PITFALLS.md`
