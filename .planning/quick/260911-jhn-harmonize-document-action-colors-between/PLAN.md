# Quick Task 260911-jhn: Harmonize Document Action Colors Between 3-Dot Menu and Multi-Select Bar

## Goal
Establish a unified, consistent color-coding scheme for document actions across both the 3-dot dropdown menu and the multi-select batch action bar:
- **Move**: Amber/Orange (`amber-600` / `amber-500`)
- **Copy**: Indigo/Purple (`indigo-600` / `indigo-500`)
- **Delete**: Rose/Red (`rose-600` / `rose-500`)
- **Rename**: Blue (`blue-500`)
- **Timeline**: Emerald (`emerald-500`)

Retain full, consistent action labels in the 3-dot dropdown menu ("Rename Document", "Move Document", "Copy Document", "Show in Timeline", "Delete Document") to maintain balanced item length.

## Tasks
1. **Update Batch Action Bar & Move Modal**:
   - Change `#btn-batch-move` to `bg-amber-600 hover:bg-amber-500`.
   - Update `#batch-move-modal` header icon, inputs focus rings, and confirm button to amber palette.
2. **Update 3-Dot Dropdown Menu**:
   - Align hover styles with icon colors (`hover:bg-amber-50 hover:text-amber-700` for Move, `hover:bg-indigo-50 hover:text-indigo-700` for Copy, `hover:bg-emerald-50 hover:text-emerald-700` for Timeline, `hover:bg-blue-50 hover:text-blue-700` for Rename, `hover:bg-rose-50 hover:text-rose-700` for Delete).
3. **Synchronize & Bump Cache Buster**:
   - Sync `web-net/wwwroot/` and bump cache busters to `?v=260911-21`.
4. **Update Milestone Docs**:
   - Add QCK-13 to `.planning/milestones/v14.0-ROADMAP.md` and update `.planning/STATE.md`.
