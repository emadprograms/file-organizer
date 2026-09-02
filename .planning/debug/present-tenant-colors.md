---
status: resolved
trigger: "the red green and yellow color scheme is actually only for tenant currently living there. the rest of the tenants who have left the house get the generic grey color."
updated: 2026-09-02
---

# Debug Session: present-tenant-colors

## Root Cause

The `duration_category` was computed for **all** tenants in `get_tree()` — both past and present. The logic calculated a `duration` span from `min_val` to `current_year` (if present) or `max_val` (if past), then assigned a color tier to everyone.

This caused even past tenants who had left years ago to receive a red, yellow, or green badge.

## Fix

In `src/api/routes.py`, gated the `duration_category` computation inside `if tenant_is_present.get(t):`. Past tenants now fall through with `duration_category = None`, which maps to the grey badge style in `index.html`.

## Verification

All 9 API tests pass. `uvicorn` auto-reloaded and the change is live in the browser on refresh.

## Files Changed

- `src/api/routes.py` — conditional duration_category assignment
