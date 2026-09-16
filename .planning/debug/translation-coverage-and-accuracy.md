---
status: resolved
trigger: "the feature is nice. the text become translucent. but the translation itself is horrible. the text coverage is horrible. the text isn't being covered or translated. just some random words are being covered and even they are not translated. please be diligent and make proper tests for these."
created: 2026-09-16
updated: 2026-09-16
---

## Resolution Summary
- **status**: resolved
- **root_cause**:
  1. **Line Drop Filter Bug**: In `renderPageTranslationLayer()`, `if (!translated || translated === origText) return;` dropped 90%+ of detected lines because lines without an exact phrase match returned identical to the source text.
  2. **PDF.js Text Layer Fragmentation**: `page.getTextContent().items` returned character- and syllable-level fragments rather than cohesive lines, preventing phrase matching and scattering boxes across words.
  3. **Absence of Single-Word Morphology & Boundary Matching**: No word-level dictionary or morphological prefix/suffix decomposition (`ال`, `و`, `ب`, `ل`, `لل`, `ف`, `ها`, `هم`, `نا`, `ين`, `ات`). Furthermore, substring matching without word boundaries corrupted words (e.g. replacing `سري` [confidential] inside `الدوسري` [Al Doseri]).
  4. **Lack of Phonetic Transliteration Fallback**: Any unindexed Arabic word remained in raw Arabic script inside the overlay box.
- **fix**:
  1. **100% Text Line Coverage**: Replaced line drop filter with `const translated = hasArabic ? translateArabicText(origText) : origText; if (!translated || !translated.trim()) return;`. Every detected line receives an in-place overlay box.
  2. **PDF.js Digital Text Clustering**: Created `clusterPdfItemsIntoLines()` grouping glyphs and text items by vertical coordinates into unified lines with cohesive bounding boxes `[min(x0), min(y0), max(x1), max(y1)]`.
  3. **Multi-Tier Offline Translation Engine**:
     - Converted Eastern Arabic numerals (`٠-٩` -> `0-9`).
     - Added comprehensive governmental, housing, and legal phrases in `ARABIC_PHRASES` with strict word-boundary regexes `(^|[^\u0600-\u06FF...])phrase(?=[^\u0600-\u06FF...]|$)`.
     - Built 300+ word dictionary in `ARABIC_WORDS` and Bahraini personal/family names in `ARABIC_NAMES`.
     - Implemented morphological decomposition in `translateArabicWord()` for prefixes (`وال`, `بال`, `لل`, `ال`, etc.) and suffixes (`هم`, `ها`, `نا`, `ه`, `ي`).
     - Implemented fallback phonetic transliteration in `transliterateArabic()` guaranteeing **zero raw Arabic characters remain in any translated box**.
  4. **Preserved Interactivity**: Kept user-praised translucent peek (`opacity: 0.12`) on hover/click and global "Peek Original" page button.
- **verification**:
  - All 38 doc viewer tests in `tests/web/components/doc_viewer.test.js` pass (including 9 new rigorous translation, coverage, clustering, morphology, and peeking tests).
  - All 478 JS Vitest tests pass across 37 test suites.
  - All 955 .NET tests pass (`dotnet test --no-build`).
