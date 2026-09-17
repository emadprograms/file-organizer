---
status: complete
quick_id: 260917-bk5
slug: make-a-timestamped-copy-of-the-current-o
date: 2026-09-17
description: Make a timestamped copy of the current organize.db and the areas_v11 folder
---

# Quick Task Summary: Timestamped Backup of organize.db and areas_v11 Folder

## Overview
Created a complete, verified, timestamped backup of the active SQLite database (`organizer.db`) and the full directory structure of `D:\areas_v11`.

### Timestamp Used
- **Timestamp ID:** `20260917082207` (Generated: 2026-09-17 08:22:07 AM)

### Generated Backups
1. **Standalone Database Backups:**
   - `D:\organizer_20260917082207.db` (58.14 MB) — Atomic online SQLite backup of `D:\areas_v11\organizer.db`, verified with `PRAGMA integrity_check;` (`ok`).
   - `D:\areas_v11\organizer.db.bak_20260917082207` (58.14 MB) — In-place safety backup inside `areas_v11`.
   - `D:\organizer_repo_20260917082207.db` (0.08 MB) — Backup of root repository database `organizer.db`.

2. **Full Directory Mirror (`areas_v11`):**
   - Destination: `D:\areas_v11_20260917082207`
   - Total Size: ~18.10 GB across 20,517 files and 764 directories.
   - Synchronized via multi-threaded `robocopy` (`/MT:16 /S /E /DCOPY:DA /COPY:DAT /R:3 /W:5`).
   - Contains clean, verified `organizer.db` with WAL/SHM safely checkpointed.

### Size Analysis: Why areas_v11 is ~18 GB (Double 9 GB)
Analysis of the folder breakdown confirmed that `areas_v11` contains two parallel representations of the document collection:
1. **Raw Scanned Batches (`batches/`):** 8.92 GB across 253 multi-page master PDF files (one per house).
2. **Extracted Documents (`vault/`):** 8.95 GB across 20,154 individual categorized PDF files extracted from the batches for active viewing, categorization, and page editing.
3. **Databases and Other Files:** 0.22 GB (including active `organizer.db` and database backups).
Together, `batches` (~8.9 GB) + `vault` (~8.9 GB) = ~18.1 GB total. No accidental nested folder copies or rogue duplicates exist.
