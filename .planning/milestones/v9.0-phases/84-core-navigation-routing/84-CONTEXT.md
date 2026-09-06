# Context: Phase 84 - Core Navigation & Routing

## Goals from ROADMAP.md
**Requirements:** [NAV-01, NAV-03]
**Description:** Build the foundational sidebar hierarchy and URL routing system to allow deep linking.
**Success Criteria:**
- User sees a collapsible sidebar populated with Areas, Houses, and Tenants up to 3 levels deep.
- User can expand and collapse levels in the sidebar.
- User visiting a deep link sees the sidebar automatically expand to highlight the corresponding item.

## Current State
- The backend has `/api/houses` which currently just lists directories directly inside `areas_root`.
- The frontend has `index.html` with a basic `#sidebar` div, but no JS logic for a hierarchical sidebar or routing.

## Constraints
- Frontend must be written in vanilla JS/DOM.
- Backend must be written in FastAPI.
- Strict TDD: Must add pytest tests for backend, playwright tests for frontend.
