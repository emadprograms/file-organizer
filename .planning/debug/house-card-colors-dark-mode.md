---
status: resolved
trigger: "I cannot see the house card colors in dark mode. the yellow, green, red borders that would tell the tenant duration"
created: 2026-09-14T13:46:00Z
updated: 2026-09-14T13:52:00Z
---

## Current Focus
- hypothesis: "In src/HousingApplication.Web/wwwroot/css/styles.css, the CSS rule 'html.dark .house-card { border-color: #1e293b; }' and 'html.dark .house-card:hover { border-color: #3b82f6; }' had a higher CSS specificity (0, 2, 0) than Tailwind's utility classes (border-l-emerald-500, border-l-amber-500, border-l-rose-500, border-l-slate-300 with specificity 0, 1, 0). The shorthand 'border-color' property set all four sides (top, right, bottom, left), which completely overwrote border-left-color with dark slate (#1e293b) or blue (#3b82f6), obliterating the duration indicator border colors (green for <5y, amber for 5-10y, red for >10y, slate for vacant)."
- test: "Replaced shorthand 'border-color: #1e293b;' on html.dark .house-card and 'border-color: #3b82f6;' on html.dark .house-card:hover with individual border side properties (border-top-color, border-right-color, border-bottom-color). Added explicit dark mode rules for .house-card.border-l-emerald-500 (#10b981), .border-l-amber-500 (#f59e0b), .border-l-rose-500 (#f43f5e), .border-l-slate-300 / .dark:border-l-slate-600 (#475569) both statically and on hover with !important. Also harmonized .border-rose-200/80 for tenant items."
- expecting: "In dark mode, house cards have clear, vivid left indicator borders matching the tenure legend (<5y emerald, 5-10y amber, >10y rose, vacant slate), and hover preserves the duration indicator left border while illuminating top/right/bottom borders with blue (#3b82f6)."
- next_action: "Complete. All Vitest and .NET tests passing; byte parity confirmed."

## Symptoms
- **Expected behavior**: In dark mode, house cards in the Area Grid should display vivid left borders indicating tenant duration (green/emerald for <5 years, yellow/amber for 5-10 years, red/rose for >10 years, slate for vacant), matching the legend at the top of the area view.
- **Actual behavior**: The user could not see the house card colors in dark mode. The yellow, green, and red borders that indicate tenant duration were invisible.
- **Error messages**: None (CSS styling conflict / specificity override).
- **Timeline**: Present in dark mode styling rules in styles.css.
- **Reproduction**: Switch to dark mode (add class 'dark' to html), navigate to an area grid (e.g. `#/area/Safra%20C`), and observe that the house cards do not show green, yellow, or red left borders.

## Root Cause
In `src/HousingApplication.Web/wwwroot/css/styles.css`:
1. `html.dark .house-card` set `border-color: #1e293b;` (CSS specificity 0, 2, 0).
2. `html.dark .house-card:hover` set `border-color: #3b82f6;` (CSS specificity 0, 3, 0).
3. The CSS shorthand property `border-color` sets all four sides (`border-top-color`, `border-right-color`, `border-bottom-color`, and `border-left-color`).
4. Tailwind's duration indicator utility classes on house cards (`border-l-emerald-500`, `border-l-amber-500`, `border-l-rose-500`, `border-l-slate-300`) have specificity (0, 1, 0).
5. Because the dark mode `.house-card` rules had higher specificity and used the 4-side shorthand `border-color`, they completely overwrote the left indicator border with dark slate `#1e293b` at rest and `#3b82f6` on hover, making tenure indicator borders invisible in dark mode.
6. Additionally, `html.dark .border-rose-200\/80` was missing from the dark mode palette for long tenure tenant rows within house cards.

## Fix
1. **Preserved Single-Side Left Borders**:
   In `src/HousingApplication.Web/wwwroot/css/styles.css`:
   - Updated `html.dark .house-card` to only set `border-top-color: #1e293b;`, `border-right-color: #1e293b;`, and `border-bottom-color: #1e293b;`, avoiding shorthand `border-color`.
   - Updated `html.dark .house-card:hover` to only set `border-top-color: #3b82f6;`, `border-right-color: #3b82f6;`, and `border-bottom-color: #3b82f6;`, ensuring hover outline highlights top/right/bottom while leaving the left indicator intact.
2. **Explicit Tenure Duration Rules**:
   Added dedicated dark-mode duration indicator rules at rest and on hover with `!important` to prevent any parent slate border rules from clobbering:
   - Emerald `< 5y` (`.border-l-emerald-500`): `#10b981 !important;`
   - Amber `5–10y` (`.border-l-amber-500`): `#f59e0b !important;`
   - Rose `> 10y` (`.border-l-rose-500`): `#f43f5e !important;`
   - Slate `vacant` (`.border-l-slate-300`, `.dark:border-l-slate-600`): `#475569 !important;`
3. **Harmonized Tenant Row Border**:
   - Added `html.dark .border-rose-200\/80` to match emerald and amber implementations for tenant overview items.
4. **Synchronized Distribution Output**:
   - Synchronized `src/HousingApplication.Web/wwwroot/css/styles.css` to `dist/win-x64/wwwroot/css/styles.css` maintaining 100% byte parity.
5. **Comprehensive Automated Tests**:
   - Added Section 11 in `tests/web/components/dark_mode_and_tablet.test.js` covering dark mode duration border preservation and non-overriding rules.
   - Added new end-to-end component test suite `tests/web/components/dark_mode_house_card_colors.test.js` testing DOM rendering and CSS rule assertions across all tenure durations and vacant houses.

## Verification
- `npm test`: 33 test files passed, 378 tests passed (including all dark mode and area grid card tests).
- `dotnet test`: 925 tests passed (HousingApplication.Tests).
- Byte parity between `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`: 100% verified identical.
