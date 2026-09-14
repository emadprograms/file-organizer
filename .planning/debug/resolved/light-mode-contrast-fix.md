---
status: resolved
trigger: "this isn't what I had in mind. the white background is still very white but the selection and borders and everything have all become greyer making them look ugly and out of contrast and out of place. This isn't what I had in mind at all."
created: 2026-09-14
updated: 2026-09-14
---

## Current Focus
- hypothesis: The changes in commit `4ae590d` attempted to reduce light mode glare by darkening the page canvas and utility classes (`body`, `.bg-slate-50`, `.bg-slate-100`, `#document-viewer-panel`) down to muddy grey tones (`#edf0f5`, `#e4e8ef`, `#e8ecf2`) and adding a heavy `1px rgba(226, 232, 240, 0.8)` ring box-shadow on cards, while leaving the primary visual surfaces (cards at `#fbfcfd` and `.bg-white` at `#f8fafc`) virtually 99% stark white. This inverted the visual contrast hierarchy: buttons and badges turned into dark grey rectangles, borders doubled in thickness and turned visibly grey, while the cards themselves continued to glaringly project 99% pure white light against muddy grey backdrops.
- test: Verified calibrated CSS rules adhering to the Apple macOS / GitHub light theme model: calm neutral canvas (`#f6f8fa`), delicate crisp borders (`#e2e8f0`), clean elevated surfaces (`#ffffff` without box-shadow rings), vibrant delicate selection (`#eff6ff` / `#3b82f6`), and unmolested utility classes for buttons and badges.
- resolution: Cleaned `styles.css` (both in `src/` and `dist/win-x64/`), eliminated dark rings and global utility overrides, updated unit test suite `tests/web/components/light_mode_eye_comfort.test.js`, and verified 100% pass across all 30 Vitest test suites (331 tests) and 161 .NET tests.

## Symptoms
- **Expected**: A calm, comfortable light mode with reduced glare ("basically make it a bit greyer. the grey shouldn't be visible but the whiteness should be reduced") where background surfaces are soft on the eyes without borders, buttons, badges, and selection turning into dark, muddy grey outlines.
- **Actual**: The primary card surfaces remained glaringly white, while navbar buttons, badges, segmented tab tracks, and card borders turned noticeably dark grey and muddy, making the UI look disjointed, fragmented, and "ugly and out of contrast and out of place".
- **Reproduction**:
  1. Open the application in default light mode.
  2. Notice navbar action triggers (`#btn-search-trigger`, `#btn-shortcuts-trigger`, `#btn-theme-toggle`, `#sidebar-toggle-btn`) and badges (`.doc-date-badge`, `.doc-count-badge`, tenant badges) rendering in muddy dark slate `#edf0f5` / `#e4e8ef`.
  3. Notice house cards and category folder cards having a prominent, dark double-border ring caused by `box-shadow: 0 0 0 1px rgba(226, 232, 240, 0.8)`.
  4. Notice card surfaces (`#fbfcfd`) remaining visually stark white (99% luminance), standing out starkly against the dirty grey canvas (`#edf0f5`).

## Root Cause Analysis
1. **Inverted Contrast Hierarchy & Stark White Card Retention**:
   - The user spends >90% of visual focus looking at house cards (`.house-card`), folder cards (`.category-folder-card`), timeline cards, and document panels.
   - In commit `4ae590d`, cards were styled with `background-color: #fbfcfd;` (RGB 251, 252, 253; 98.6% luminance), and `.bg-white` was set to `#f8fafc` (97.6% luminance). Both are virtually indistinguishable from pure `#ffffff`.
   - Meanwhile, the canvas and panels were pushed down to `#edf0f5` (88% luminance) and `#e4e8ef` (84% luminance).
   - This widened the luminance gap between cards and canvas, causing the white cards to punch through with intensified glare rather than softened comfort.
2. **Aggressive Hijacking of Tailwind Utility Selectors**:
   - Overriding `html:not(.dark) .bg-slate-50 { background-color: #edf0f5; }` and `html:not(.dark) .bg-slate-100 { background-color: #e4e8ef; }` globally caused widespread collateral damage:
     - Navbar buttons (`#btn-search-trigger`, `#btn-shortcuts-trigger`, `#btn-theme-toggle`, `#sidebar-toggle-btn`, `#back-to-grid-btn`) turned into dark grey rectangles.
     - Document metadata badges (`.doc-date-badge`, `.doc-count-badge`, tenant pills) turned into dark muddy grey blobs.
     - Table header cells and empty state boxes became dark slate blocks.
