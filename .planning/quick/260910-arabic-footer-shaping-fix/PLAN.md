# Quick Task Plan: Fix Arabic Category Text Shaping in PDF Export Running Footer

## Context & Problem
In the exported chronological PDF dossier, the category name at the bottom center of each page currently renders in "terminal Arabic" — isolated, disconnected letters drawn in LTR order (e.g. separate letters `ع` `ق` `و` `د` instead of the connected cursive Arabic word `عقود`).
In PDF rendering engines (PyMuPDF `insert_text` and PDFSharpCore `DrawString`), raw Unicode Arabic characters do not automatically receive complex script shaping and bidirectional reordering.

## Objective
Implement proper Arabic contextual reshaping (initial, medial, final, isolated forms) and bidirectional (BiDi) visual reordering across both the Python FastAPI backend (`src/api/routes.py`) and ASP.NET Core 8.0 backend (`web-net/Program.cs`), with unit and integration tests verifying properly connected glyphs.

## Implementation Details
1. **Python FastAPI Backend**:
   - Ensure `requirements.txt` contains `arabic-reshaper` and `python-bidi`.
   - In `src/api/routes.py`:
     - Shape and reorder Arabic category strings using `get_display(arabic_reshaper.reshape(clean_cat))`.
     - Calculate text width and draw the shaped text onto the PDF page.
2. **ASP.NET Core 8.0 Backend**:
   - Implement `web-net/Common/ArabicReshaper.cs`:
     - Standalone, zero-dependency C# class providing contextual letter reshaping (Unicode Presentation Forms-B) and visual RTL word/character reordering.
   - In `web-net/Program.cs`:
     - In `/api/areas/{areaId}/houses/{houseId}/export-pdf`, pass `ArabicReshaper.ReshapeAndReorder(cleanCat)` to `gfx.DrawString`.
3. **Automated Testing**:
   - In `tests/test_v14_features.py`:
     - In `test_export_house_archive_pdf_running_footer`, assert that the extracted text in the PDF contains reshaped cursive Arabic forms (e.g. `ﻋﻘﻮﺩ` / `ﺩﻮﻘﻋ`) rather than raw disconnected letters.
   - In `web-net/FileOrganizer.Tests/`:
     - Add unit tests in `ArabicReshaperTests.cs` verifying all 13 standard Arabic category names.
     - Verify `ApiEndpointTests.cs` runs and passes.
4. **Verification**:
   - `.venv/bin/pytest tests/test_v14_features.py -v`
   - `~/.dotnet/dotnet test web-net/FileOrganizer.Tests/`
   - `npm run test:frontend`
5. **Documentation & Commit**:
   - Create `SUMMARY.md`.
   - Update `.planning/STATE.md`.
   - Commit and push to `origin/main`.
