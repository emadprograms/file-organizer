# Phase 49: 1-to-Many Shortcut Mapping - Plan

## Context Reference
This plan implements the requirements outlined in REQ-01 for Phase 49, as detailed in `49-CONTEXT.md`.

## Goal
Update `state.json` to handle 1 vault ID mapping to multiple physical shortcuts. This decoupling ensures physical page counts remain accurate regardless of shortcut count, and Timeline View generates accurately without duplicating pages.

## Step 1: State Migration and Schema Updates
1. **Target**: `src/core/state.py` (or where the `grouped_documents` schema/dict is defined and loaded).
2. **Action**: 
   - During the state loading phase (`State.load` or reconciliation initialization), scan through all `grouped_documents`.
   - If a document group dictionary has the `"shortcut_name"` key, remove it and create a new `"shortcuts"` key mapped to a list containing that original string: `["old_shortcut_name"]`.
   - If it doesn't have `"shortcut_name"`, ensure `"shortcuts"` is initialized as an empty list (or set).
3. **Internal Data Structure**: Use a Python `set` internally during runtime processing to prevent duplicate shortcut tracking.

## Step 2: Reconciliation Engine Updates
1. **Target**: `src/reconcile/core.py`
2. **Action**:
   - Update the shortcut discovery logic. Instead of mapping one physical shortcut per vault ID and treating the rest as copies to be "adopted" (which creates new vault IDs), map multiple physical shortcuts pointing to the same `vault_id` into the `"shortcuts"` list of that single document group.
   - For orphan/deletion detection, a vault document should only be considered "orphaned" or ready for deletion if its `"shortcuts"` list becomes completely empty. If one shortcut is deleted but others remain, just remove that deleted shortcut from the `"shortcuts"` list.

## Step 3: Timeline View Generation
1. **Target**: `src/reports/timeline.py` (or the equivalent module handling the timeline view generation).
2. **Action**:
   - Iterate over `grouped_documents` (by `vault_id`) rather than iterating over individual shortcuts. This naturally prevents duplication on the timeline.
   - **Location Tag**: Use the "primary" or "first discovered" shortcut path as its primary location tag.
   - If `len(shortcuts) > 1`, add a subtle indicator to the location tag, such as `(+ 1 other location)` or `(+ X other locations)`.
   - **Sorting**: Ensure sorting relies on the underlying vault file's metadata and date, so the number of shortcuts does not affect ordering.
   - **Canonical Name**: Use the underlying vault filename as the canonical name in the timeline to avoid naming conflicts if shortcuts are named differently.

## Step 4: Verification Engine Updates
1. **Target**: `src/core/verification.py`
2. **Action**:
   - Update validation checks to expect the `"shortcuts"` list instead of `"shortcut_name"`.
   - Ensure the physical page count audit explicitly counts pages from the vault PDFs without multiplying them by the number of shortcuts.

## Step 5: Testing
1. **Target**: Test suite (`tests/` directory).
2. **Action**:
   - Add a test for auto-migrating `"shortcut_name"` to `"shortcuts"`.
   - Add a test verifying that adding a duplicate shortcut to the same vault ID correctly updates the `"shortcuts"` list without inflating the `state.json` page count metadata.
   - Add a test verifying the Timeline View does not duplicate entries when a vault ID has multiple shortcuts.
