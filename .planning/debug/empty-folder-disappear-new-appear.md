---
status: resolved
trigger: "except in cases where the folder becomes empty and a new folder is created upon moving the document. you need to show the folder disappearing the new folder re-appearing."
created: 2026-09-12
updated: 2026-09-12
---

## Current Focus
- hypothesis: In `moveDocInDom` and `copyDocInDom`, source folders are not removed from the DOM when their count drops to 0, and target folders are not dynamically constructed and inserted when `findCard(targetCatName)` is null.
- test: Test `moveDocInDom` when source folder count reaches 0 (verify source card is removed) and when target folder does not exist (verify target card is created and inserted at sorted position).
- expecting: Empty source folder disappears from DOM, new target folder appears at sorted position with document inside and correct count badge.
- resolution: Implemented `createCategoryCardElement(cat)` and `insertCategoryCardSorted(card, catName)`. In `moveDocInDom`, when `remainingCount === 0`, remove `sourceCard`, prune `openCategoryNames`, clean up `cats`, and show empty state if no folders remain. If `!targetCard`, dynamically create the category card, open it, and insert it at sorted position. In `copyDocInDom`, if `!targetCard`, create and insert the category card at sorted position.

## Symptoms
- **Expected**:
  1. When moving the last document out of a category folder, the folder becomes empty and disappears from the categories view.
  2. When moving or copying a document into a newly created or previously empty folder, the new folder appears in the categories view at its proper alphabetical/numerical sorted position with document count badge and document row.
  3. Non-empty existing folders preserve their open/closed accordion state and scroll does not jump.
- **Actual**:
  1. Empty folders stay in the DOM with a count badge of `0`.
  2. Newly created or previously empty folders never appear in the DOM because `findCard(targetCatName)` returns null and `moveDocInDom`/`copyDocInDom` fails or removes the document without creating the card.

## Evidence
- `categories-view.js:1317-1331`:
  When `targetCard` was null, `moveDocInDom` removed `docEl` and returned without creating the folder card.
- `categories-view.js:1351-1359`:
  When `count === 0`, `sourceCard` was not removed from the DOM.

## Verification
- Added 3 unit tests in `tests/frontend/components/category_folder_persistence.test.js`:
  1. `shows folder disappearing when all its documents are moved out and it becomes empty`
  2. `shows new folder appearing at sorted position when document is moved into a new folder`
  3. `handles folder disappearing and re-appearing when moving document out and then back in`
- Ran `npm run test:frontend`: All 22 test files and 200 tests passed (100%).
- Synced changes across `src/api/static/js/categories-view.js`, `web-net/wwwroot/js/categories-view.js`, and `dist/win-x64/wwwroot/js/categories-view.js`.
