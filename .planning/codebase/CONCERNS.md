# Codebase Concerns & Technical Debt

This document outlines technical debt, architectural inconsistencies, security and data loss risks, performance bottlenecks, and dependency hygiene issues identified in the **file-organizer** codebase.

---

## 1. Executive Summary & Risk Matrix

| Risk / Concern Area | Category | Severity | Impact | Remediation Effort |
| :--- | :--- | :--- | :--- | :--- |
| **Timeline View Divergence (Create vs. Reconcile)** | Architecture | **HIGH** | Breaks Zero-Delta idempotency; running reconcile on a fresh house wipes and renames all timeline shortcuts | Low (Phase 68–70) |
| **Destructive `undo` Cleanup** | Data Safety | **HIGH** | `shutil.rmtree` and unbuffered unlinking in `src/pipeline/undo.py` can permanently destroy non-whitelisted user files | Low |
| **API Fan-Out & Rate Limiting (300+ calls / 100 pages)** | Performance | **HIGH** | 35+ minute runtimes per house due to 3 separate LLM passes per page with mandatory sleeps | Medium |
| **Single-Item PowerShell Shortcut Creation in Generator** | Performance | **HIGH** | `timeline/core.py` invokes PowerShell and compiles C# inline per shortcut rather than batching | Low |
| **Missing `pypdf` in `requirements.txt`** | Dependency | **HIGH** | Fresh virtual environments fail on `import pypdf` in `src/reconcile/core.py` | Trivial |
| **Dynamic Pydantic Schema Compilation on Every Page** | Performance | **MEDIUM** | `create_model` executed in loop iterations across 100s of pages | Low |
| **Windows PID-Based Lock Flaws** | Concurrency | **MEDIUM** | `os.kill(pid, 0)` in `watcher/lock.py` subject to Windows PID recycling | Low |
| **In-Place File Renaming in Watcher Inbox** | Architecture | **MEDIUM** | Polling loop modifying user files (`_Proposed`, `_Failed`) risks partial state corruption on abort | Medium |
| **Dead Dependency (`pylnk3`) & Orphan Code Stubs** | Tech Debt | **LOW** | `pylnk3` unused in favor of `IShellLinkW`; `tenant_config/tenants.py` is empty | Trivial |
| **Test Suite Latency (>5.5 mins) & Regressions** | Quality | **MEDIUM** | 2 failing unit tests in `test_pipeline_e2e.py` and `test_reconcile_phase49.py` | Low |

---

## 2. Architectural & Design Concerns

### 2.1 Timeline View Inconsistency Between `create` and `reconcile` Modes
- **Location**: `src/timeline/core.py` (lines 333–336) vs. `src/reconcile/core.py` (lines 743–777)
- **Problem**: 
  - In `create` mode (`src/timeline/core.py`), Timeline View shortcuts are generated with format:
    ```
    {doc_counter:03d} - {lnk_filename}
    ```
    Documents are sequenced chronologically by page order.
  - In `reconcile` mode (`src/reconcile/core.py`), shortcuts are formatted with metadata suffixes:
    ```
    {idx:03d} - {date_str} - {doc_title} [{location}]{extra}.lnk
    ```
    Documents are sorted in reverse date order (`sorted(groups, key=..., reverse=True)`).
- **Consequence**: Running `python src/main.py reconcile <target>` immediately on a freshly generated house flags all timeline shortcuts as orphaned, removes them, and regenerates them in reverse order with different names. This violates the system's core **Zero-Delta Idempotency** guarantee (tracked in Roadmap Phases 68–70).

### 2.2 Unbatched PowerShell Subprocess Calls in Generation Pass
- **Location**: `src/timeline/core.py` (lines 327–336) vs. `src/utils/fs.py` (`batch_create_shortcuts`)
- **Problem**: 
  - `src/utils/fs.py` provides `batch_create_shortcuts()`, which uses a single PowerShell invocation to compile `IShellLinkW` via C# `Add-Type` and generate all shortcuts.
  - However, `src/timeline/core.py` calls `create_shortcut()` twice per document inside a synchronous loop:
    ```python
    create_shortcut(abs_vault_target, str(lnk_path))
    create_shortcut(abs_vault_target, str(timeline_lnk_path))
    ```
