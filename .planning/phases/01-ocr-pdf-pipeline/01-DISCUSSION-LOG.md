# Phase 1 Discussion Log

## OCR Engine Choice
**Options considered**: Google Cloud Vision API, Tesseract OCR, Azure OCR
**User Selection**: "I wanted to gemma for the ocr. isn't that the best? Instead of using ocr?"
**Notes**: We will skip traditional OCR tools and extract images from the PDF to send directly to the Gemma endpoint.

## PDF Manipulation Tooling
**Options considered**: PyMuPDF, pypdf
**User Selection**: PyMuPDF (fitz)
**Notes**: We will use PyMuPDF for both rendering images and extracting/saving the final PDF segments.

## Performance & Concurrency
**Options considered**: Parallel processing, Sequential processing
**User Selection**: Parallel processing
**Notes**: We will implement parallel processing to speed up the handling of large 200-page files.
