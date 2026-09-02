# Roadmap: File Organizer

## Milestones

- 🚧 **v9.0 Hierarchical Web Dashboard** — Phases 84-87 (in progress)
- ✅ **v8.0 Web-Based File Viewer** — Phases 81-83 (shipped 2026-09-02)

## Phases

### 🚧 v9.0 Hierarchical Web Dashboard

#### Phase 84: Core Navigation & Routing

**Requirements:** [NAV-01, NAV-03]
**Description:** Build the foundational sidebar hierarchy and URL routing system to allow deep linking.
**Success Criteria:**

- User sees a collapsible sidebar populated with Areas, Houses, and Tenants up to 3 levels deep.
- User can expand and collapse levels in the sidebar.
- User visiting a deep link sees the sidebar automatically expand to highlight the corresponding item.

#### Phase 85: Global Search & Empty States

**Requirements:** [NAV-02, NAV-04, NAV-05]
**Description:** Implement the core global search functionality for finding houses and people, handling keyboard interactions and empty states.
**Success Criteria:**

- User typing a name or house number in the search bar and pressing Enter sees relevant matching results.
- User searching for a non-existent item sees a clear "No results" visual indicator instead of a blank page.
- User pressing Esc clears the search input and closes the search results.

#### Phase 86: Advanced Search UX

**Requirements:** [NAV-06, NAV-07]
**Description:** Enhance the search experience with keyboard shortcuts and instant zero-click search results.
**Success Criteria:**

- User pressing Cmd/Ctrl+K focuses the search bar from anywhere on the page.
- User typing in the search bar sees top results appear instantly below the bar without pressing Enter.
- User clicking on an instant result navigates immediately to the relevant view.

#### Phase 87: Extended Search Intelligence

**Requirements:** [NAV-08, NAV-09]
**Description:** Implement complex search capabilities including typo tolerance for Arabic OCR variations and full-text document search.
**Success Criteria:**

- User searching with a minor typo in an Arabic name still sees the correct tenant in results.
- User searching for a specific term found only inside a PDF document sees the document in results.

<details>
<summary>✅ v8.0 Web-Based File Viewer (Phases 81-83) — SHIPPED 2026-09-02</summary>

See [.planning/milestones/v8.0-ROADMAP.md](milestones/v8.0-ROADMAP.md) for full phase details.

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 84. Core Navigation & Routing | v9.0 | 1/1 | Complete    | 2026-09-02 |
| 85. Global Search & Empty States | v9.0 | 1/1 | Complete    | 2026-09-02 |
| 86. Advanced Search UX | v9.0 | 1/1 | Complete    | 2026-09-02 |
| 87. Extended Search Intelligence | v9.0 | 0/1 | Pending | |
| 81. Frontend Test Suite Foundation | v8.0 | 1/1 | Complete | 2026-09-02 |
| 82. Python REST API endpoints | v8.0 | 1/1 | Complete | 2026-09-02 |
| 83. Read-only Web GUI | v8.0 | 1/1 | Complete | 2026-09-02 |