- **Consequence**: For a 100-document house, 200 separate PowerShell subprocesses are launched, each initializing PowerShell, compiling inline C#, and writing to disk. This adds 30–60 seconds of purely synthetic startup overhead to generation.

### 2.3 Fragile In-Place Filename State Transitions in Watcher (`FSUIOrchestrator`)
- **Location**: `src/watcher/orchestrator.py` (lines 29–95)
- **Problem**:
  - The watcher coordinates user flow by polling the inbox every 2 seconds and renaming input PDFs directly (`file.pdf` $\rightarrow$ `file Proposed.pdf` $\rightarrow$ `file OK.pdf` $\rightarrow$ `file_Error_Invalid_Format.pdf`).
  - If the user or process terminates the listener while a file is in `Proposed` state, or if transient file-system locks prevent a rename, files become trapped in intermediate naming states.
  - Cache directories (`.tmp_*_master`) rely on `time.time() - mtime > 300` heuristics for cleanup.
- **Consequence**: High potential for orphaned files, dangling locks, and unhandled user rename collisions in multi-user or OneDrive/cloud-synced directories.

### 2.4 Empty Stub Modules and Legacy Code Artifacts
- **Location**: `src/tenant_config/tenants.py`, `src/llm/providers.py`
- **Problem**:
  - `src/tenant_config/tenants.py` is a 5-line empty stub containing only a logger and docstring.
  - `src/llm/providers.py` imports `openai` and contains docstrings/constants referencing OpenRouter and Groq providers, but the implementations were removed, leaving misleading imports and comments.
  - `src/core/config.py` defines `OPENROUTER_MODEL` and `GROQ_MODEL` environment variable lookups that are never referenced by active providers.
  - `src/reconcile/core.py` (lines 412–419) contains a duplicated dictionary update loop (`for p in old_per_page_filtered: p["page_index"] = idx_map.get(...)`).

---

## 3. Performance & Scalability Bottlenecks

### 3.1 Massive LLM Vision & Text Call Fan-Out
- **Location**: `src/categorization/categorization.py`, `src/categorization/fine_categorization.py`, `src/routing/router.py`
- **Problem**:
  - **Pass 1 (Categorization)**: Every single page triggers **2 separate Vision API calls**:
    1. Category Classification (`CategorySchema`)
    2. Field Extraction (`ExtractionSchema`)
  - **Pass 2 (Fine Categorization)**: Every single page triggers **1 text LLM call** (`FineCategorizationResponse`).
  - **Pass 3 (Routing & Double Check)**: Ambiguous documents trigger `double_check_others()`, which makes **2 additional LLM calls** (initial pick + confirmation).
- **Calculation for a 100-Page Document**:
  - Pass 1: 200 vision calls
  - Pass 2: 100 text calls
  - Grouping: 10–15 chunk calls
  - Routing: 20–40 calls
  - **Total**: ~350 LLM calls per document.
- **Latency**: At the default `delay_between_pages = 7.0s`, a single 100-page file requires **~2,450 seconds (~40 minutes)** of execution time, dominated by sleeps to respect Gemini free-tier RPM limits.

### 3.2 Heavy Synchronous OpenCV Image Pre-processing
- **Location**: `src/pdf/image_processing.py` (`extract_and_clean_page`)
- **Problem**:
  - For every page, `fitz` renders a 300 DPI pixmap to disk as raw PNG.
  - The raw PNG is read via `np.fromfile` and decoded with OpenCV.
  - OpenCV executes:
    1. Green-channel extraction
    2. Minimum bounding rectangle deskew (`cv2.minAreaRect`, `cv2.warpAffine`)
    3. $15\times 15$ kernel dilation + $21\times 21$ Gaussian blur for illumination background
    4. Floating-point division normalization (`np.where(bg > 0, 255.0 * (gray/bg), 255.0)`)
    5. Levels adjustment (`cv2.LUT`)
    6. Diacritic boosting (`cv2.morphologyEx` Black-Hat filter)
    7. Unsharp mask sharpening (second Gaussian blur + `cv2.addWeighted`)
    8. PNG encoding and disk write
