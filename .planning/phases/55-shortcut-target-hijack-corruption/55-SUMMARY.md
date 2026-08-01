# Phase 55 Summary & Learnings

## Decisions Made
- Chose to repair hijacked shortcuts immediately after populating `physical_lnk_by_vault` rather than delaying it to the deletion loop. This elegantly prevents both deletion *and* cross-contamination with a single state-correction step.
- Included `shortcuts_repaired` in the reconciliation report payload to provide operational visibility.

## Lessons & Patterns
- **Path Encoding Gotchas**: The `tenant_folder_names` map generates paths containing Left-to-Right Marks (`\u200e`) and date suffixes. When writing E2E tests, it's safer to explicitly match these generated strings rather than assuming purely ASCII paths, to avoid false-positive test failures during the move-folder logic.

## Surprises
- When a shortcut is heavily corrupted or points to a non-PDF file, `read_shortcut_target` could return `None` or an external path. The `try/except` block with `is_relative_to(source_dir.resolve())` gracefully guards against crashes, ensuring we can still fall back to `state.json` for repair.
