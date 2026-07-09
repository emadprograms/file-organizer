# Phase 11 Context: Conditional LLM Folder Routing and Folder Renaming

## Objective
Implement strict 1:1 English-to-Arabic folder mapping and a conditional LLM routing system that reduces hallucinations by constraining available choices based on broad document categories.

## Background
- Documents are initially classified into one of 7 broad categories: Forms, Letters, ID, Contract, Utility Bills, Pictures, Others.
- 13 specific folders (mapped to Arabic names) exist as the final destination.
- Currently, the LLM may see all folders, leading to confusion or incorrect routing.

## Requirements
- **Direct Python Routing:** ID, Contract, Utility Bills, and Pictures must bypass the LLM and be routed directly by Python to their singular respective folders.
- **Constrained LLM Prompting:** Forms and Letters must only present their specific valid sub-folders to the LLM.
- **Double-Check for Others:** If 'Others', prompt LLM with all 13 folders. If it selects 'Miscellaneous Letters', accept. If it selects another folder, retry to confirm. If it fails to confirm the same folder twice, default to 'Miscellaneous Letters'.
- **System-Wide Renaming:** Update folder references across the application to match the Arabic folder names exactly.
- **Tests:** Update and add tests to verify dynamic constrained routing schema and fallback logic.

## Status
Ready for discussion.
