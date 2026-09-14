---
status: resolved
trigger: "add arabic support for house numbers if I write 500 in arabic. search doesn't register it as a house number. fix this."
created: 2026-09-14
updated: 2026-09-14
---

## Root Cause Analysis
1. **Arabic-Indic Numerals Mismatch**:
   - House numbers in the SQLite database are stored in ASCII Latin digits (`500`, `552A`, `616`, `SAF F 2450_1`).
   - The search pipeline previously did not normalize Arabic-Indic digits (`٠١٢٣٤٥٦٧٨٩`) or Eastern Arabic-Indic / Persian digits (`۰۱۲۳۴۵۶۷۸۹`). Searching `٥٠٠` sent `LOWER(h.id) LIKE '%٥٠٠%'` to SQLite, which never matched `500`.
2. **House Prefix Words**:
   - Queries with prefixes like `بيت 500`, `بيت ٥٠٠`, `منزل 500`, `منزل ٥٠٠`, `شقة 2450_1`, or `house 500` failed to match house IDs because the full string including the prefix was compared against `h.id`.
3. **Alphanumeric Letter Suffixes**:
   - Houses with letter suffixes (e.g. `552A`) are often typed by Arabic users as `٥٥٢أ` or `552أ`. Without letter mapping (`أ` $\leftrightarrow$ `A`, `ب` $\leftrightarrow$ `B`, `د` $\leftrightarrow$ `D`), these failed to resolve to the corresponding house.

## Solution
1. **`TextUtils.cs`**:
   - Added `NormalizeArabicDigits(string? text)` converting both `٠-٩` and `۰-۹` to standard `0-9`.
   - Added `ToArabicDigits(string? text)` converting `0-9` to `٠-٩`.
   - Added `ExtractHouseNumber(string? query)`:
     * Splits hyphenated house strings (`houseId.Split(" - ")[0]`).
     * Normalizes digits to ASCII.
     * Strips house prefixes (`بيت`, `منزل`, `دار`, `شقة`, `عمارة`, `فيلا`, `وحدة`, `رقم`, `مبنى`, `سكن`, `house`, `flat`, `unit`, `villa`, `building`, `apt`, `apartment`, `no.`, `h.`, `#`).
     * Normalizes letter suffixes (e.g., `552أ` or `552 أ` $\rightarrow$ `552A`).
   - Updated `GetArabicSearchVariants`:
     * Generates both Latin digit and Arabic-Indic digit search variants.
     * Extracts core house number and adds its numeric and letter variations.
   - Updated `ScoreTenantMatch`:
     * Matches tenants by extracted house number with high score (950) when the query targets a house number (e.g. `٥٠٠`, `بيت ٥٠٠`, `552A`, `٥٥٢أ`).
2. **`FileOrganizerRepository.cs`**:
   - Updated `SearchAsync` to extract `coreHouseNumber`, adding prioritized sorting:
     * Exact house match (`LOWER(h.id) = @ExactHouse`) ranked first.
     * Prefix house match (`LOWER(h.id) LIKE @PrefixHouse`) ranked second.
     * Then by ID length and alphabetical.
   - Updated `CreateHouseAsync` to normalize Arabic digits on house creation.
3. **Frontend (`command-palette.js` and `index.html`)**:
   - Added `normalizeArabicDigits` in `command-palette.js` for client-side search and static mode.
   - Updated search input placeholder and empty state helper text to explicitly guide users (`e.g. 500 or ٥٠٠`).
   - Synced changes to `dist/win-x64/`.

## Verification
- **Automated Tests**:
  - Created `tests/HousingApplication.Tests/HouseNumberSearchTests.cs` (25 test cases covering Arabic digits, Eastern digits, Arabic prefixes, English prefixes, letter suffixes, and flat IDs).
  - `dotnet test`: **925 Passed, 0 Failed**.
  - `npm test`: **361 Passed, 0 Failed** across 31 test suites.
- **Live Search API Verification**:
  - `curl /api/search?q=٥٠٠`: Returns House 500 (`Safra D • فواز خليل الطارش • 66 Documents`) at #1, plus tenants Fawaz, Abdullah, and Adel.
  - `curl /api/search?q=بيت+٥٠٠`: Returns House 500 at #1, plus tenants.
  - `curl /api/search?q=منزل+٥٠٠`: Returns House 500 at #1, plus tenants.
  - `curl /api/search?q=٥٥٢أ`: Returns House 552A at #1, plus tenants Adnan and Avinash.
  - `curl /api/search?q=شقة+٢٤٥٠_١`: Returns House SAF F 2450_1 at #1.
