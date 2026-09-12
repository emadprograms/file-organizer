---
status: investigating
trigger: "when I move the document to another tenant in the same house. the document doesn't moves but it still keeps showing until I click refresh. take a look at this. it works fine and disappears if I move into the same tenant but when I multiselect or single select and move to another tenant in the same house. it doesn't disappear. make tests. fix this. update the milestone. commit and push changes."
created: 2026-09-12
updated: 2026-09-12
---

## Symptoms
- **Expected**:
  - When moving document(s) (either via single select / 3-dots Move Document modal, or multi-select Batch Move modal, or drag-and-drop) to another tenant in the same house, the document(s) should immediately be removed from the current tenant's category folder view without requiring a manual page refresh.
- **Actual**:
  - Moving within the same tenant updates the DOM/disappears from the old folder, but when moving to another tenant in the same house, the document still keeps showing in the current view until the user clicks refresh.
- **Reproduction**:
  - Open a house and drill down into a tenant's category folder.
  - Select one document (via 3-dots Move Document) or multiple documents (via multi-select -> Move Selected).
  - Select a different tenant from the tenant dropdown in the move modal (in the same house), and confirm the move.
  - Observe that the document remains visible in the current folder list until refresh is manually clicked.

## Current Focus
- **hypothesis**: In categories-view.js / doc-manager.js, when moving a document to a different tenant, either the DOM removal logic assumes the target is in the current tenant's folder list (e.g., calling `moveDocInDom` which tries to find the target folder in the current DOM, or failing to remove the element when the target tenant is different), or `moveDocInDom` expects the document to move to a folder on the page, or the backend response is handled differently when tenant_id changes.
- **next_action**: Inspect `handleBatchMoveConfirm`, `executeMoveDocument`, `moveDocInDom`, and related move handlers in `categories-view.js` and `doc-manager.js`.