- **Consequence**: CPU-intensive operations execute sequentially on the main thread for every page before any LLM calls start. For large scans (200+ pages), image extraction alone takes several minutes.

### 3.3 Dynamic Pydantic Model Recompilation in Tight Loop
- **Location**: `src/categorization/categorization.py` (lines 102–103, 138)
- **Problem**:
  ```python
  CategoryLiteral = Literal[tuple(categories.keys())]
  CategorySchema = create_model('CategorySchema', category=(CategoryLiteral, ...))
  ...
  ExtractionSchema = create_model('ExtractionSchema', **extracted_fields)
  ```
  `create_model()` is invoked on **every page loop iteration**, dynamically synthesizing Pydantic classes and recalculating field validators repeatedly rather than caching schema definitions once at module initialization.

### 3.4 Synchronous Disk I/O on Global API Tracking
- **Location**: `src/core/config.py` (`record_successful_call`)
- **Problem**:
  `record_successful_call()` executes an unbuffered synchronous file open and append (`with open(LOG_FILE, "a") as f: f.write(...)`) on every successful LLM call without concurrency locks, rotation, or size limits. Over thousands of pages, `.tracking/api_calls.log` grows unbounded.

---

## 4. Security, Concurrency & Data Safety Risks

### 4.1 Destructive Directory Wiping in `undo` Command
- **Location**: `src/pipeline/undo.py` (lines 78–103)
- **Problem**:
  - `run_undo()` reconstructs the original PDF and then executes a blind directory sweep:
    ```python
    for item in target_dir.iterdir():
        if item.resolve() == output_pdf_path.resolve():
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    ```
  - It only preserves files whose lowercase names contain `"raw_dump"`, `"tenant"`, or `"categorization"`.
- **Consequence**: Any user-created notes, extra PDF documents, subfolders, Excel trackers, or manual documentation stored in the house directory are permanently unlinked and deleted with no OS Recycle Bin or backup fallback.

### 4.2 PowerShell Script Subprocess Execution
- **Location**: `src/utils/fs.py` (`create_shortcut`, `batch_create_shortcuts`, `batch_read_shortcut_targets`)
- **Problem**:
  - Shortcut operations spawn `powershell.exe -NoProfile -ExecutionPolicy Bypass -File windows_shortcut.ps1`.
  - Temporary input JSON files are passed through `%TEMP%`.
  - While necessary due to Python limitations with Windows Unicode shortcuts, relying on shell-level script bypasses increases vulnerability to system execution policies, antivirus interception, or process elevation issues on locked-down corporate Windows environments.

### 4.3 Path Traversal String Prefix Checks
- **Location**: `src/timeline/core.py` (line 272)
- **Problem**:
  ```python
  if not str(target_dir).startswith(str(output_base_dir.resolve())):
      raise ValueError(f"Path traversal detected: {target_dir}")
  ```
  Using `str.startswith()` on file paths without ensuring a trailing path separator is a known security anti-pattern (e.g., `D:\Areas\House1` matches `D:\Areas\House10_Malicious`).
  - *Recommendation*: Use `target_dir.is_relative_to(output_base_dir)` (as done in `src/main.py`).

### 4.4 Unreliable PID Liveness Checking on Windows
- **Location**: `src/watcher/lock.py` (lines 24–30)
- **Problem**:
  - `acquire_lock()` uses `os.kill(pid, 0)` to test if a lock holder process is still alive.
  - On Windows, `os.kill(pid, 0)` invokes `OpenProcess()`. If the original process died and Windows assigned that same PID to an unrelated background system process (PID reuse/recycling), `acquire_lock` permanently believes the lock is held and refuses to start.
  - The project already has `filelock` in `requirements.txt`, which provides cross-platform OS-level file locking, but `src/watcher/lock.py` uses custom PID handling instead.

---

## 5. Dependency & Environment Hygiene

