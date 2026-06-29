# Arabic Document OCR & Translation Pipeline Research

## Objective
To develop a robust image pre-processing pipeline capable of cleaning scanned official Arabic documents (specifically those suffering from bleed-through, dark watermarks, and low contrast) to perfectly extract and translate the text using the Gemma 4 26B vision model.

## Methodology & Findings

### 1. Initial Attempts: Binarization vs. Illumination Normalization
- **Basic Contrast/Thresholding:** Simple thresholding and binarization destroyed the Arabic script. Arabic typography relies heavily on fine connecting strokes (Mashq) and tiny diacritics (dots). Hard binarization erased critical dots (which changes letters entirely) and broke connecting lines, making the text unreadable for OCR engines.
- **The Breakthrough (Division Normalization):** We extracted the Green Channel (which provided the highest contrast for black text over pale watermarks) and estimated a background illumination map by heavily dilating and blurring the image to "erase" the text. Dividing the original image by this illumination map perfectly flattened the lighting and neutralized shadows/watermarks while completely preserving the anti-aliased sub-pixels of the text.

### 2. The Danger of Over-cleaning
We tested washing out the normalized background using a Levels adjustment at different "White Points" (`160`, `200`, `220`).
- **White Point 160 (Aggressive):** This created a perfectly stark, pure-white background that looked beautiful to the human eye. However, it caused massive **data loss**. It erased the faint ink strokes in loops (turning the number '9' into a '1') and deleted faint diacritic dots (causing the model to read the area 'Sitra' as 'Sahira'). Furthermore, the extremely high-contrast sparse pixel map actually triggered an internal vision encoder bug (500 INTERNAL error) on the Gemma backend.
- **White Point 200 - 220 (Optimal):** A much gentler washout preserves the physical integrity of the original ink, retaining the crucial mid-tones. This allowed the AI model to accurately read fine strokes, faint numbers, and even accurately detect "smudged/modified" text fields that the aggressive clean completely erased. 

### 3. Diacritic Boost (Black-Hat Filter)
By applying a morphological Black-Hat filter using a tiny 3x3 kernel *after* the washout, we successfully isolated and deepened the remaining tiny dark objects (Arabic dots/Tashkeel) without artificially boosting background noise.

### 4. Gemma Integration
The final, optimally cleaned image can be successfully passed into the `models/gemma-4-26b-a4b-it` vision endpoint. When the noise is properly neutralized without erasing the mid-tones, the model provides highly accurate, hallucination-free English translations of complex official documents.
