# Phase 88: View Mode Switcher & Area Grid Layout — Context

## Goal
Enable users to switch between the classic Tree View and an Area Grid Overview. In Grid View mode, the sidebar shows only Areas, and clicking an Area displays a responsive Grid of House Cards in the main view.

## Scope
- Add View Switcher control at top of sidebar or header (Tree View vs Grid View).
- Conditionally render sidebar in Tree View mode (full hierarchy) vs Grid View mode (areas only).
- Add `#area-grid-panel` in main layout to display the house grid when an area is selected.
- Handle state and URL routing to preserve active view and area selection.
