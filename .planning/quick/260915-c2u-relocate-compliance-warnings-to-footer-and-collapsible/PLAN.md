---
status: complete
quick_id: 260915-c2u
slug: relocate-compliance-warnings-to-footer-and-collapsible
date: 2026-09-15
description: Relocate House Card Missing-Docs Warning to Card Footer & Make House Profile Compliance Checklist Collapsible (Option A + Option 1)
---

# Plan: Relocate House Card Missing-Docs Warning to Card Footer & Make House Profile Compliance Checklist Collapsible

## User Intent
1. In the House Card (`area-grid.js`), the missing documents warning was placed in the body right below the tenants list, crowding the tenants and expanding card height irregularly.
2. In the Tenant Selection UI / House Profile (`house-profile.js`), the compliance check was a massive 5-box card at the very top, hogging vertical space and distracting from viewing the actual tenants.
3. User selected **Option A** (Embed missing docs warning into card footer) and **Option 1** (Collapsible slim banner in House Profile with toggle).

## Key Changes
1. `area-grid.js`:
   - Remove `missingDocsStripHtml` from between the tenant list and the footer.
   - Embed `missingFooterPillHtml` with class `.missing-docs-strip` into `footerHtml` next to stay/archive badges.
   - Dedicate 100% of the card body to clean tenant history and stay duration.
2. `house-profile.js`:
   - Replace the large fixed 5-box compliance card with a sleek ~36px collapsible accordion header.
   - Show status badge, shield icon, tenant name, and `عرض التفاصيل ▾` toggle.
   - Expand 5-category upload cards on demand, persisting state in `localStorage`.
3. Verification:
   - Verify all 435 Vitest tests and 925 .NET xUnit tests pass with zero regressions.
