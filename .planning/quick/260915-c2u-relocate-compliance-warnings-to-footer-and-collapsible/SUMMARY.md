---
status: complete
quick_id: 260915-c2u
slug: relocate-compliance-warnings-to-footer-and-collapsible
date: 2026-09-15
description: Relocate House Card Missing-Docs Warning to Card Footer & Make House Profile Compliance Checklist Collapsible (Option A + Option 1)
commit: HEAD
---

# Quick Task Summary: Relocate House Card Missing-Docs Warning to Footer & Make House Profile Compliance Checklist Collapsible

**Task ID**: `260915-c2u`  
**Status**: Complete  
**Date**: 2026-09-15  

## Overview
Based on user feedback, the tenant file compliance indicators were refined across both the Area Grid (House Cards) and House Profile (Tenant Selection UI) to eliminate visual clutter and prevent crowding:
1. **House Cards (`area-grid.js`) — Option A**: Moved the missing documents warning out of the card body (where it previously touched and crowded the tenants list) into the card footer as a compact inline pill (`.missing-docs-strip`) adjacent to stay duration or total document count.
2. **House Profile / Tenant Selection UI (`house-profile.js`) — Option 1**: Replaced the permanent ~200px 5-column grid block with a sleek, one-line (~36px) collapsible accordion banner (`.tenant-compliance-card`). It displays the shield icon, active tenant name, compliance score (`X/5 ناقص ⚠️` or `مكتمل 5/5 ✓`), and a toggle button (`عرض التفاصيل ▾` / `إخفاء التفاصيل ▴`), smoothly revealing the 5 upload cards on demand and remembering preferences in `localStorage`.

---

## Accomplishments

### 1. Area Grid House Card Optimization (`area-grid.js`)
- Eliminated vertical bloat between tenant list and card footer.
- Relocated `.missing-docs-strip` into `card-footer` as an inline pill:
  - Displays `⚠️ ناقص: [list]` with tooltip and missing count badge.
  - Aligns cleanly alongside `Latest Stay` / `Total Archive` metrics.
- Preserved existing CSS classes and DOM test contracts so all existing test suites continue to pass without modifications.
- Synchronized static assets to `dist/win-x64/wwwroot/js/area-grid.js`.

### 2. House Profile Collapsible Compliance Header (`house-profile.js`)
- Replaced large fixed 5-card grid with a compact, progressive disclosure header:
  - Default view: ~36px height header banner showing compliance score and toggle.
  - Expanded view: Reveals all 5 mandatory document category cards with upload buttons and category navigation.
  - Interactive toggle on click with smooth chevron rotation and label change (`عرض التفاصيل` ↔ `إخفاء التفاصيل`).
  - Stores expansion state in `localStorage` under `tenant_compliance_expanded`.
- Ensures tenants are immediately visible upon entering any house profile with zero scrolling required.
- Synchronized static assets to `dist/win-x64/wwwroot/js/house-profile.js`.

---

## Verification
- **Vitest Frontend Test Suite**: All 36 test files passed, 435/435 tests passed (including `tenant_file_integrity.test.js`, `area_grid_card.test.js`, `house_profile.test.js`).
- **.NET Test Suite**: All 925 tests passed (0 failures).
- **Static Asset Parity**: 1:1 sync between `src/HousingApplication.Web/wwwroot/js/` and `dist/win-x64/wwwroot/js/`.
