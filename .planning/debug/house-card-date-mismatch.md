---
status: investigating
trigger: "i changed the document date of the starting documents in house 616 but the house card still shows from1990. the tenant selection ui is okay. why does the house card and the tenant selection ui use separate logic."
created: 2026-09-14T09:37:00Z
updated: 2026-09-14T09:37:00Z
---

## Symptoms
- **Expected Behavior**: Changing the document date of the starting documents for a house (e.g. house 616) should update the house card tenure duration / start date in the Area Grid. The house card and the tenant selection UI (House Profile / Tenancy Register) should use unified logic and stay in sync.
- **Actual Behavior**: The house card still shows "from1990" (or outdated start year), whereas the tenant selection UI shows the updated date.
- **Error Messages**: None.
- **Timeline**: Observed after changing document dates.
- **Reproduction**: Change the document date of the starting document for a tenant/house, return to Area Grid; house card still shows previous start year while tenant selection UI shows the new date.

## Current Focus
- **hypothesis**: The Area Grid house cards and the House Profile / Tenancy Register derive their tenure start date and duration from different sources or data paths (e.g. cached tree / static tree node vs live DB query / recalculation, or house card using static metadata while tenant selection UI recalculates `MIN(primary_date)`).
- **test**: Investigate where house card tenure / start dates are calculated in frontend and backend, compared to the tenant selection UI.
- **expecting**: Identify where the date logic diverges or where data is not refreshed / recomputed when document dates are changed.
- **next_action**: "gather initial evidence"

## Evidence
(none yet)

## Eliminated
(none yet)
