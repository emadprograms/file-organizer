# Phase 5: Arabic Formatting & LLM Accuracy

## Domain Boundary
This phase focuses on structural formatting and AI output reliability: fixing Arabic string mutilation, ensuring Windows File Explorer sorting via zero-padded directories, optimizing when those directories are created, and enforcing LLM retry logic rather than swallowing exceptions. We are focusing *how* to implement these fixes without adding new capabilities.

## Canonical Refs
- `.planning/ROADMAP.md` (Phase 5 goal and requirements)

## Decisions

### 'Al-' Prefix Handling
- **Decision**: Disable stripping entirely.
- **Details**: Remove the `.replace("ال", "")` logic completely. We will rely strictly on exact matches and let the AI output normalized names natively.

### Zero-Padded Folder Format
- **Decision**: Use underscore separator: `01_CategoryName`.
- **Details**: Folders will be formatted exactly like `01_عقود السكن` to ensure correct lexicographical sorting in Windows File Explorer.

### Dynamic Folder Generation
- **Decision**: Just-in-time (Write-time) creation.
- **Details**: Only create the category folder right before a PDF is actually saved into it. This keeps output folders maximally clean by completely eliminating empty directories.

### Retry Limits & Fallback
- **Decision**: Fallback to UNKNOWN folder.
- **Details**: When an LLM exception occurs or a resident name is missing for `other_letters`, we trigger retries. If the max retries are exhausted, move the document to an UNKNOWN fallback folder, log the failure, and continue processing instead of halting the entire pipeline.
