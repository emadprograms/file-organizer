---
title: "Implement reconcile --tenants mode in main.py"
status: "complete"
---

# Summary

**Implemented `reconcile --tenants` CLI subcommand:**
- Added the `reconcile` command to the main parser with arguments `--tenants`, `--dry-run`, and `<target_dir>`.
- Implemented `run_reconcile_mode` in `src/main.py`.
- Correctly bypasses LLM inference and directly updates `canonical_tenant` in `_1_cleaned.json` and `primary_tenant` in `_2_grouped.json`.
- Restructures the `target_folder` and `output_file` paths in `_3_routed_and_finalized.json` efficiently via string manipulation rather than re-running the deterministic PDF splitting logic, preserving existing topic folders and unique file suffixes.
- Renames physical PDFs on disk, auto-creating new directories as required, and recursively cleans up resulting empty directories.
- Tested and verified execution logic in a dry-run scenario.
