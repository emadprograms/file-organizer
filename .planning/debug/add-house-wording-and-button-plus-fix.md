---
status: resolved
trigger: "the add new house has too many words and the the modal that opens when you click on create new house has, the button inside has too many + for some reason. fix these two."
created: 2026-09-11
updated: 2026-09-11
---

## Symptoms
- **Expected**:
  1. The "+ Add House" dashed card in the Area Grid overview should be sleek, clean, and concise, without verbose explanatory sentences or redundant plus symbols in the text.
  2. The submit button inside the Add House modal (`#btn-add-house-submit`) should have clean action text without repetitive `+` symbols or brackets.
- **Actual**:
  1. The dashed Add House card (`#add-house-grid-card`) contained verbose explanation text (`انقر هنا لتسجيل منزل جديد في هذه المنطقة`) in addition to dual titles with redundant `+` in the header.
  2. The submit button text (`#add-house-submit-text`) contained redundant `+` signs and bracket wrappers: `[ + إضافة المنزل ] / [ + Create House ]`.
- **Reproduction**:
  - Open Area Grid view (e.g. `#/area/Safra%20C`). Observe the dashed card at the end of the grid.
  - Click the card to open `#add-house-modal`. Look at the bottom-right blue submit button.

## Root Causes
1. In `area-grid.js`, `renderAreaGrid` included a 3rd line `<span class="text-[11px] text-slate-400 mt-2">انقر هنا لتسجيل منزل جديد في هذه المنطقة</span>` and an extra `+` inside the `<h3>` text despite having a large central plus SVG icon.
2. In `index.html`, `#add-house-submit-text` was written with legacy placeholder notation `[ + إضافة المنزل ] / [ + Create House ]`.

## Resolution
1. **Streamlined Add House Card**:
   - In `area-grid.js`, removed the verbose 8-word sentence `<span class="text-[11px] text-slate-400 mt-2">انقر هنا لتسجيل منزل جديد في هذه المنطقة</span>`.
   - Cleaned the header to `إضافة منزل جديد` (no redundant `+` in the title since the large plus icon circle is prominently displayed above).
   - Card now has concise dual titles: `إضافة منزل جديد` / `Add New House`.
2. **Clean Submit Button in Add House Modal**:
   - In `index.html`, updated `#add-house-submit-text` from `[ + إضافة المنزل ] / [ + Create House ]` to `إضافة المنزل / Create House`.
   - Stripped all brackets `[ ]` and redundant `+` symbols.
3. **Multi-Stack Parity & Testing**:
   - Synchronized static assets across `web-net/wwwroot/`, `src/api/static/`, and `dist/win-x64/wwwroot/` with 0 diff.
   - Updated `tests/frontend/components/add_house.test.js` and `tests/frontend/components/unified_header.test.js` (161 Vitest tests passing).
   - Verified 85/85 .NET xUnit tests and 18/18 Python pytest tests pass.
