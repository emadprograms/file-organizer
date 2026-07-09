# Security Audit: Phase 11 - Conditional LLM Folder Routing and Folder Renaming

## Overview
- **Phase:** 11
- **Status:** VERIFIED
- **Date:** 2026-07-09
- **Audit Focus:** LLM Hallucination Prevention, Routing Precision, and Fallback Safety.

## Threat Model & Mitigations

### 1. LLM Hallucinations (Invalid Folder Names)
- **Threat:** The LLM may generate a folder name that does not exist in the definitive Arabic mapping, causing filesystem errors or pipeline crashes.
- **Mitigation:** 
    - **Strict Type Enforcement:** The `RoutingResponse` Pydantic model utilizes a `field_validator` that checks the `selected_folder` against an `allowed_folders` list passed via `validation_context`.
    - **Retry Loop with Feedback:** If validation fails, the router captures the rejected value and provides explicit feedback to the LLM in a retry attempt (up to 3 attempts).
- **Verification:** Verified in `src/processing/routing/router.py` within the `RoutingResponse.validate_folder` method and the `route_document` retry loop.

### 2. Routing Imprecision (Wrong Category Type)
- **Threat:** The LLM might assign a "Letter" to a "Form" folder (or vice versa) if the full list of folders is provided, increasing the noise in target directories.
- **Mitigation:**
    - **Constrained Prompting:** The router filters `allowed_folders` based on the document's category (`FORM_CATEGORIES` or `LETTER_CATEGORIES`), ensuring the LLM only sees plausible options for that document type.
- **Verification:** Verified in `src/processing/routing/router.py` where `allowed_folders` is dynamically assigned based on the `category` of the `DocumentGroup`.

### 3. "Miscellaneous" Dumping (Over-reliance on Others)
- **Threat:** LLMs often default to a "Miscellaneous" or "Others" folder when uncertain, leading to poor organization.
- **Mitigation:**
    - **Double-Check Flow:** Any document categorized as `OTHER_LETTERS` or hitting the "None of the above" escape hatch is routed through `double_check_others`.
    - **Two-Step Verification:** The double-check involves an initial broad pick followed by a targeted confirmation call to verify if the selection is truly better than the "Miscellaneous" default.
- **Verification:** Verified in `src/processing/routing/router.py` implementation of `double_check_others`.

### 4. Double-Check Hallucinations
- **Threat:** The second confirmation call in the double-check flow might itself hallucinate an invalid folder.
- **Mitigation:**
    - **Safe Fallback:** If the confirmation call returns a value other than the `initial_pick` or `رسائل متنوعة`, or if the call fails, the system automatically falls back to the safest default: `رسائل متنوعة`.
- **Verification:** Verified in `src/processing/routing/router.py` within the final pick logic of `double_check_others`.

## Conclusion
The implementation of Phase 11's routing system is robust. It successfully moves from a "trust-but-verify" approach to a "constrain-and-enforce" architecture, significantly reducing the risk of LLM hallucinations and improving the precision of document organization.
