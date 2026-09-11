---
status: complete
quick_id: 260911-fdi
slug: folder-specific-icons-for-categories-01-
date: 2026-09-11
description: Category-Specific Folder Icons for Standard Folders (01-13) and Empty Folder for Custom Folders (14+)
commit: HEAD
---

# Quick Task Summary: Category-Specific Folder Icons (01-13) & Empty Folder for Custom (14+)

**Task ID**: `260911-fdi`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-11)  
**Status**: Complete  
**Date**: 2026-09-11  

## Overview
Enhanced the Folders / Categories view (`categories-view.js`) by replacing generic empty folder icons with tailored, purpose-built Heroicons outline icons for all 13 standard folders, while retaining the clean empty folder icon for any custom user folders (14 onwards).

## Accomplishments
1. **Descriptive Category Icons (01 to 13)**:
   - `01 - بيانات أساسية`: Property / Home icon (`M3 12l2-2...`) representing master property deed and house data.
   - `02 - بيانات شخصية`: User identity icon (`M16 7a4 4 0 11-8...`) representing tenant personal/civil records.
   - `03 - أمر تخصيص`: Clipboard Check decree icon (`M9 5H7a2 2 0...`) representing official allocation orders.
   - `04 - محضر تسليم مفتاح`: Key icon (`M15 7a2 2 0...`) representing key delivery and handover minutes.
   - `05 - عقود`: Document Text icon (`M9 12h6m-6...`) representing contracts and lease agreements.
   - `06 - كهرباء وماء`: Lightning Bolt icon (`M13 10V3L4...`) representing utilities (MEW).
   - `07 - استقطاع إيجار`: Banknotes / Cash icon (`M17 9V7a2...`) representing rent payment deductions.
   - `08 - وقف استقطاع بدل`: Ban / Stop sign icon (`M18.364 18.364...`) representing cessation/halt of allowance deductions.
   - `09 - إشعارات`: Bell notification icon (`M15 17h5...`) representing notices and warnings.
   - `10 - صيانة`: Wrench tool icon (`M14.7 6.3a1...`) representing maintenance works.
   - `11 - صور ومعاينات`: Camera icon (`M3 9a2...`) representing photographic site surveys and inspections.
   - `12 - تعديلات`: Pencil / Edit icon (`M11 5H6...`) representing renovation and property alterations.
   - `13 - رسائل متنوعة`: Envelope / Mail icon (`M3 8l7.89...`) representing general correspondence.
2. **Custom Folder Fallback (14 onwards & user-created)**:
   - Any folder with numeric prefix 14 or higher (e.g., `14 - تصاريح بناء`), or unnumbered custom user categories, consistently renders the standard empty folder icon (`M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z`).
3. **Architecture & Testing**:
   - Implemented `getFolderIconSvg(name)` resolver supporting both prefixed and un-prefixed category lookups.
   - Added `.folder-icon-box` container wrapper for clean styling and testing.
   - Exported `getFolderIconSvg`, `FOLDER_ICONS`, and `EMPTY_FOLDER_SVG` on both `window` and `module.exports`.
   - Synchronized `src/api/static/js/categories-view.js` with `web-net/wwwroot/js/categories-view.js` (zero diff).
   - Added unit test suite `tests/frontend/components/categories_folder_icons.test.js` (5 tests, 100% passing).
   - All 133 frontend Vitest tests across 12 files pass cleanly.
