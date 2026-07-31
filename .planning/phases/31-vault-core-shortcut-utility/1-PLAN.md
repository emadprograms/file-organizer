---
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - src/vault/__init__.py
  - src/vault/core.py
  - src/vault/shortcut.py
  - tests/test_vault.py
autonomous: true
---

# Phase 31: Vault Core & Shortcut Utility

## Goal
Implement the core vault storage mechanism and Windows shortcut generation utility to safely store documents and create lightweight shortcuts for user organization.

## Requirements
- VAULT-01, VAULT-02, VAULT-03, VAULT-04, VAULT-05
- LNK-01, LNK-02, LNK-03, LNK-04

<threat_model>
ASVS Level: Level 1
Blocking Threshold: high
Potential Threats:
- Path traversal when constructing absolute paths for shortcut targets or storing PDFs.
- Shortcut hijacking if the generated `.lnk` files point to unintended locations.
Mitigations:
- Ensure UUID generation is safe and resulting filenames (`doc_{UUID}.pdf`) contain no user-supplied input.
- Validate that the target path used in `.lnk` points exactly to a `.pdf` file within the `.source_files/vault/` directory.
</threat_model>

## Tasks

<task>
<action>
Add `pylnk3` to `requirements.txt` to support Windows shortcut generation. Append `pylnk3` to the end of the file.
</action>
<read_first>
- requirements.txt
</read_first>
<acceptance_criteria>
`requirements.txt` contains `pylnk3`
</acceptance_criteria>
</task>

<task>
<action>
Create `src/vault/__init__.py` (empty or basic imports).
Create `src/vault/core.py` and implement `Vault` class.
Implement `store_pdf(source_pdf: Path, house_root: Path) -> str` method.
The method must:
1. Ensure the hidden directory `house_root / ".source_files" / "vault"` exists.
2. Generate a unique UUID for the document using `uuid.uuid4()`.
3. Use a two-phase commit: copy `source_pdf` to a temporary file `.tmp` in the vault, then rename it (using `os.replace`) to `doc_{UUID}.pdf`.
4. Return the new UUID string.
Once stored, files must never be moved or renamed by the system.
</action>
<read_first>
- src/utils/fs.py
</read_first>
<acceptance_criteria>
`src/vault/core.py` contains `class Vault` with `store_pdf` method that uses `.tmp` extension and `os.replace`.
</acceptance_criteria>
</task>

<task>
<action>
Create `src/vault/shortcut.py` and implement `ShortcutManager` class.
Implement `create_shortcut(target_pdf: Path, category_dir: Path, date_str: str, title: str) -> Path`.
The method must:
1. Ensure `category_dir` exists (e.g. `10_صيانة/`).
2. Construct the target absolute path prefixed with `\\?\` for long Arabic path support on Windows (e.g., `\\\\?\\C:\\...`).
3. Construct the shortcut name as `{date_str} - {title}.lnk`.
4. Use `pylnk3.create()` (or the equivalent pylnk3 API) to generate the `.lnk` file in `category_dir` pointing to the prefixed absolute target path.
5. Return the path to the created shortcut.
</action>
<read_first>
- src/vault/core.py
</read_first>
<acceptance_criteria>
`src/vault/shortcut.py` contains `create_shortcut` function/method that constructs a path starting with `\\\\?\\` and calls `pylnk3`.
</acceptance_criteria>
</task>

<task>
<action>
Create `tests/test_vault.py` with pytest test cases covering `Vault` and `ShortcutManager`.
Write tests to verify:
1. `Vault.store_pdf` creates `.source_files/vault/doc_{UUID}.pdf` using a mocked two-phase commit, avoiding orphan files.
2. `ShortcutManager.create_shortcut` generates a `.lnk` file with the correct naming convention and `\\?\` path prefix using a mocked `pylnk3`.
</action>
<read_first>
- src/vault/core.py
- src/vault/shortcut.py
</read_first>
<acceptance_criteria>
`tests/test_vault.py` exists and `pytest tests/test_vault.py` exits 0.
</acceptance_criteria>
</task>

## Verification
- Vault storage properly generates UUIDs and handles files atomically.
- Shortcut generation constructs correct `\\?\` prefixed target paths and generates `.lnk` files.
- `requirements.txt` contains `pylnk3`.

## must_haves

```yaml
truths:
  - ".source_files/vault directory is created per house"
  - "Each document receives a unique UUID"
  - "Physical PDFs are stored as doc_{UUID}.pdf"
  - "Vault uses two-phase commit for atomic writes"
  - "System generates .lnk files using pylnk3"
  - "Shortcuts are named with date and document title"
  - "Shortcut targets use absolute paths with \\\\?\\ prefix"
prohibitions:
  - statement: "Vault PDFs must never be moved or renamed after creation"
    status: "resolved"
    verification: "Code inspection confirms store_pdf only writes new files and never updates/moves existing doc_{UUID}.pdf files."
```

## Artifacts this phase produces
- **File**: `src/vault/__init__.py`
- **File**: `src/vault/core.py`
- **File**: `src/vault/shortcut.py`
- **File**: `tests/test_vault.py`
- **Class**: `Vault` in `src/vault/core.py`
- **Method**: `Vault.store_pdf`
- **Class**: `ShortcutManager` in `src/vault/shortcut.py`
- **Method**: `ShortcutManager.create_shortcut`
- **Dependency**: `pylnk3` added to `requirements.txt`
