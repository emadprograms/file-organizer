# Vault Architecture & Bidirectional Reconciliation — Pitfalls Analysis

## 1. Windows `.lnk` File Generation & Arabic Support
**Warning Signs:**
- Shortcuts fail to open or point to malformed paths (e.g., `C:\?`) instead of the vault.
- Runtime errors related to `MAX_PATH` (260 characters) when creating deeply nested tenant folders.
- Libraries (like `pylnk3` or `winshell`) throwing `UnicodeEncodeError` or corrupting Arabic filenames in the `.lnk` target block.

**Prevention Strategy:**
- **Encoding:** Explicitly use Windows Unicode APIs (via `pywin32` / `win32com.client`) rather than legacy command-line tools or byte-manipulation libraries that might default to ANSI/CP1252.
- **Path Length Limits:** Prepend absolute paths with `\\?\` to bypass the 260-character `MAX_PATH` limitation on Windows, which is crucial for deeply categorized Arabic folder names.
- **Network Drives:** Avoid using mapped drive letters if the destination might be on a NAS. Use UNC paths (`\\server\share\`) in shortcut targets to prevent broken links if the drive map drops.

**Which phase should address it:** Core Utility Phase (`utils/shortcut_manager.py` or equivalent).

## 2. Vault Storage Architecture
**Warning Signs:**
- Two distinct PDFs generating the same vault ID (collisions) and overwriting each other.
- Unreferenced PDFs accumulating in the vault (orphaned files) if the pipeline crashes after file copy but before state update.
- Identical files being stored multiple times instead of being deduplicated.

**Prevention Strategy:**
- **ID Collisions:** Use a robust hashing mechanism (e.g., SHA-256 of file contents) combined with a UUIDv4 suffix to guarantee uniqueness, rather than relying solely on incremental counters or partial hashes.
- **Orphaned Files:** Implement a two-phase commit: write the file to the vault with a `.tmp` extension, update `state.json`, then atomically rename the file to remove `.tmp`. A startup routine can safely purge stale `.tmp` files.
- **Folder Limits:** Avoid storing tens of thousands of PDFs in a single flat directory. Implement a partitioned structure (e.g., `vault/e4/f1/e4f1...pdf`) using the first two characters of the hash.

**Which phase should address it:** Vault Storage Engine Implementation Phase.

## 3. Bidirectional Sync & Reconciliation
**Warning Signs:**
- Infinite sync loops where the system constantly re-writes a shortcut that the user just attempted to move.
- User intent (a folder move) being incorrectly interpreted as a "delete from old, create in new" operation, losing the user's manual categorization.
- State reverting to an old LLM-categorized version when the app restarts, ignoring manual dragging.

**Prevention Strategy:**
- **Detecting Moves vs. Deletes:** Track the Vault ID embedded within the shortcut. If a shortcut pointing to Vault ID `X` disappears from Folder A and appears in Folder B, it's a move. If it disappears entirely, it is a deletion.
- **Conflict Resolution:** Establish a "user-wins" pinning strategy. `state.json` must distinguish between `llm_path` and `user_pinned_path`.
- **Race Conditions:** Use file system events (e.g., via `watchdog`) with debouncing. Do not trigger a full reconciliation on every single instantaneous file event; wait for a short idle timeout (e.g., 2 seconds) to ensure the user has finished their drag-and-drop operation.

**Which phase should address it:** FS-UI / Watcher Adaptation Phase (Reconciliation module).

## 4. `state.json` Corruption Risks
**Warning Signs:**
- The `state.json` ends up as a 0-byte file after a power loss or unexpected crash, bricking the tenant's data.
- Processes lock up or crash when the file watcher and the background pipeline attempt to write to `state.json` concurrently.

**Prevention Strategy:**
- **Crash During Write:** Use the "atomic write" pattern. Write the new state to `state.json.tmp`, flush the OS buffers (`os.fsync`), and perform an atomic rename over the existing `state.json`.
- **Concurrent Access:** Implement file-based locking (using a library like `filelock`) to serialize reads and writes across background pipeline threads and UI watcher threads.

**Which phase should address it:** State Engine / Context Unification Phase.

## 5. Migration from Direct-Placement to Vault
**Warning Signs:**
- Complete duplication of data on disk (the old physical files remain alongside new vault versions).
- Loss of custom organization (e.g., if a user manually moved a physical PDF in the old system, and the migration resets it to the original LLM categorization).

**Prevention Strategy:**
- **Stateful Migration:** The migration script must scan the *current* folder structure of the old system. For each physical PDF found:
  1. Hash it, move it to the Vault, and assign its new ID.
  2. Create a `.lnk` in the exact same physical folder where the PDF was just found.
  3. Register this path in the new `state.json` as a user-pinned location, guaranteeing no loss of user modifications.
- **Dry-run Mode:** Build a simulation mode that reports what will happen without touching files, ensuring safe testing on existing houses.

**Which phase should address it:** Dedicated Migration Script Phase (typically the final phase before rollout).

## 6. Arabic Filename Handling on Windows (NTFS)
**Warning Signs:**
- Standard folder creation throws `FileNotFoundError` or `OSError` due to path mangling or invalid character interpretation.
- BiDi (Bidirectional) text rendering issues in Windows Explorer where Right-To-Left overrides make paths visually confusing or functionally broken in string concatenation.

**Prevention Strategy:**
- **Native Types:** Use Python 3's native `pathlib` consistently for all path manipulations instead of raw string concatenation. `Path / 'ArabicName'` guarantees correct slash direction.
- **Normalization:** Normalize Arabic unicode strings (e.g., using `unicodedata.normalize('NFC', text)`) before using them in file paths to prevent issues with decomposed characters in NTFS.

**Which phase should address it:** Core Utility / Pipeline Phase.
