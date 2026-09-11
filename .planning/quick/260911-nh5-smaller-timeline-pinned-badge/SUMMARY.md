---
status: complete
task_id: 260911-nh5
slug: smaller-timeline-pinned-badge
date: 2026-09-11
---

# Quick Task Summary: Make Pinned Emoji and Text Smaller in Timeline View

**Task ID**: `260911-nh5` (QCK-21)  
**Status**: Complete  
**Date**: 2026-09-11  

---

## 1. Overview
In the chronological Timeline view, manually assigned documents (`is_manual: 1`) display a lock badge with the label "Pinned". Previously, this badge was styled with `text-[10px] font-semibold` and an unscaled emoji `🔒`, resulting in an oversized badge that overwhelmed adjacent document titles.
Both the lock emoji and the text have now been scaled down:
- The lock emoji is wrapped in an inline span with `text-[8px] leading-none` to prevent emoji visual bloat.
- The badge container text sizing has been reduced to `text-[8.5px] font-medium leading-none` with tightened padding and spacing (`gap-0.5`).
- Added semantic class `.doc-pinned-badge` for clean targeting and testing.

## 2. Changes Made
1. **`src/api/static/js/timeline-view.js`**:
   - Updated `lockBadgeHtml` to use `.doc-pinned-badge text-[8.5px] font-medium gap-0.5` and `<span class="text-[8px] leading-none inline-block">🔒</span><span class="leading-none">Pinned</span>`.
2. **`src/api/static/index.html`**:
   - Bumped cache bust query parameter from `?v=260911-26` to `?v=260911-27` across all 17 scripts and stylesheets.
3. **Tri-Directory Asset Parity**:
   - Synchronized static assets to `web-net/wwwroot/` and `dist/win-x64/wwwroot/` with 0 diff.
4. **Automated Test Coverage**:
   - Created `tests/frontend/components/timeline_pinned_badge.test.js` (3 tests) validating pinned document styling, non-pinned exclusion, and mixed document lists.

## 3. Verification
- Vitest Frontend Suite: 164 passed across 17 files (+3 tests).
- ASP.NET Core xUnit Suite: 85 passed.
- Python Backend API (pytest): 33 passed.
- Static Asset Parity: `diff -ru` = 0.
