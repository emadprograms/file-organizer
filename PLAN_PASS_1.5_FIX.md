# Detailed Implementation Plan: Pass 1.5 Refactor (Dates, Aliases, Visibility)

## 🎯 Objective
Complete overhaul of Pass 1.5 in `src/pipeline.py` to correctly handle birth-date outliers, sparse-date documents (photos), and out-of-order alias mapping, while adding full audit visibility.

---

## 🛠 Step-by-Step Instructions for Implementation

### Part 1: `_interpolate_dates` Refactor (Date Cleaning)
**Goal:** Use LLM intelligence to identify chronological outliers and fill gaps algorithmically.

1.  **Remove Legacy Check:** 
    - Locate the loop that checks `if dt.year < 1970 or dt.year > datetime.now().year`. 
    - **DELETE** this logic entirely.

2.  **Implement LLM-Based Outlier Detection (New Step):**
    - Collect all `(page_index, date)` pairs where `date != "NONE"`.
    - Call `self.client.detect_date_outliers(date_pairs)`.
    - For every page index returned by the LLM as an outlier:
        - Set `raw_pages[idx][1].date = "NONE"`.
        - **LOG:** `print(f"[Pass 1.5 Date] Page {idx}: {old_date} -> NONE (LLM detected as outlier)")`

3.  **Perform Global Interpolation (Second Loop):**
    - Maintain the existing logic that fills `"NONE"` values.
    - **Edge Case Handling:**
        - If Page 1 is `"NONE"`, it must take the date from the first valid page found moving forward.
        - If the last page is `"NONE"`, it must take the date from the last valid page found moving backward.
    - **LOG:** `print(f"[Pass 1.5 Date] Page {i}: NONE -> {interpolated_date} (Interpolated from Page {anchor_index})")`

---

### Part 2: `_map_aliases` Refactor (Two-Pass Mapping)
**Goal:** Ensure aliases are mapped regardless of where the `PERSONAL_DETAILS` page appears.

1.  **Pass A: Primary Tenant Identification:**
    - Create a loop that scans **all** `raw_pages`.
    - **Rule 1 (Anchors):** If a page category is in `ANCHOR_CATEGORIES` (Basic Details, Key Handover, Contract), the first valid resident name found is the `active_primary_tenant`.
    - **Rule 2 (Frequency):** If no anchor is found, use a `Counter` to find the name that appears most frequently (> 3 times) across the whole document.
    - Store the final `active_primary_tenant` in a variable.

2.  **Pass B: Alias Mapping:**
    - Create a **second, separate loop** through `raw_pages`.
    - If `page.category == Category.PERSONAL_DETAILS` AND `active_primary_tenant != "UNKNOWN"`:
        - Iterate through all `residents` on that page.
        - If a resident is NOT the `active_primary_tenant`, add them to `canonical_mapping` as an alias: `canonical_mapping[resident] = active_primary_tenant`.
        - **LOG:** `print(f"[Pass 1.5 Alias] Page {i}: Mapping '{resident}' -> '{active_primary_tenant}' (Category: PERSONAL_DETAILS)")`

---

### Part 3: Visibility & Audit Logs
**Goal:** Make Pass 1.5 a transparent process.

- Ensure every change in `_interpolate_dates` and `_map_aliases` uses the `print` format specified above.
- Add a starting and ending log for the whole process:
    - `print(f"--- Starting Pass 1.5 Audit for {pdf_path} ---")`
    - `print(f"--- Pass 1.5 Completed for {pdf_path} ---")`

---

## 🧪 Verification Checklist for Executor

### Test Case 1: The "Birth Date" Photo Mix
- **Setup:** Page 1 (`1986-01-01`), Page 2-5 (`NONE`), Page 6 (`2011-01-01`), Page 7 (`2011-01-02`).
- **Pass:** LLM identifies Page 1 as an outlier $ightarrow$ set to `NONE` $ightarrow$ interpolated to `2011-01-01`.

### Test Case 2: The "Out-of-Order" Resident
- **Setup:** Page 1 (`PERSONAL_DETAILS`: "John Doe", "Jane Doe"), Page 10 (`CONTRACT`: "John Doe").
- **Pass:** Pass A identifies "John Doe" as Primary. Pass B maps "Jane Doe" $ightarrow$ "John Doe".

### Test Case 3: The "Chronological" File
- **Setup:** Page 1 (`2020`), Page 5 (`2021`), Page 10 (`2022`).
- **Pass:** LLM identifies no outliers because they shift naturally.

---

## ⚠️ Final Warning for Executor
- **DO NOT** use a fixed year like 1970.
- **DO NOT** map aliases in the same loop you identify the tenant.
- **SURELY** use `self.client` for the outlier detection to ensure Cloud $ightarrow$ Local fallback and rate limiting.
