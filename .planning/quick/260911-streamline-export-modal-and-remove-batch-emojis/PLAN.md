# Quick Task Plan: Streamline Export Modal & Remove Batch Button Emojis (QCK-07)

**Task ID**: `260911-streamline-export-modal-and-remove-batch-emojis`  
**Milestone**: v14.0 Power-User Operations & Portfolio Expansion (QCK-07)  
**Status**: Completed  
**Date**: 2026-09-11  

## Objective
Streamline the House Archive Export Options Modal (`#export-archive-modal`) by stripping verbose explanatory text in favor of an intuitive, clean visual design, and remove distracting emojis from the floating batch operations bar (`#batch-action-bar`) on Move, Copy, and Delete buttons while preserving the helpful `✕` glyph on the Deselect button.

## User Intent & Requirements
1. **Batch Action Bar (`#batch-action-bar`)**:
   - Keep selection text: "Move Selected", "Copy Selected", "Delete Selected", "Deselect".
   - Remove emojis (`📁`, `📋`, and `🗑️`) from the Move, Copy, and Delete buttons to eliminate distraction.
   - Retain the `✕` icon on `#btn-batch-deselect` (`<span>✕</span><span>Deselect</span>`) as helpful visual reinforcement for clearing selection.
2. **Download Archive Options Modal (`#export-archive-modal`)**:
   - Transition from explanatory verbose text to intuitive visual-first presentation.
   - **Header**: Title is `تصدير الأرشيف • Export Archive`; remove the explanatory subtitle paragraph completely.
   - **Format Options**:
     - Label: `صيغة التصدير • Format`.
     - Card A (ZIP): Emoji `📦`, Title `ZIP`, Subtitle tag `مجلدات • Folders`. Remove long explanatory paragraph.
     - Card B (PDF): Emoji `📄`, Title `PDF`, Subtitle tag `تسلسل زمني • Timeline`. Remove long explanatory paragraph.
   - **Tenant Scope**:
     - Label: `المستأجر • Tenant`.
     - Remove explanatory paragraph completely.
     - Default option text: `🏛️ كامل السجل • All Records` (updated in both `index.html` and `house-profile.js`).
   - **Modal Footer**:
     - Cancel button: `Cancel`.
     - Download button: `<span id="export-archive-btn-text">⬇️ Download</span>`.
3. **Synchronization**:
   - Recompile and copy static files via `~/.dotnet/dotnet build web-net/FileOrganizer.Web.csproj`.
   - Verify 0 diff with `diff -ru src/api/static/ web-net/wwwroot/`.
4. **Testing**:
   - Vitest component test suite passing (`npm run test:frontend`).
   - Python pytest backend test suite passing (`.venv/bin/pytest tests/test_v14_features.py tests/test_document_management_api.py -v`).
   - ASP.NET Core xUnit test suite passing (`~/.dotnet/dotnet test web-net/FileOrganizer.Tests/`).
