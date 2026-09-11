---
status: complete
date: 2026-09-11
task_id: 260911-odx
---

# Quick Task Summary: Add House Grid Card with Dashed Outline and Huge Plus Symbol

## Overview
Replaced the top navbar Add House button with a modern dashed-outline "Add House" card (`#add-house-grid-card`) placed at the end of the houses list in Area Grid view (`area-grid.js`). The dashed card features a prominent plus symbol icon, dual Arabic and English call-to-action labels (`+ إضافة منزل جديد` / `Add New House`), and an explanatory prompt inviting users to click the empty house to register a new house in the selected area.

## Key Changes
1. **Removed Top Navbar Button:**
   - Completely removed `#open-add-house-modal-btn` from `#top-navbar` in `index.html`.
   - Cleaned up `area-grid.js` to eliminate redundant navbar button visibility toggles.
2. **Dashed Add House Grid Card:**
   - In `area-grid.js` (`renderAreaGrid`), dynamically creates and appends `#add-house-grid-card` to `houseCardsContainer` at the end of the house cards list.
   - Styled with `border-2 border-dashed border-slate-300 hover:border-blue-500`, smooth hover scaling (`group-hover:scale-110`), and a large central plus symbol inside a rounded container (`w-14 h-14`).
   - Includes localized titles: `+ إضافة منزل جديد`, `Add New House`, and helper text `انقر هنا لتسجيل منزل جديد في هذه المنطقة`.
   - Accessible via click and keyboard (`Enter` / `Space`).
   - Supports empty areas (`houses.length === 0`) seamlessly by presenting the dashed card directly without a dead-end message.
3. **Multi-Stack Parity & Testing:**
   - Maintained 100% static parity across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/` (zero diff).
   - Updated `tests/frontend/components/unified_header.test.js` to assert removal of the top navbar button.
   - Updated `tests/frontend/components/add_house.test.js` with tests for card presence, click opening, keyboard activation, and empty area behavior (160 Vitest tests passing).
   - Verified backend suites: 85/85 .NET xUnit tests passing, 18/18 Python pytest tests passing.
