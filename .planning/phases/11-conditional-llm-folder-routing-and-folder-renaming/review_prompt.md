Please review the following plans for Phase 11.
Focus on logic, edge cases (especially the "Others" double check), completeness of the verification plan, and potential risks.

Context:
- 13 specific folders mapped to Arabic names exist as final destinations.
- Direct Python Routing for ID, Contract, Utility Bills, Pictures.
- Constrained LLM Prompting for Forms and Letters.
- Double-Check for Others (retry if doesn't pick Miscellaneous Letters, accept if picks same twice, default to Misc if not).
- System-Wide Renaming to Arabic folder names.

Plan 11-01: Folder Mapping and Direct Routing Infrastructure
Defines Arabic folder mapping. Refactors `route_document` to bypass LLM for ID, Contract, Utility Bills, Pictures.

Plan 11-02: Constrained LLM Routing and "Others" Double-Check
Filters `allowed_folders` based on document category (Forms/Letters). Implement double-check logic for OTHER_LETTERS.

Plan 11-03: System-Wide Integration and Validation
Update hardcoded English folder names to Arabic. Update test suites. E2E validation.
