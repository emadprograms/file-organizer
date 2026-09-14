---
status: resolved
trigger: "the card considers everyone tenants. the house card. for house 540 it says there are 4 tenants. that is incorrect. 4 tenants. 1 applicant. the house card needs to be updated."
created: 2026-09-14T07:42:00Z
updated: 2026-09-14T07:45:00Z
---

## Symptoms
- **Expected Behavior**: The house card in the area grid should differentiate resident tenants from applicants. The header badge should show resident count and applicant count separately (e.g. "4 Tenants • 1 Applicant"), and applicants in the card overview list should have distinctive applicant styling rather than being labeled as "Past Tenant".
- **Actual Behavior**: The house card aggregated all children under `c.type === 'tenant'`, displaying "N Tenants" for everyone regardless of `is_resident`, and rendered applicants as "Past Tenant" with a past resident icon.
- **Error Messages**: None.
- **Timeline**: Present since applicant support was introduced in Milestone 16.
- **Reproduction**: View any house card in the Area Houses Grid (`area-grid.js`) for a house that has applicants registered.

## Root Cause
In `src/HousingApplication.Web/wwwroot/js/area-grid.js`, `renderAreaGrid` filtered `house.children` solely on `c.type === 'tenant'` into a single list `tenants`. The header badge displayed `${tenants.length} Tenants`, ignoring `is_resident`. In the tenant list mapping, any child that was not the active current tenant defaulted to "Past Tenant" styling with a past clock icon, causing applicants (`is_resident === 0`) to be counted as tenants and labeled as past residents.

## Fix
1. **Differentiate Residents vs Applicants**:
   In `src/HousingApplication.Web/wwwroot/js/area-grid.js`:
   ```javascript
   const allTenants = (house.children || []).filter(c => c.type === 'tenant');
   const residents = allTenants.filter(t => t.is_resident !== 0);
   const applicants = allTenants.filter(t => t.is_resident === 0);
   ```
2. **Dynamic Header Badge Format**:
   - Both residents & applicants: `${residents.length} ${residents.length === 1 ? 'Tenant' : 'Tenants'} • ${applicants.length} ${applicants.length === 1 ? 'Applicant' : 'Applicants'}`
   - Only residents: `${residents.length} ${residents.length === 1 ? 'Tenant' : 'Tenants'}`
   - Only applicants: `${applicants.length} ${applicants.length === 1 ? 'Applicant' : 'Applicants'}`
   - Zero: `0 Tenants`
3. **Distinct Applicant Card Styling**:
   For `t.is_resident === 0`:
   - `cardBg`: `'bg-purple-50/30 border-purple-200/60 dark:bg-purple-950/20 dark:border-purple-800/40'`
   - `nameClass`: `'font-medium text-purple-900 dark:text-purple-200'`
   - `tenantIcon`: Distinct purple applicant badge icon with `title="Applicant • متقدم"`
   - `tenureText`: `t.subtitle ? `${t.subtitle} • متقدم` : 'Applicant • متقدم'`
4. **Preserved Resident Styling**:
   For `t.is_resident !== 0`, preserved active resident (green/amber/rose by duration category) vs past tenant (slate) styling.
5. **Scroll & Interaction**:
   `scrollClass` and click propagation handlers evaluate on `allTenants.length > 3`.

## Verification
- Added comprehensive unit tests in `tests/web/components/area_grid_card.test.js`:
  - Verified 4 residents and 1 applicant produces `4 Tenants • 1 Applicant` in `.tenants-count`.
  - Verified applicant card item receives purple styling, purple icon with `title="Applicant • متقدم"`, and no "Past Tenant" label.
  - Verified singular/plural badge count variations (`1 Tenant • 1 Applicant`, `2 Applicants`, `1 Applicant`, `0 Tenants`).
- Ran full test suites:
  - `npm run test:web`: 30 test files, 339 passed (100%).
  - `~/.dotnet/dotnet test`: 164 passed, 0 failed (100%).
