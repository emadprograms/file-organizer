# Quick Task 260911-odx: Add House Grid Card with Dashed Outline and Huge Plus Symbol

**Task:** Remove top navbar Add House button and append an Add House card with dashed outline and huge plus symbol at the end of the house grid in Area Grid view
**Mode:** quick
**Date:** 2026-09-11

## Must Haves

1. **Remove Top Navbar Add House Button:**
   - Remove `#open-add-house-modal-btn` from `#top-navbar` in `index.html`.
   - Update `area-grid.js` and `router.js` to safely remove or null-guard any references to `open-add-house-modal-btn`.

2. **Dashed Add House Card in Area Grid:**
   - In `area-grid.js`, inside `renderAreaGrid(areaNode)`, render a dashed card `#add-house-grid-card` at the end of `houseCardsContainer`.
   - The card features:
     - Prominent dashed border (`border-2 border-dashed border-slate-300 hover:border-blue-500`)
     - Large plus symbol icon in the center (`w-12 h-12` container with `w-6 h-6` plus icon)
     - Arabic and English call to action: `+ إضافة منزل جديد` / `Add New House`
     - Descriptive hint: `انقر هنا لتسجيل منزل جديد في هذه المنطقة`
     - Accessible hover & active animations (`group-hover:scale-110`, `hover:bg-blue-50/40`, `cursor-pointer`)
   - Empty Area handling: When `houses.length === 0`, do NOT early-return before displaying the card. The dashed card should always be present and usable so users can add their first house.
   - Click action: Clicking `#add-house-grid-card` calls `openAddHouseModal(areaNode.name)`.

3. **Multi-Stack Parity:**
   - Synchronize all frontend changes across `web-net/wwwroot/`, `src/api/static/`, and `dist/win-x64/wwwroot/`.
   - Verify `diff -r src/api/static web-net/wwwroot` has 0 diff.

4. **Automated Testing:**
   - Update `tests/frontend/components/add_house.test.js` to test opening the modal via `#add-house-grid-card`.
   - Update `tests/frontend/components/unified_header.test.js` to verify top navbar no longer has `#open-add-house-modal-btn`.
   - Run Vitest suite (`npm run test:frontend`).
   - Run .NET test suite (`dotnet test web-net/FileOrganizer.Tests/FileOrganizer.Tests.csproj`).
   - Run Python test suite (`.venv/bin/pytest tests/test_v14_features.py`).
