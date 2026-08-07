# Quick Task: Enforce max character limit on LLM generated filenames

## Description
To prevent hitting the Windows MAX_PATH limit (260 characters), we need to strictly limit the length of text the LLM generates for fields that eventually become filenames. 

## Steps
1. Update `src/core/categories.yaml` to append "MUST BE MAXIMUM 50 CHARACTERS LONG." to fields that act as filenames (`letters.subject`, `pictures.image_contents`, `others.brief_summary`).
2. Create `SUMMARY.md` marking it complete.
3. Update `STATE.md` Quick Tasks list.
4. Commit the changes.