3. **Card Box-Shadow 1px Outline Ring**:
   - Commit `4ae590d` added `box-shadow: 0 1px 2px 0 rgba(15, 23, 42, 0.04), 0 0 0 1px rgba(226, 232, 240, 0.8);` to `.house-card` and `.category-folder-card`.
   - On top of Tailwind's existing `border border-slate-200`, this synthetic 1px ring doubled border thickness and deepened border opacity, creating an unsightly dark grey frame around every card.
4. **Darkened Root Border Tokens**:
   - `:root` tokens were adjusted so `--border-default: #cbd5e1;` (slate-300) and `--border-emphasis: #94a3b8;` (slate-400), shifting light mode boundaries to heavy, dark strokes.
5. **Selection & Active State Mismatch**:
   - `.doc-row-selected` and active tab pills contrasted abruptly against mismatched muddy panel backgrounds, appearing disconnected and harsh.

## Harmonious Solution (Apple macOS / GitHub Light Theme Model)
1. **Calm Unified Neutral Canvas (`#f6f8fa`)**:
   - Replaced all dirty grey canvas colors (`#edf0f5`, `#e4e8ef`, `#e8ecf2`) with a uniform, glare-free neutral background:
     - `html:not(.dark) body`: `#f6f8fa`
     - `html:not(.dark) #area-grid-panel, html:not(.dark) #database-inspector-panel, html:not(.dark) #welcome-panel`: `#f6f8fa`
     - `html:not(.dark) #document-viewer-panel`: `#f1f5f9` (soft neutral backing behind document view)
   - At ~97% luminance with balanced blue-slate undertone, `#f6f8fa` eliminates blinding 100% white glare without looking "grey" or "dirty".
2. **Clean Elevated White Surfaces Without Dark Rings**:
   - Styled `.house-card, .category-folder-card` with clean elevated `#ffffff`, crisp delicate border `#e2e8f0`, and gentle soft shadow:
     `box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02);`
   - Completely eliminated the `0 0 0 1px rgba(226, 232, 240, 0.8)` ring box-shadow.
3. **Clean Delicate Borders**:
   - Restored `:root` tokens:
     - `--border-subtle: #f1f5f9;`
     - `--border-default: #e2e8f0;`
     - `--border-emphasis: #cbd5e1;`
   - Restored delicate 1px border styling across `#top-navbar` (`#e2e8f0`), `#document-list-panel` (`#e2e8f0`), and input fields (`#e2e8f0`).
4. **Preserved Utility Classes for Buttons & Badges**:
   - Removed global overrides for `.bg-slate-50` and `.bg-slate-100`.
   - Restored authentic Tailwind rendering for search buttons (`bg-slate-50/80`), icon buttons, badges (`.doc-date-badge`, `.doc-count-badge`), and tab capsules (`bg-slate-200/60`).
5. **Vibrant & Delicate macOS/GitHub Selection**:
   - Updated `.doc-row-selected` to:
     - `background-color: #eff6ff !important;` (Tailwind blue-50)
     - `border-color: #93c5fd !important;` (Tailwind blue-300)
     - `box-shadow: inset 0 0 0 1.5px #3b82f6, 0 1px 2px 0 rgba(59, 130, 246, 0.08) !important;`
   - Added delicate macOS-style `::selection` rule: `background-color: #bfdbfe; color: #1e3a8a;` (and `html.dark ::selection`: `background-color: #1d4ed8; color: #ffffff;`).

## Evidence & Verification
- **Automated Tests**:
  - Updated `tests/web/components/light_mode_eye_comfort.test.js` to assert the calibrated design system tokens and rules.
  - Vitest test suite run: **30 test files passed, 331 tests passed** (0 failures).
  - .NET test suite run: **161 tests passed** (0 failures).
- **Static Asset Parity**:
  - Verified 100% byte-for-byte parity between `src/HousingApplication.Web/wwwroot/css/styles.css` and `dist/win-x64/wwwroot/css/styles.css`.
- **Dark Mode Protection**:
  - All 27 dark mode tests in `tests/web/components/dark_mode_and_tablet.test.js` passed without modification, confirming dark mode remains 100% untouched and functional.
