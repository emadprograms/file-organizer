---
status: complete
date: 2026-09-12
slug: 260912-touch-drag-move-document
quick_task: QCK-35
title: "Touch Press-and-Hold Drag-and-Drop Document Move Support on Tablets"
---

# Quick Task Summary: Touch Press-and-Hold Drag-and-Drop Document Move Support on Tablets

## Overview
Enabled touch-based drag-and-drop document move on tablets and touchscreen devices (e.g. Android tablet, iPad):
- **Press-and-Hold Activation:** Holding finger on a document title/row for $\ge 280$ms initiates touch drag mode with haptic vibration feedback (`navigator.vibrate(40)`).
- **Floating Drag Avatar:** `#touch-drag-avatar` follows the finger with the document title, move icon, and move badge (`نقل • Move`), without scrolling the page (`e.preventDefault()` on drag).
- **Target Folder Highlighting:** Dragging over destination category folder cards applies active visual feedback (`drag-over-active`, `ring-2`, `ring-blue-500`, `bg-blue-50/70`, `dark:bg-blue-900/40`) via `document.elementFromPoint`.
- **Drop & Move Execution:** Releasing finger over destination category folder triggers `handleCategoryDrop`, performing PATCH API move, in-place DOM update (`moveDocInDom`), and toast notification.
- **Accidental Click & Toggle Suppression:** Synchronously sets `_justFinishedTouchDrag` timestamp upon drop, preventing accidental document opening or accordion card toggling.
- **Normal Gestures Preserved:** Swiping $> 8$px before 280ms cancels the timer for normal list scrolling; quick taps ($< 280$ms) open the document normally.

## Verification
- **Frontend Unit Tests (Vitest):** 232 tests passed across 24 test files (100%), including 16 tests in `touch_and_mobile_interactions.test.js`.
- **.NET Core xUnit Tests:** 146 tests passed (100%).
- **Multi-Stack Parity:** 0 diff across `src/api/static/`, `web-net/wwwroot/`, and `dist/win-x64/wwwroot/`.
