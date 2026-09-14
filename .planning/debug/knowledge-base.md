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
