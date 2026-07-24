---
slug: move-temp-files
date: "2026-07-24"
---

# Move temp files to prevent inbox clutter

- Use OS Temp Directory (`tempfile.gettempdir()`) for `.tmp.pdf` and other ephemeral processing files.
- Move the `.inbox.lock` file to `~/.file-organizer/locks` so it doesn't show up in the watched folder.
- Use `~/.file-organizer/cache` for temporary directories during append mode so they can still be matched up later in finalize.