### 5.1 Missing Dependency in `requirements.txt` (`pypdf`)
- **Location**: `requirements.txt` vs `src/reconcile/core.py` (line 6) & `src/core/verification.py` (line 116)
- **Problem**:
  - `src/reconcile/core.py` has a top-level `import pypdf`.
  - `src/core/verification.py` imports `pypdf` to validate vault PDF headers.
  - However, `requirements.txt` does **not** list `pypdf`.
  - A clean installation in a new environment will immediately fail when running `reconcile` or `verify` with `ModuleNotFoundError: No module named 'pypdf'`.

### 5.2 Dead Dependency (`pylnk3`)
- **Location**: `requirements.txt` (line 15)
- **Problem**:
  - `pylnk3` was discarded in Phase 40 / Milestone v5.2 due to Arabic UTF-16 Mojibake bugs in Windows shortcut headers.
  - It was replaced by `IShellLinkW` via PowerShell interop, but remains in `requirements.txt` as dead weight.

### 5.3 Unused Dependency (`openai`)
- **Location**: `requirements.txt` (line 7), `src/llm/providers.py` (line 14)
- **Problem**:
  - `openai` is imported in `src/llm/providers.py` but is unused because all active calls route through `google-genai` (`GeminiProvider`).

### 5.4 Windows UTF-8 Terminal Encoding Warnings
- **Location**: `src/main.py` (lines 308–315)
- **Problem**:
  - On standard Windows CMD and PowerShell consoles, stdout defaults to `cp1252` or `cp1256`, causing UnicodeEncodeErrors when logging Arabic tenant names.
  - The CLI attempts `sys.stdout.reconfigure(encoding='utf-8')`, but users running without `PYTHONIOENCODING=utf8` may experience garbled terminal output.

---

## 6. Test Suite & Verification Gaps

### 6.1 Test Suite Regressions
Running the full pytest suite (349 tests) takes **~5 minutes 40 seconds** and produces **2 failures**:
1. `tests/test_pipeline_e2e.py::test_cli_prepend_1273_unknown`:
   - Mocking expectation mismatch during CLI prepend simulation.
2. `tests/test_reconcile_phase49.py::test_phase49_duplicate_shortcut_adopted_into_list`:
   - Reconcile verification failure triggered by corrupted dummy PDF mock streams (`invalid pdf header: b'dummy'`) and missing `500_report.json`.

### 6.2 Test Suite Execution Latency
- The test suite takes >5 minutes because numerous tests execute live PowerShell subprocesses (`powershell.exe`) and perform full image disk writes rather than using isolated in-memory unit mocks for filesystem shortcuts.

---

## 7. Actionable Recommendations & Remediation Plan

### Short-Term Fixes (Immediate)
1. **Fix `requirements.txt`**: Add `pypdf>=4.0.0` and remove `pylnk3` and unused `openai`.
2. **Harmonize Timeline View Sorting**: Align `src/reconcile/core.py` and `src/timeline/core.py` to use identical format and chronological sorting (Milestone v6.1).
3. **Batch Shortcut Creation in Generator**: Update `src/timeline/core.py` to collect all shortcuts into a single list and invoke `batch_create_shortcuts()`.
4. **Fix Path Traversal Check**: Replace `str.startswith()` with `.is_relative_to()` in `src/timeline/core.py`.
5. **Safeguard `undo`**: Move unpreserved files to `.trash/` instead of executing permanent `shutil.rmtree()` / `unlink()`.

### Medium-Term Refactoring
1. **Consolidate Pass 1 LLM Calls**: Combine classification and field extraction into a single unified JSON schema prompt per page (reducing vision calls by 50%).
2. **Precompile Pydantic Schemas**: Move `create_model` calls in `categorization.py` outside of the per-page loop.
3. **Adopt `filelock` in Watcher**: Replace custom `os.kill(pid, 0)` PID lock in `src/watcher/lock.py` with standard `filelock.FileLock`.
4. **Remove Dead Modules & Imports**: Delete `src/tenant_config/tenants.py`, clean unused `openai` and OpenRouter/Groq references from `src/llm/providers.py`.
