---
wave: 1
depends_on: []
files_modified:
  - scratch/classify_559.py
  - scratch/classify_qwen_local.py
  - scratch/compare_predictions.py
autonomous: true
---

# Phase 1: explore-alternatives-to-llm-classification

## Verification Criteria

<must_haves>
  <truths>
    - D-01: Previous local options (LayoutLM, OpenCV heuristics, rule-based) are discarded.
    - D-02: Implement a new approach using the qwen2.5-vl model.
    - D-03: All created or modified files MUST be located inside the `scratch/` directory. No modifications are permitted in the `src/` directory.
    - D-04: Accuracy remains the primary optimization goal.
    - D-05: Evaluate the qwen2.5-vl model as a full local replacement for the current LLM API classification.
    - `scratch/ground_truth.json` MUST be successfully generated from the baseline script.
    - `scratch/classify_qwen_local.py` MUST successfully execute fully offline using the local `qwen2.5-vl` model.
    - `scratch/1281_qwen_predictions.json` MUST be generated and contain valid classifications for `pdfs/1281_cleaned.pdf`.
    - `scratch/compare_predictions.py` MUST successfully calculate the accuracy and output it to `scratch/1281_qwen_accuracy_report.txt`.
  </truths>
</must_haves>

## Artifacts this phase produces

- `scratch/ground_truth.json` (JSON data structure containing baseline classifications)
- `scratch/classify_qwen_local.py` (Python script executable)
- `scratch/1281_qwen_predictions.json` (JSON data structure containing Qwen2.5-VL classifications)
- `scratch/compare_predictions.py` (Python script executable)
- `scratch/1281_qwen_accuracy_report.txt` (Text file report)

## Tasks

<task>
  <id>1</id>
  <name>Generate Ground Truth</name>
  <read_first>scratch/classify_559.py</read_first>
  <action>Modify `scratch/classify_559.py` to ensure it outputs its Gemini API baseline predictions to `scratch/ground_truth.json` upon execution, and run it against `pdfs/1281_cleaned.pdf`.</action>
  <acceptance_criteria>The file `scratch/ground_truth.json` exists and contains a valid JSON representation mapping page numbers to their respective 'form', 'letter', or 'picture' classifications for `pdfs/1281_cleaned.pdf`.</acceptance_criteria>
</task>

<task>
  <id>2</id>
  <name>Implement Qwen2.5-VL Local Classifier</name>
  <read_first>scratch/classify_559.py</read_first>
  <action>Create `scratch/classify_qwen_local.py` which uses `fitz` (PyMuPDF) to extract images from `pdfs/1281_cleaned.pdf` and queries a local `qwen2.5-vl` model (via Ollama at `http://localhost:11434/v1` or HuggingFace Transformers) to classify each page as 'form', 'letter', or 'picture'. Save the output to `scratch/1281_qwen_predictions.json`.</action>
  <acceptance_criteria>The script `scratch/classify_qwen_local.py` exists, runs without connecting to cloud APIs, and generates a `scratch/1281_qwen_predictions.json` file structured identically to `scratch/ground_truth.json`.</acceptance_criteria>
</task>

<task>
  <id>3</id>
  <name>Evaluate Qwen2.5-VL Accuracy</name>
  <read_first>scratch/ground_truth.json, scratch/1281_qwen_predictions.json</read_first>
  <action>Create and run `scratch/compare_predictions.py` to compare the JSON outputs from `scratch/ground_truth.json` and `scratch/1281_qwen_predictions.json`. Calculate the percentage of matching classifications and save the results (accuracy score and any discrepancies) to `scratch/1281_qwen_accuracy_report.txt`.</action>
  <acceptance_criteria>The file `scratch/compare_predictions.py` exists, and its execution successfully generates `scratch/1281_qwen_accuracy_report.txt` containing the calculated accuracy percentage and list of mismatches.</acceptance_criteria>
</task>
