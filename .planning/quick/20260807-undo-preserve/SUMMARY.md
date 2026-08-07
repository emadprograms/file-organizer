---
status: complete
---
# Summary: Preserve OCR Dump and Tenants YAML in Undo Command

- Modified `src/pipeline/undo.py` to preserve `.raw_dump.json`, `_report*.json`, and `*tenant*.yaml` files.
- The files are moved to a temporary directory before the wipe out, and then placed back inside the `.source_files/` directory.
- This allows a user to "undo" without losing the expensive LLM OCR dump or the `tenants.yaml` definitions.
