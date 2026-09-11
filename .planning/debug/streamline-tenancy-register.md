---
status: resolved
trigger: "سجل المستأجرين المتعاقبين 3 مستأجر ... this entire section here is too wordy. it should be intuitive. not wordy. fix this."
created: 2026-09-11
updated: 2026-09-11
---

## Symptoms
- **Expected**: The Tenancy Register cards in the House Profile overview (`renderHouseProfile`) should be sleek, intuitive, compact, and non-wordy. Icons and visual hierarchy should communicate status and navigation without repeating boilerplate terms or full-sentence navigation prompts.
- **Actual**:
  1. Header repeats "مستأجر" directly below the section heading: `3 مستأجر` next to `سجل المستأجرين المتعاقبين`.
  2. Uses generic chat emojis (`👤`, `⌛`) instead of clean Heroicons SVG icons.
  3. Status badges repeat the word "مستأجر": `🟢 المستأجر الحالي` and `⚪ مستأجر سابق`.
  4. Lease duration contains repetitive prefixes: `بدء الإيجار ` and `فترة الإيجار: `.
  5. Document and category counts are placed in a separate heavy footer row with border divider (`border-t`) and separate styled boxes (`📄 25 مستند`, `📁 10 مجلدات`).
  6. The footer repeats a full sentence link on every single card: `استعراض المجلدات ←` even though the card is already clickable.
- **Reproduction**: Navigate to any house in the house register (e.g. `#/area/Safra%20D/house/500`).

## Root Causes
- In `src/api/static/js/house-profile.js`, `renderHouseProfile` constructed the tenant register card with unnecessary textual redundancy and multi-row layout instead of a unified, compact modern list item layout with clean SVGs, dot badges, and subtle drilldown chevrons.

## Resolution
1. **Header Count Badge**:
   - Replaced `${profile.tenants.length} مستأجر` with a simple circular count pill `${profile.tenants.length}` matching the app-wide count badge pattern.
2. **SVG Iconography**:
   - Replaced emojis `👤` and `⌛` with clean Heroicons user and clock SVGs in soft tinted avatar boxes.
3. **Streamlined Status Badge**:
   - Replaced wordy `🟢 المستأجر الحالي` and `⚪ مستأجر سابق` with sleek dot badges: `● حالي` (emerald) and `● سابق` (slate), with descriptive `title` attributes for tooltips/accessibility.
4. **Clean Dates**:
   - Stripped redundant `بدء الإيجار ` and `فترة الإيجار: ` prefixes, presenting clean duration strings like `2020 (مستمر منذ 7 سنوات)` or `2000 – 2002 (سنتان)`.
5. **Inline Counts & Navigation Indicator**:
   - Removed the bulky `border-t` footer and repetitive text `استعراض المجلدات ←`.
   - Incorporated document and category counts directly into a single compact secondary line using subtle Heroicon SVGs.
   - Added a subtle drilldown chevron arrow (`←` in RTL) on the edge of the card that nudges on hover.
6. **Dual-Backend Parity**:
   - Synchronized `src/api/static/js/house-profile.js` to `web-net/wwwroot/js/house-profile.js` (`diff -r` returns 0).
7. **Test Updates & Verification**:
   - Added unit test in `tests/frontend/components/house_profile.test.js` verifying the streamlined layout, lack of boilerplate strings, and presence of clean badges/counts.
   - Updated Playwright assertions in `tests/frontend/test_house_register.py`.
   - Verified 144 Vitest tests, 84 .NET xUnit tests, and Playwright suites pass.
