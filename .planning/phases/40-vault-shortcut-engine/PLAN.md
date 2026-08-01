# Phase 40: Vault & Shortcut Resolution Engine

## Objective
The verifier recursively parses `.lnk` files in categorized directories and `[Timeline View]`, validating their absolute targets against the vault.

## Scope
- Discard `pylnk3` due to its inability to handle Arabic Unicode paths correctly.
- Implement a custom C# interop script (`ps_shortcut.ps1`) natively leveraging the `IShellLinkW` API.
- Use `subprocess` in Python with UTF-8 encoding to securely invoke the C# script and read shortcut targets.
- Validate targets exist physically in `.source_files/vault/`.
- Handle edge cases with `os.path.samefile` or absolute string matching.

## Implementation Steps
1. Create `src/utils/ps_shortcut.ps1` to handle COM-free Unicode-safe shortcut creation and resolution.
2. Update `src/utils/fs.py` to bridge Python's `read_shortcut_target` to the PowerShell execution.
3. Update `src/core/verification.py` to use `read_shortcut_target` instead of `pylnk3.parse`.
4. Validate that the target file is inside the `vault/` directory.

## Status
- **Status:** COMPLETED
- **Completed On:** 2026-08-01
