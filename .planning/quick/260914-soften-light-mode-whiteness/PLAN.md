# Quick Plan: Soften Light Mode Whiteness for Eye Comfort

## User Requirement
"reduce the whiteness in light mode.. like its too white. I don't want it that white. basically make it a bit greyer. the grey shouldn't be visible but the whitness should be reduced."

## Context & Objectives
In default light mode, pure `#ffffff` (`bg-white`) combined with Tailwind's near-white `bg-slate-50` (`#f8fafc` at 98% luminance) causes high screen glare and eye fatigue.
The goal is to:
1. Reduce stark whiteness across light mode surfaces without making the UI look visibly grey, dirty, or drab.
2. Soften the base canvas / workspace backgrounds (`bg-slate-50`, `bg-slate-100`, body) to an eye-pleasing neutral slate tint (`#edf0f5` / `#e4e8ef`).
3. Soften stark `#ffffff` elevated surfaces (`bg-white`, `bg-white/90`) to a gentle off-white (`#f8fafc` / `#fbfcfd`) that feels clean and white to the eye but eliminates the harsh 255/255/255 glare.
4. Ensure dark mode remains 100% unaffected.
5. Maintain 100% static asset parity across `src/HousingApplication.Web/wwwroot/` and `dist/win-x64/wwwroot/`.
6. Maintain 100% pass rate across all Vitest frontend and .NET backend test suites.

## Affected Files
- `src/HousingApplication.Web/wwwroot/css/styles.css`
- `dist/win-x64/wwwroot/css/styles.css`
- `tests/web/components/light_mode_eye_comfort.test.js` (new)
- `.planning/quick/260914-soften-light-mode-whiteness/PLAN.md`
- `.planning/quick/260914-soften-light-mode-whiteness/SUMMARY.md`
- `.planning/STATE.md`

## Implementation Tasks

### Task 1: Calibrate Light Mode Surfaces in `styles.css`
- In `styles.css`, update `:root` semantic tokens for light mode:
  - `--surface-canvas`: `#edf0f5`
  - `--surface-panel`: `#f6f8fb`
  - `--surface-card`: `#f9fafb`
  - `--surface-elevated`: `#ffffff`
  - `--surface-hover`: `#eef2f6`
- Add scoped light mode rules (`html:not(.dark)`):
  - `html:not(.dark) body`: `#edf0f5`
  - `html:not(.dark) .bg-slate-50`: `#edf0f5`
  - `html:not(.dark) .bg-slate-100`: `#e4e8ef`
  - `html:not(.dark) .bg-white`: `#f8fafc`
  - `html:not(.dark) .bg-white\/90`: `rgba(248, 250, 252, 0.92)`
  - `html:not(.dark) .bg-white\/95`: `rgba(248, 250, 252, 0.96)`
  - `html:not(.dark) #top-navbar`: `rgba(248, 250, 252, 0.92)` with border `#e2e8f0`
  - `html:not(.dark) #document-list-panel`: `#f5f7fa` with border `#e2e8f0`
  - `html:not(.dark) #area-grid-panel, html:not(.dark) #database-inspector-panel`: `#edf0f5`
  - `html:not(.dark) #document-viewer-panel`: `#e8ecf2`
  - `html:not(.dark) input:not([type="checkbox"]):not([type="radio"]), html:not(.dark) select, html:not(.dark) textarea`: `#ffffff`
  - Active segmented tabs (`#tab-categories.bg-white`, `#tab-timeline.bg-white`): `#ffffff` with subtle contrast
  - Card subtle elevation (`.house-card`, `.category-folder-card`): subtle shadow and crisp border
- Mirror identical changes to `dist/win-x64/wwwroot/css/styles.css`.

### Task 2: Automated Tests
- Create `tests/web/components/light_mode_eye_comfort.test.js` verifying:
  - Light mode surface tokens and rules exist and target `html:not(.dark)`.
  - Stark white `.bg-white` is softened to `#f8fafc` in light mode.
  - Main panels (`#top-navbar`, `#document-list-panel`, `#area-grid-panel`) have light mode calibrations.
  - Dark mode rules remain strictly intact.
  - 100% byte parity between `src/` and `dist/` for `styles.css`.
- Run `npm run test:web` and `~/.dotnet/dotnet test tests/HousingApplication.Tests/HousingApplication.Tests.csproj`.

### Task 3: Documentation & Release
- Generate `SUMMARY.md` in `.planning/quick/260914-soften-light-mode-whiteness/`.
- Update `.planning/STATE.md` with entry under "Quick Tasks Completed".
- Commit and push to `origin main`.
