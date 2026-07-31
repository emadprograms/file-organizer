# Stack Research: Vault Architecture & Bidirectional Reconciliation

## 1. Windows Shortcut (.lnk) Generation
**Recommended Library:** `pylnk3` (v0.4.2+)
- **Rationale:** `pylnk3` is a *pure Python* library for reading and writing Windows `.lnk` files. Even though the application targets Windows, using a pure Python package allows the codebase to run and be unit-tested on macOS without raising `ModuleNotFoundError` for Windows-specific binaries.
- **Integration Points:** Generating the `00_Timeline_View/` sequence and the categorized folder shortcuts pointing to the immutable vault PDFs.
- **Alternative (Not Recommended for this dev setup):** `pywin32` / `winshell`. These wrap Windows COM objects and strictly require a Windows environment to import, which would break the local macOS development workflow.

## 2. UUID-Based Vault Storage
**Standard Library:** `uuid` (specifically `uuid4()`)
- **Rationale:** Universally unique identifiers are perfect for generating immutable vault IDs. No external library required.
- **Integration Points:** When a PDF is finalized, it should be copied to `Vault/<uuid>.pdf`. All `.lnk` shortcuts point to this exact immutable path.

## 3. Unified state.json & Atomic Writes (Crash Safety)
**Standard Libraries:** `json`, `os`, `tempfile`
- **Rationale:** To prevent corrupted states during unexpected shutdowns, atomic write operations are mandatory.
- **Implementation Pattern:** Write-then-replace.
  1. Dump state to a temporary file (`state.json.tmp`) using `tempfile.NamedTemporaryFile(dir=..., delete=False)` in the *same directory* as the target file.
  2. Call `f.flush()` and `os.fsync(f.fileno())` to ensure the OS flushes data to physical disk.
  3. Use `os.replace(tmp_name, target_name)` which is guaranteed to be atomic on POSIX and generally safe/atomic on modern Windows.

## 4. Bidirectional Filesystem Sync
**Standard Libraries:** `pathlib` (`Path.rglob`), `os`
- **Rationale:** The system needs to detect if a user manually moved a `.lnk` file from one folder to another. By scanning the directory tree for `.lnk` files and reading their target paths via `pylnk3`, we can map current filesystem intent back to the vault UUID.
- **Integration Points:** A reconciliation function that compares the filesystem structure of shortcuts against the expected structure in `state.json`. Deviations are treated as "user overrides" and pinned in the state.

## 5. What NOT to Add
- **`watchdog` (Event-based Filesystem Watchers):** Do not add `watchdog` for bidirectional sync. Real-time event sync on user-manipulated folders leads to race conditions, partial moves, and complex debounce logic. State-comparison polling via `pathlib` is safer and deterministic.
- **`pywin32` / `win32com`:** Avoid these entirely. They will immediately break the macOS development environment. Stick to the pure Python `pylnk3`.
- **Database ORMs (SQLAlchemy, SQLite):** The milestone explicitly requests a unified `state.json` file. Introducing a relational database violates the architectural constraints.
