---
status: complete
---

Executed changes directly. 
- Moved lock file to centralized `~/.file-organizer/locks` 
- Used OS `tempfile` for atomic writes and scratch PDFs
- Used `~/.file-organizer/cache` for cross-process `.tmp_` directorie
