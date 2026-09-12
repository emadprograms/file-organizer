---
status: investigating
trigger: "when selecting the move document option by default the tenant whose folder you are in, his name should appear. when I click on the 3 dots or multi-select it sometimes shows random, sometimes latest tenant. No. the name of the tenant should be the one that is open. second of all, the lock pin. there is no way to unlock the documents and reset to auto. suppose user drageed the wrong files and later wants to change the tenant dates. reconclication won't work on those locked (or pinned) files. there should be way to unlock them. add this to the 3 dots for documents that are pinned. Unpin or pin both. suppose the document is in the correct place and the user wants to pin it. He can it pin it from the 3 dots too. and when in categories there is show in timeline option when clicking on 3 dots. when in the timeline. clicking on 3 dots should give a show in categories options. fix these. update milestone docs. make tests. commit and push changes."
created: 2026-09-12
updated: 2026-09-12
---

## Symptoms
1. **Move Document Tenant Pre-selection**: When opening the Move Document modal (either via 3 dots on a single document or via batch multi-select), the tenant dropdown (`#batch-move-tenant-select`) does not reliably select the tenant whose folder is currently open. Instead, it preserves stale previous selections (`prevVal`), picks random entries from `selectedDocIds` Set iteration order, or falls back to the latest active tenant from the database query's `ORDER BY`.
2. **Lock / Pin Toggle**: There is no option in the 3-dots action menu to unpin/unlock documents (`is_manual = 0`) so they can participate in auto-reconciliation when tenant dates are adjusted, nor to manually pin unpinned documents (`is_manual = 1`).
3. **Timeline-to-Categories Navigation**: While Categories view provides a "Show in Timeline" option in the 3-dots menu, the 3-dots menu in Timeline view still displays "Show in Timeline" instead of switching to "Show in Categories".

## Current Focus
- hypothesis: Stale DOM select values, inverted precedence in tenant resolution, missing 3-dots pin/unpin action, and static menu item labels in doc-manager.js cause these UX inconsistencies.
- next_action: Implement fixes across categories-view.js and doc-manager.js, synchronize static assets, update .NET and Python backends if needed, write tests, update milestone docs, commit and push.
