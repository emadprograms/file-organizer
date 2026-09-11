# Quick Task Plan: Category-Specific Folder Icons (01-13) & Empty Folder for Custom (14+)

**Task ID**: `260911-fdi`  
**Slug**: `folder-specific-icons-for-categories-01-`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-11)  
**Status**: Completed  
**Date**: 2026-09-11  

## Objective
Implement descriptive, purposeful Heroicons outline icons for each of the standard categories 01 through 13 in the Folders view, while using the standard empty folder icon for custom folders (14 onwards).

## Requirements
1. **Standard Categories (01 to 13)**:
   - 01 - بيانات أساسية: Home icon (base property data)
   - 02 - بيانات شخصية: User icon (personal/tenant identity)
   - 03 - أمر تخصيص: Clipboard Check icon (allocation decree / official assignment)
   - 04 - محضر تسليم مفتاح: Key icon (key handover record)
   - 05 - عقود: Document Text icon (contracts & lease agreements)
   - 06 - كهرباء وماء: Lightning Bolt icon (utilities, electricity & water)
   - 07 - استقطاع إيجار: Cash / Banknotes icon (rent salary deduction)
   - 08 - وقف استقطاع بدل: Ban / Stop icon (stop allowance deduction)
   - 09 - إشعارات: Bell icon (notifications & official notices)
   - 10 - صيانة: Wrench icon (maintenance & repair)
   - 11 - صور ومعاينات: Camera icon (photos & site inspections)
   - 12 - تعديلات: Pencil / Edit icon (renovations & alterations)
   - 13 - رسائل متنوعة: Mail / Envelope icon (miscellaneous letters)
2. **Custom Folders (14 onwards & user-created)**:
   - Always render the empty folder icon (`M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z`).
3. **Implementation & Tests**:
   - Implement `getFolderIconSvg(folderName)` in `src/api/static/js/categories-view.js`.
   - Update `renderCategories()` to render the icon returned by `getFolderIconSvg(cat.name)`.
   - Synchronize changes to `web-net/wwwroot/js/categories-view.js`.
   - Expose `getFolderIconSvg` on `window` for testability and other components.
   - Add comprehensive unit tests in `tests/frontend/components/categories_view.test.js` (or a dedicated test file) asserting each folder 01-13 receives its distinct descriptive icon, and 14+ / custom folders receive the empty folder icon.
   - Run Vitest suite to verify 100% pass.
