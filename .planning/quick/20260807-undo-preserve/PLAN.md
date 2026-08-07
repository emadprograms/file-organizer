# Quick Task: Preserve OCR Dump and Tenants YAML in Undo Command

## Description
Update the `python src/main.py undo` command so that it does not wipe out everything indiscriminately. It should preserve the `tenants.yaml` file and the OCR dump (`_report.json` or `.raw_dump.json`) inside the `.source_files/` directory, while still deleting the `vault/`, `_state.json`, timeline shortcuts, and tenant folders.

## Steps
1. In `src/pipeline/undo.py`, before wiping the `target_dir`, identify and copy the `tenants.yaml`, `_report.json`, and `.raw_dump.json` files to a temporary directory.
2. Wipe the directory as usual (leaving only the reconstructed PDF).
3. Recreate the `.source_files/` directory.
4. Move the preserved files from the temporary directory into `.source_files/`.
5. Update `STATE.md` to reflect the completion of this quick task.
6. Commit the changes.
