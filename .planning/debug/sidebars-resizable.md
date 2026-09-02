---
status: resolved
trigger: "the sidebars are not resizable"
updated: 2026-09-02
---

# Debug Session: sidebars-resizable

## Symptoms
- **Expected behavior**: The user should be able to drag the edges of both sidebars (the Vaults tree and the Document list) to adjust their widths dynamically.
- **Actual behavior**: The first sidebar used standard CSS `resize: horizontal`, which often only provides a tiny drag handle in the bottom-right corner and wasn't accessible or intuitive. The second sidebar (Document List) was hardcoded to `w-1/3` and completely unresizable.
- **Error messages**: None.
- **Timeline**: Always.
- **Reproduction**: Try dragging the edges of the sidebars.

## Resolution
- **root_cause**: Lack of dedicated resizer DOM elements and JavaScript dragging logic for responsive layout changes.
- **fix**: 
  - Added dedicated `div` splitters (`w-1.5`) between the panels in `src/api/static/index.html`.
  - Implemented vanilla JavaScript drag-and-drop event listeners (`mousedown`, `mousemove`, `mouseup`) that calculate cursor deltas and update the panel widths dynamically.
  - Removed standard CSS `resize: horizontal` to use the more robust JS splitter.
  - Ensured limits were placed on dragging (e.g. max `60%`, min `200px`) to prevent UI breaking.
- **verification**: Tests passed and manual verification confirmed the fix.
- **files_changed**:
  - `src/api/static/index.html`
