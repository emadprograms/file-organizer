---
status: in_progress
quick_id: 260917-bk5
slug: make-a-timestamped-copy-of-the-current-o
date: 2026-09-17
description: Make a timestamped copy of the current organize.db and the areas_v11 folder
---

# Plan: Timestamped Backup of organize.db and areas_v11 Folder

## User Intent
The user requested a timestamped copy of the current `organize.db` (the active SQLite database `D:\areas_v11\organizer.db` and repository database) and the `areas_v11` folder (`D:\areas_v11`).

## Key Tasks
1. **SQLite Database Online Backup (`organizer.db`):**
   - Perform an atomic, consistent online backup of `D:\areas_v11\organizer.db` using SQLite's online backup API via Python (`sqlite3.backup`).
   - Create a timestamped copy at `D:\organizer_{timestamp}.db`.
   - Create an internal backup copy at `D:\areas_v11\organizer.db.bak_{timestamp}`.
   - Run `PRAGMA integrity_check;` on the backup to verify 100% integrity.
   - Also create a timestamped copy of the repo root `organizer.db` (`organizer_local_repo_{timestamp}.db`).

2. **Directory Mirror Copy (`areas_v11`):**
   - Use multi-threaded Windows `robocopy` (`/S /E /DCOPY:DA /COPY:DAT /MT:16 /R:3 /W:5`) to create a full mirror at `D:\areas_v11_{timestamp}`.
   - Copy the verified online database backup into `D:\areas_v11_{timestamp}\organizer.db` to guarantee clean state regardless of active WAL mode.
   - Verify file count and total size parity between source and destination.

3. **Record & Update State:**
   - Create `SUMMARY.md` in `.planning/quick/260917-bk5-make-a-timestamped-copy-of-the-current-o/`.
   - Update `.planning/STATE.md` under `### Quick Tasks Completed`.
