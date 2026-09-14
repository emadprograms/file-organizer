---
status: resolved
trigger: "why did you remove the colored borders of the cards? how were they affecting the light mode harshness. why break something to fix something? the white is still quite white too. you literallly didn't do anything and broke things."
created: 2026-09-14
updated: 2026-09-14
---

## Current Focus
- hypothesis: The 4-side `border-color` shorthand in `html:not(.dark) .house-card` and `html:not(.dark) .category-folder-card` overrode Tailwind's `border-l-[5px] border-l-emerald-500`, `border-l-amber-500`, `border-l-rose-500`, and `border-l-slate-300` stripes.
- resolution: Removed `border-color` completely from `.house-card` and `.category-folder-card`. Calibrated the background colors: canvas to `#edf0f4` (~93% luminance) and cards/panels to `#f7f9fb` (~97.5% luminance) to eliminate stark 255 glare while maintaining crisp white appearance and brilliant contrast for colored tenure stripes.
- outcome: Resolved and verified.

## Symptoms
- expected: House cards must retain their 5px colored tenure indicator borders (< 5y emerald green, 5-10y amber yellow, > 10y rose red, vacant slate). Light mode whiteness must be genuinely softened to relieve eye strain without stripping colored indicators or turning elements into muddy grey.
- actual: Colored tenure borders were stripped off house cards (all borders became uniform slate #e2e8f0), while the card surfaces were kept at #ffffff (pure stark white), failing to reduce glare.
- errors: Visual regression; missing tenure indicator borders.
- timeline: Introduced in commit `6c79ddd`.
- reproduction: Open Area Grid view; observe house cards have plain grey left borders instead of green/amber/rose/slate tenure stripes.

## Evidence
- timestamp: 2026-09-14T06:39:00Z
  observation: `src/HousingApplication.Web/wwwroot/css/styles.css` line 163 contains `border-color: #e2e8f0;` and line 169 contains `border-color: #cbd5e1;`. Because CSS `border-color` is a 4-side shorthand, it takes precedence over Tailwind's `border-l-emerald-500`, overriding `border-left-color` to `#e2e8f0`.
- timestamp: 2026-09-14T06:39:30Z
  observation: `src/HousingApplication.Web/wwwroot/css/styles.css` line 162 has `background-color: #ffffff;`, line 133 has `background-color: #ffffff;`, line 125 has `background-color: rgba(255, 255, 255, 0.92);`. These explicit pure `#ffffff` rules prevent any reduction in stark whiteness.

## Resolution
- Root cause: CSS rule `html:not(.dark) .house-card, html:not(.dark) .category-folder-card { border-color: #e2e8f0; }` and hover counterpart set the 4-side `border-color` shorthand, clobbering Tailwind utility classes `border-l-[5px] border-l-emerald-500` etc.
- Fix:
  1. Removed `border-color: #e2e8f0;` and hover `border-color: #cbd5e1;` from `.house-card` and `.category-folder-card`.
  2. Calibrated canvas to `#edf0f4` (`body`, `#area-grid-panel`, `#database-inspector-panel`, `#welcome-panel`, `#document-viewer-panel`).
  3. Calibrated cards and panels to `#f7f9fb` (`#top-navbar`, `#document-list-panel`, `.house-card`, `.category-folder-card`), which appears as a clean elevated white surface on the `#edf0f4` canvas while completely eliminating the 255/255/255 glare laser beam.
  4. Preserved clean white `#ffffff` fill for input fields, textareas, and active segmented tab pills.
  5. Mirrored `styles.css` identically to `dist/win-x64/wwwroot/css/styles.css` (`diff -u` returns 0).
  6. Added automated tests in `tests/web/components/light_mode_eye_comfort.test.js` to strictly enforce that no `border-color` shorthand is applied to `.house-card` or `.category-folder-card`.
- Verification:
  - `npm run test:web`: 30/30 test files passed (333/333 tests).
  - `dotnet test`: 161/161 C# tests passed.
