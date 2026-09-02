---
status: investigating
trigger: |
  DATA_START
  the app is working for safra c. I can see the pdfs in the timeline but I don't see anything for safra d in the app. check
  no the app doesn't show any pdfs in the timeline when I click on safra d houses in the sidebar and then click on the name. there is a timeline and categories tab. they are suppose dto show the pdfs. nothing is in there. I see "No documents for this selection" inside timeline.
  DATA_END
---
# Debug Session: Safra D missing PDFs

## Symptoms
- **Expected behavior**: When clicking on Safra D houses in the sidebar and then clicking on the name, the timeline and categories tabs should display the PDFs.
- **Actual behavior**: App doesn't show any PDFs in the timeline or categories tab. Instead, it displays "No documents for this selection" inside the timeline.
- **Error messages**: UI shows "No documents for this selection".
- **Timeline**: N/A
- **Reproduction**: Click on Safra D houses in the sidebar > click on the name > check timeline and categories tabs.

## Current Focus
- hypothesis: The API endpoints for timeline and categories are reading from `grouped_documents` which doesn't contain `vault_id`s in the newer pipeline version used for Safra D, resulting in silent validation failures.
- next_action: implement fix to read from `routed_documents` if it contains `vault_id`s, preserving backward compatibility.