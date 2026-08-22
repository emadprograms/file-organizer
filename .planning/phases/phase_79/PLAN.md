# Phase 79: Append/Prepend Mode for Ingest

## Objective
Implement append/prepend functionality natively into the \ingest\ command to handle newly dropped PDFs in an existing house, entirely replacing the deprecated watcher/inbox methodology.

## Design
When \ingest\ is run on a house directory:
1. Scan for raw \*.pdf\ files in the root folder. (Since older PDFs are moved to \.source_files/vault/\, any PDF in the root is newly added).
2. Generate aw_dump.json\ for all discovered root PDFs.
3. Check \state.json\. If \state.json\ exists and is populated, trigger **Prepend Mode**.
4. In Prepend Mode:
   - Calculate \page_shift\ = total number of pages across the newly discovered PDFs.
   - Run the AI pipeline (Cleaning, Fine Categorization, Grouping, Routing) **only** on the new aw_dump.json\ data.
   - Shift existing index references in \state.json\ (\cleaned_pages\, \ine_categorized_pages\, \grouped_documents\, outed_documents.per_page\) by \page_shift\.
   - Prepend the new AI data to the shifted arrays.
   - Save the unified \state.json\.
5. The econcile\ command (already built) will later ingest the raw PDF from the root folder, slice it into the vault, and create the \.lnk\ shortcuts based on the updated \state.json\.

## Steps
1. **Modify \src/ingest/core.py\:**
   - Detect \*.pdf\ files in the target root.
   - If \state.json\ exists, isolate the new aw_dump.json\ paths and run passes on them.
2. **Index Shifting Logic:**
   - Shift \original_index\ in \cleaned_pages\ and \ine_categorized_pages\.
   - Shift \start_page\ and \end_page\ in \grouped_documents\.
   - Shift \page_index\ in outed_documents.per_page\.


**Note**: Sent architectural clarification to user regarding ingest vs reconcile boundaries.