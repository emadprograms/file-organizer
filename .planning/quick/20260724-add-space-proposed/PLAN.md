---
slug: add-space-proposed
date: "2026-07-24"
---

# Add space before 'Proposed' in PDF filename

- Fix `new_pdf_name` in `src/watcher/orchestrator.py` to use `" Proposed.pdf"` instead of `"Proposed.pdf"`.
- Update the checks in `process_inbox` and `finalize` to match the new spaced format (`" Proposed"`).
