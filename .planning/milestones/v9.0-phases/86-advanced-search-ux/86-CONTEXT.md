# Phase 86 Context: Advanced Search UX

## Requirements
- **NAV-06**: User can open the search bar instantly using a Cmd/Ctrl+K keyboard shortcut.
- **NAV-07**: User sees instant top matches for search queries as they type, before full submission (Zero-Click).

## Success Criteria
- User pressing Cmd/Ctrl+K focuses the search bar from anywhere on the page.
- User typing in the search bar sees top results appear instantly below the bar without pressing Enter.
- User clicking on an instant result navigates immediately to the relevant view.

## Dependencies
- Phase 85 (Global Search & Empty States) has been completed, meaning we already have a search input and some way to display results upon submission.
- Frontend uses vanilla JS/DOM and Playwright for tests.
