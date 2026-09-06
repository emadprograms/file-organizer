# Requirements: Milestone v10.0 Area Grid Overview & Tenure Visualization

## Milestone v10.0 Requirements

### Dual View & Navigation
- [x] **GRID-01**: User can toggle between "Tree View" and "Grid View" via an intuitive view switcher control.
- [x] **GRID-02**: In Grid View, the sidebar shows only the Area list (e.g. Safra C, Safra D, Safra Flats) without hierarchical sub-trees.
- [x] **GRID-03**: Selecting an area in Grid View renders a responsive grid of House Cards/Boxes in the main content dashboard.

### House Card Data & Visuals
- [x] **GRID-04**: Each house card displays the house name/id, the current active tenant ("الآن / Present"), and residency start date/tenure.
- [x] **GRID-05**: Each house card has tenure-based color-coding: Green (< 5 years), Yellow (5–10 years), Red (> 10 years).
- [x] **GRID-06**: Each house card displays the total document count and per-category document count breakdown.

### Interactions & Static Parity
- [x] **GRID-07**: Clicking any house card navigates directly into that house's detailed Categories/Timeline view.
- [x] **GRID-08**: A breadcrumb or "Back to Area Grid" button allows instant return to the area card grid.
- [x] **GRID-09**: Both live API mode and static IIS export mode (`tree.json`, static bundle) support all grid view features seamlessly.

### Quality & Verification
- [x] **GRID-10**: End-to-end Playwright tests verify view toggling, card rendering, tenure color badges/borders, document count breakdowns, and drill-down navigation.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GRID-01 | Phase 88 | Complete |
| GRID-02 | Phase 88 | Complete |
| GRID-03 | Phase 88 | Complete |
| GRID-04 | Phase 89 | Complete |
| GRID-05 | Phase 89 | Complete |
| GRID-06 | Phase 89 | Complete |
| GRID-07 | Phase 90 | Complete |
| GRID-08 | Phase 90 | Complete |
| GRID-09 | Phase 90 | Complete |
| GRID-10 | Phase 91 | Complete |
