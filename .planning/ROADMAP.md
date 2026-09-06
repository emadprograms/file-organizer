# Roadmap: File Organizer

## Milestones

- 🚧 **v10.0 Area Grid Overview & Tenure Visualization** — Phases 88-91 (in progress)
- ✅ **v9.0 Hierarchical Web Dashboard** — Phases 84-87.1 (shipped 2026-09-06)
- ✅ **v8.0 Web-Based File Viewer** — Phases 81-83 (shipped 2026-09-02)

## Phases

### 🚧 v10.0 Area Grid Overview & Tenure Visualization

#### Phase 88: View Mode Switcher & Area Grid Layout
**Requirements:** [GRID-01, GRID-02, GRID-03]
**Description:** Build the dual-view toggle (Tree View vs Grid View), adapt the sidebar to show only areas in Grid View mode, and create the responsive house card grid container.
**Success Criteria:**
- User can toggle between Tree View and Grid View from the UI.
- In Grid View mode, the sidebar displays only the list of areas.
- Clicking an area renders the house grid container in the main view.

#### Phase 89: House Card Metrics & Tenure Color-Coding
**Requirements:** [GRID-04, GRID-05, GRID-06]
**Description:** Extract and display house metadata: current active tenant, residency start year/duration, tenure color styling (Green < 5 yrs, Yellow 5-10 yrs, Red > 10 yrs), total doc counts, and category breakdown.
**Success Criteria:**
- Each house card shows house name, active tenant, and tenure duration.
- Visual colors reflect tenure length accurately (green, yellow, red).
- Document counts and category badges are clearly visible on each card.

#### Phase 90: Drill-down Navigation & Static Parity
**Requirements:** [GRID-07, GRID-08, GRID-09]
**Description:** Enable clicking house cards to navigate into detailed category/timeline views with breadcrumb navigation to return to the grid, and ensure static IIS export parity.
**Success Criteria:**
- Clicking a card opens the Categories/Timeline panel for that house.
- A "Back to Area Grid" breadcrumb returns smoothly to the grid overview.
- Static export pipeline generates complete data for IIS offline viewing.

#### Phase 91: Playwright E2E Test Suite & Milestone Verification
**Requirements:** [GRID-10]
**Description:** Create end-to-end Playwright tests verifying all grid interactions, color classifications, data rendering, and navigation flows.
**Success Criteria:**
- Playwright tests simulate view toggling, card rendering, and drill-downs.
- All backend and frontend tests pass 100%.

<details>
<summary>✅ v9.0 Hierarchical Web Dashboard (Phases 84-87.1) — SHIPPED 2026-09-06</summary>

See [.planning/milestones/v9.0-ROADMAP.md](milestones/v9.0-ROADMAP.md) for full phase details.

</details>

<details>
<summary>✅ v8.0 Web-Based File Viewer (Phases 81-83) — SHIPPED 2026-09-02</summary>

See [.planning/milestones/v8.0-ROADMAP.md](milestones/v8.0-ROADMAP.md) for full phase details.

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 88. View Mode Switcher & Area Grid Layout | v10.0 | 0/1 | In Progress | - |
| 89. House Card Metrics & Tenure Color-Coding | v10.0 | 0/1 | Pending | - |
| 90. Drill-down Navigation & Static Parity | v10.0 | 0/1 | Pending | - |
| 91. Playwright E2E Test Suite & Milestone Verification | v10.0 | 0/1 | Pending | - |
