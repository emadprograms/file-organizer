# Phase 29.1: Fix Append-Mode Finalize Bugs

**Milestone:** v4.0 Architectural Cleanup
**Status:** Ready
**Priority:** URGENT — blocking production file-organization workflow

## Context

During production use of the append mode (dropping `502.pdf` from `D:\safra d additions` into the inbox), three critical bugs were discovered in the `finalize()` flow of `src/watcher/orchestrator.py` and `src/timeline/core.py`.

### Evidence

Full log from the failed 502 run:
`file:///C:/Users/Emad/.gemini/antigravity-cli/brain/ab6bd629-2456-42d6-9c34-bf9879d6148f/.system_generated/tasks/task-38.log`

## Bug 1: Duplicate House Directory Created (Cross-Drive Rename Failure)

**File:** `src/timeline/core.py` → `ensure_target_directories()` (line 146)
**Root Cause:** `Path.rename()` cannot move across drives (C: temp → D: areas). When this fails, the fallback on line 150 does `house_dir.mkdir()` which creates a **brand new empty directory** `502 - قأحمد الحبار الشيخ` instead of using the existing `502 - قاسم سعيد زين أحمد`.

**Log Evidence:**
```
WARNING - Could not rename C:\Users\Emad\AppData\Local\Temp to D:\Areas\Safra D\502 - قأحمد الحبار الشيخ: [WinError 17] The system cannot move the file to a different disk drive
```

**Result:** Two house directories exist side-by-side:
- `502 - قاسم سعيد زين أحمد` (original, with original _finalized.pdf)
- `502 - قأحمد الحبار الشيخ` (new empty one with broken tiny _finalized.pdf)

**Expected Behavior:** The `finalize()` flow should NEVER try to rename the house directory. It should always resolve and use the existing house directory that was found during the `propose()` step. The house directory name should only change via `reconcile --tenants`, not during append-mode finalization.

## Bug 2: Unnecessary `_raw_append.pdf` Intermediate File

**File:** `src/watcher/orchestrator.py` → `finalize()` (lines 407-431)
**Root Cause:** The finalize flow creates and permanently keeps a `_raw_append.pdf` in `.source_files/`, then rebuilds `_finalized.pdf` from it every single time by recompressing the entire accumulated PDF.

**Problems:**
1. Defeats the purpose of compression — you're keeping an uncompressed copy permanently
2. The original pages (from the initial `create` run) are NOT in `_raw_append.pdf` anyway, so the "protect originals" argument doesn't hold
3. Each finalization recompresses the ENTIRE file (all accumulated pages), not just the new ones — wasteful and causes quality degradation on re-compression

**Expected Behavior:**
- Compress each new incoming document's pages individually
- Append the compressed pages directly to the existing `_finalized.pdf`
- Do NOT maintain a separate `_raw_append.pdf`
- Rebuild the TOC incrementally (append new bookmarks, don't rebuild from scratch)

## Bug 3: House Directory Re-resolution After organize() Creates Wrong Target

**File:** `src/watcher/orchestrator.py` → `finalize()` (lines 561-567)
**Root Cause:** After `run_generation_pass()` calls `organize()`, the code re-resolves `house_dir` by scanning `area_dir` for directories starting with the house ID. But `organize()` may have created a NEW directory (Bug 1), so re-resolution picks up the wrong (new empty) directory. The `_raw_append.pdf` and `_finalized.pdf` then get written to the wrong location.

**Expected Behavior:** The `house_dir` should be resolved ONCE at the start of `finalize()` and never change. The finalize flow should not allow `organize()` to rename or create new house directories.

## Bug 4: Missing Test Coverage for Append-Mode Finalize Flow

**File:** `tests/`
**Root Cause:** None of these three bugs were caught by the existing test suite. This means the append-mode finalize flow either has no tests, or the tests don't exercise realistic conditions (cross-drive paths, existing house directories with different names, multi-document finalization).

**Required Tests:**
1. **Cross-drive rename guard:** Test that `ensure_target_directories()` works when `target_dir` and `house_dir` are on different drives (or mock this scenario). Verify no duplicate directories are created.
2. **Append to existing house directory:** Test that `finalize()` places documents into the EXISTING house directory, even when the house folder name doesn't match the current tenant name.
3. **No `_raw_append.pdf` created:** Test that after finalization, no `_raw_append.pdf` exists in `.source_files/`.
4. **`_finalized.pdf` grows correctly:** Test that after appending N documents, the `_finalized.pdf` contains the correct total page count (original + appended).
5. **Multi-document batch finalize:** Test OK-ing multiple proposed documents in sequence and verify they all land in the correct tenant subfolders without creating ghost directories.

## UAT Criteria

- [ ] Dropping a PDF into the inbox and OK-ing it appends pages to the EXISTING `_finalized.pdf` in the EXISTING house directory
- [ ] No `_raw_append.pdf` is created in `.source_files/`
- [ ] No duplicate house directories are created
- [ ] The house directory is NOT renamed during append-mode finalization
- [ ] TOC in `_finalized.pdf` includes bookmarks for both old and new documents
- [ ] Individual document PDFs are placed in the correct tenant subfolders
- [ ] File quality does not degrade — each page is compressed exactly once
- [ ] Tests exist for all three bugs (cross-drive rename, `_raw_append.pdf` removal, house directory re-resolution)
- [ ] Tests exercise realistic append-mode scenarios (existing house dir, multi-document batch, cross-drive paths)
- [ ] Works correctly when Areas are on D: drive and temp files are on C: drive

## Files to Modify

| File | Change |
|------|--------|
| `src/watcher/orchestrator.py` | Rewrite `finalize()` to append compressed pages directly to `_finalized.pdf`; remove `_raw_append.pdf` logic; pass fixed `house_dir` to generation pass |
| `src/timeline/core.py` | Fix `ensure_target_directories()` to handle cross-drive scenarios; prevent house directory rename during append mode |
| `src/pipeline/runner.py` | Verify `run_generation_pass()` respects a fixed output directory |
| `tests/test_finalize_append.py` | New test file covering all three bugs with realistic append-mode scenarios |

## Dependencies

None — this is a standalone bugfix phase.
