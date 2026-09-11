---
status: complete
date: 2026-09-11
task_id: 260911-ny4
---

# Quick Task Summary: Arabic Tenant Count Badge in Tenancy Register Header

## Overview
Replaced the bare digit inside a circle in the Tenancy Register header (`سجل المستأجرين المتعاقبين`) with an Arabic tenant count badge (e.g. `3 مستأجرين` or `1 مستأجر`) styled as a rounded pill (`.tenants-count-badge`).

## Changes
- Updated `house-profile.js` across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/`.
- Added unit test in `tests/frontend/components/house_profile.test.js`.
