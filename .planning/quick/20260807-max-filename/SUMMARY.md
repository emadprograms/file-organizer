---
status: complete
---
# Summary: Enforce max character limit on LLM generated filenames

- Updated `src/core/categories.yaml` to enforce a hard maximum length of 50 characters on fields that are typically used as filenames (`subject` for letters, `brief_summary` for others, and `image_contents` for pictures).
- This explicitly instructs the LLM to write brief titles instead of generating extremely descriptive paragraphs, successfully avoiding the Windows 260 character MAX_PATH limit when creating filesystem shortcuts.
