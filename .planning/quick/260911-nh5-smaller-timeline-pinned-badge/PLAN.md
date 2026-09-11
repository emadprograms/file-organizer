# Quick Task Plan: Make Pinned Emoji and Text Smaller in Timeline View

**Task ID**: `260911-nh5` (QCK-21)  
**Description**: Reduce the size of the pinned lock emoji and "Pinned" text badge on documents in Timeline view  
**Date**: 2026-09-11  

---

## 1. Problem Statement
In the chronological Timeline view (`timeline-view.js`), documents that have been manually assigned (`is_manual: 1`) display a lock badge with the text "Pinned". Currently:
- The badge is styled with `text-[10px] font-semibold px-1.5 py-0.5 gap-1`.
- The emoji `🔒` is rendered at standard inline size (~12-14px bounding box), making it look disproportionately large.
- The "Pinned" text at 10px bold occupies significant horizontal space next to document titles, creating visual heaviness.
- The user requested making both the emoji and the text smaller.

## 2. Proposed Changes

### 1. `src/api/static/js/timeline-view.js`
- Update `lockBadgeHtml`:
  - Wrap the lock emoji in a dedicated span with `text-[8px] leading-none inline-block`.
  - Reduce badge font size to `text-[8.5px]` with `font-medium leading-none` and tighten gap to `gap-0.5`.
  - Add `.doc-pinned-badge` class for clear semantic styling and automated test targeting.

### 2. Cache Busting & Tri-Directory Asset Synchronization
- Bump asset cache version from `?v=260911-26` to `?v=260911-27` in `index.html` (scripts and stylesheet).
- Synchronize `timeline-view.js` and `index.html` to `web-net/wwwroot/` and `dist/win-x64/wwwroot/`.
- Verify `diff -ru src/api/static/ web-net/wwwroot/` and `diff -ru src/api/static/ dist/win-x64/wwwroot/` report 0 differences.

### 3. Automated Test Coverage
- Add unit test coverage in `tests/frontend/components/` verifying:
  - Documents with `is_manual: 1` render `.doc-pinned-badge` containing `text-[8.5px]` and child emoji span with `text-[8px]`.
  - Documents with `is_manual: 0` do not render the badge.
- Re-run all test suites (Vitest, .NET xUnit, Python Pytest, Playwright E2E).

### 4. Milestone Documentation & Audit Updates
- Update `STATE.md`, `PROJECT.md`, `ROADMAP.md`, `milestones/v14.0-ROADMAP.md`, `MILESTONES.md`, and `v14.0-MILESTONE-AUDIT.md` for QCK-21.
