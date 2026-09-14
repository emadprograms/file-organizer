# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## dark-mode-tablet-overhaul — Dark mode overhaul with semantic palette, surface elevation, and tablet optimizations
- **Date:** 2026-09-14
- **Error patterns:** dark mode, tablet, ugly, black filter, pastel badges, contrast, surface elevation
- **Root cause:** Naive global CSS class overrides (.bg-white, .bg-slate-50) missed opacity utilities (bg-slate-50/70, bg-slate-200/60), left jarring un-themed pastel badges (emerald, amber, rose, purple), inverted hover states, lacked surface elevation depth for tablets, and lacked eye-friendly PDF canvas framing.
- **Fix:** Implemented full CSS semantic tokens (:root and html.dark), multi-tier surface elevation system, non-blinding tinted status badges, dark table zebra striping, dark modal overlays, dark PDF viewer framing, and dedicated iPad/tablet responsive rules (768px-1024px).
- **Files changed:** src/HousingApplication.Web/wwwroot/css/styles.css, src/HousingApplication.Web/wwwroot/index.html, dist/win-x64/wwwroot/css/styles.css, dist/win-x64/wwwroot/index.html, tests/web/components/dark_mode_and_tablet.test.js, docs/ARCHITECTURE.md, docs/DEVELOPMENT.md
---

## light-mode-contrast-fix — Light mode whiteness reduction, contrast harmonization, and border restoration
- **Date:** 2026-09-14
- **Error patterns:** light mode, too white, borders greyer, ugly, out of contrast, out of place, selection grey
- **Root cause:** Inverting contrast by globally overriding .bg-slate-50 and .bg-slate-100 to muddy dark slate (#edf0f5, #e4e8ef), increasing root border tokens to #cbd5e1, and applying 1px double-border box-shadow rings to cards, while leaving card surfaces stark white (99% luminance). This turned buttons, badges, and borders dirty grey while intensifying card glare against dark backdrops.
- **Fix:** Adopted the Apple macOS / GitHub light theme model: unified neutral anti-glare canvas (#f6f8fa), clean elevated white surfaces (#ffffff) with soft natural drop shadows and no dark box-shadow rings, restored delicate borders (#e2e8f0, #f1f5f9), removed global utility overrides on .bg-slate-50/.bg-slate-100 to keep buttons and badges crisp, and upgraded .doc-row-selected to vibrant light blue (#eff6ff / #93c5fd) with native-style ::selection.
- **Files changed:** src/HousingApplication.Web/wwwroot/css/styles.css, dist/win-x64/wwwroot/css/styles.css, tests/web/components/light_mode_eye_comfort.test.js
---
