# Quick Task Plan: Category Folder Circular Document Count Badge & Refined Document Date Sizing (QCK-10)

**Task ID**: `260911-category-doc-count-circle-and-smaller-doc-date`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-10)  
**Status**: Completed  
**Date**: 2026-09-11  

## Objective
1. In the Folders / Categories view (`categories-view.js`), replace the verbose text badge `"${cat.document_count} Documents"` on folder header cards with a sleek, circular count badge showing just the number inside a circle (e.g. `1`, `2`, `14`), with a descriptive `title` attribute for full accessibility.
2. Reduce the size of the document date badge (`doc-date-badge`) rendered on the right side of each document row in categories view so it no longer cramps or covers the document title, making it a little smaller while remaining crisp and legible.

## User Intent & Requirements
1. **Category Folder Document Count Badge**:
   - Instead of writing `1 Documents` / `2 Documents`, render just the count number inside a circle (`min-w-[20px] h-5 px-1 rounded-full bg-slate-100 text-slate-600 text-[10px] font-bold border border-slate-200 flex items-center justify-center flex-shrink-0 select-none`).
   - Include `title="${cat.document_count} ${cat.document_count === 1 ? 'Document' : 'Documents'}"` for tooltip and accessibility.
2. **Refined Document Date Badge Sizing**:
   - In `categories-view.js`, update `.doc-date-badge`:
     - Reduce font size from `text-[10px]` to `text-[9px]` with `tracking-tight`.
     - Maintain readable styling (`font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200/70 select-none`).
     - This gives ~12-15px more width to the document title container, avoiding unnecessary truncation.
3. **Asset Synchronization & Testing**:
   - Synchronize all static files to `web-net/wwwroot/` via `dotnet build`.
   - Update tests (Vitest, Playwright `test_tabs.py` if needed).
   - Ensure all test suites pass (Vitest, xUnit, Pytest).
