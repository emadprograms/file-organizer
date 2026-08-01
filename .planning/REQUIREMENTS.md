# Requirements: v5.2 Deep Architecture Integrity & Verification

## 1. Core Module Integration (REQ-01)
- The verification logic MUST be implemented as a core module in `src/core/verification.py` (or similar).
- It MUST NOT be a standalone script in `scripts/`.
- It MUST be accessible via the `main.py` CLI (e.g., `file-organizer verify "Safra C" --house 508`).

## 2. Vault & Shortcut Resolution (REQ-02)
- MUST identify all `.lnk` files in the house's categorized structure and `[Timeline View]`.
- MUST extract the binary target path from each `.lnk` file using `pylnk3`.
- MUST verify that the target path physically exists within the house's `.source_files/vault/` directory.
- MUST flag any broken shortcuts or shortcuts pointing outside the vault.

## 3. Orphan & Manifest Consistency (REQ-03)
- MUST scan the `.source_files/vault/` directory for any PDFs that are NOT referenced by any active shortcut.
- MUST verify that the physical shortcut layout matches the `state.json` manifest 1-to-1 (e.g., all `output_file` paths in the manifest exist as `.lnk` files on disk).

## 4. Tenant & Legacy Artifact Rules (REQ-04)
- MUST enforce that tenant folders exactly match the allowed names in `tenants.yaml`.
- MUST ensure no legacy JSON files (e.g., `_cleaned.json`, `_grouped.json`, `_routed.json`) exist in the `.source_files/` directory.
- MUST ensure no physical `.pdf` files exist in the categorized folders (only `.lnk` files).

## 5. Comprehensive Testing (REQ-05)
- MUST include extensive `pytest` coverage in the `tests/` directory.
- Tests MUST simulate healthy migrated houses, broken links, orphan files, malformed states, and legacy artifact presence.
- The verification tool itself MUST be highly reliable and strictly tested.
