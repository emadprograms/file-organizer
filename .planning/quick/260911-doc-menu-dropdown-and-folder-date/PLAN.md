# Quick Task Plan: Document 3-Dots Dropdown Action Menu & Folders Section Document Date Badge (QCK-08)

**Task ID**: `260911-doc-menu-dropdown-and-folder-date`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-08)  
**Status**: In Progress  
**Date**: 2026-09-11  

## Objective
Replace the heavy, obsolete Document Action Modal (`#doc-action-modal`) when clicking the 3-dots button with a sleek, floating dropdown action menu providing quick access to Rename, Move, Copy, Delete, and Show in Timeline. In addition, add an always-visible document date badge with light gray background in the Folders / Categories section directly before the 3-dots button.

## User Intent & Requirements
1. **Document 3-Dots Dropdown Action Menu (`.doc-dropdown-menu`)**:
   - When clicking the 3-dots button (`.doc-menu-btn`) on a document row or card (in Categories view or Timeline view), do not open the large modal dialog.
   - Display a lightweight floating context menu with:
     - **Rename Document**: Triggers inline editing on the document title.
     - **Move Document**: Opens the Move dialog configured for this document.
     - **Copy Document**: Opens the Copy dialog configured for this document.
     - **Show in Timeline**: Opens the Timeline view tab, smoothly scrolls to the document card, and highlights it with a temporary pulse/glow so the user sees its exact location.
     - **Delete Document**: Prompts for confirmation and permanently deletes the document via `DELETE /api/areas/{area}/houses/{house}/documents/{vault_id}`.
   - Clicking outside or pressing Escape cleanly dismisses the dropdown menu.
2. **Folders Section Document Date Badge**:
   - In `categories-view.js`, add a small text badge with light gray background (`bg-slate-100 text-slate-500 font-mono text-[10px] px-1.5 py-0.5 rounded border border-slate-200/60`) right before the 3-dots button showing the document date (`doc.date || doc.dates[0] || doc.primary_date || 'No Date'`).
3. **Asset Synchronization & Testing**:
   - Synchronize all frontend changes to `web-net/wwwroot/` via `dotnet build`.
   - Add unit tests in `tests/frontend/components/` validating the dropdown menu, its 5 actions, and the date badge.
   - Verify all test suites pass (Vitest, .NET xUnit, Python pytest).
