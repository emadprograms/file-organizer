# Qwen3-VL 4B Research & Implementation Plan

## Executive Summary
The goal of this phase is to evaluate `qwen3-vl` 4b as a local, offline alternative to the cloud-based LLM API (currently Gemini) for classifying document pages as 'form', 'letter', or 'picture'. Qwen3-VL-4B is a highly capable multimodal vision-language model by Alibaba Cloud that natively supports image inputs and complex visual reasoning. It is designed to be efficient enough to run locally while retaining strong accuracy. We will implement a proof-of-concept in the `scratch/` directory to measure its accuracy and feasibility as a full replacement.

## Codebase Context
The existing implementation (`scratch/classify_559.py`) relies on an `LLMClient` that routes calls to a cloud provider (Gemini) using the `google.genai` SDK. It passes an image (converted from a PDF page via PyMuPDF/fitz) and a system prompt expecting a strict JSON output matching a Pydantic schema (`SimpleClassification`).

Key integration points and constraints:
- All new code must be strictly restricted to the `scratch/` folder.
- The downstream pipeline (`src/pipeline.py`) expects 'form', 'letter', or 'picture'.
- The solution must match or exceed the accuracy of the current cloud-based method.
- The evaluation will be run against `scratch/ground_truth.json`.

## Technical Approach (How we'll implement qwen3-vl 4b)
We have two primary options for running Qwen3-VL-4B locally. We will start with the **Ollama** approach as it provides the most seamless transition from an API-based workflow, and fall back to **Transformers/vLLM** if finer control is needed.

### Option A: Local API via Ollama (Recommended)
1. **Setup:** Run the model locally using Ollama (`ollama run qwen3-vl:4b`).
2. **Implementation:** Update `scratch/classify_559.py` (or create a new script in `scratch/` to compare) to use the `openai` Python client configured to point to the local Ollama server (`http://localhost:11434/v1`).
3. **Prompting:** We will pass the base64-encoded image of the PDF page along with the system prompt to the local API. Ollama's OpenAI-compatible endpoint supports structured JSON output.

### Option B: Hugging Face Transformers
1. **Setup:** Install `transformers`, `accelerate`, and `qwen-vl-utils`.
2. **Implementation:** Load the `Qwen/Qwen3-VL-4B` model using `AutoProcessor` and the appropriate `ForConditionalGeneration` class.
3. **Execution:** Pass the PIL image and prompt directly through the processor to generate the classification string, parsing the output to ensure it matches 'form', 'letter', or 'picture'.

## Potential Risks
- **Hardware Limitations:** Running a 4B parameter multimodal model requires sufficient VRAM (around 4-8GB depending on quantization). If the local machine lacks a capable GPU, inference may be slow, breaking the "fast offline" requirement.
- **Output Formatting:** Local models can sometimes struggle with strict JSON schemas compared to top-tier cloud models. We may need to refine the prompt or use grammar constraints (e.g., Ollama's `format="json"` or llama.cpp grammars) to enforce the exact schema.
- **Accuracy Drop:** While Qwen3-VL-4B is powerful, it has far fewer parameters than Gemini. There is a risk that accuracy might not match the cloud baseline, which is the user's primary optimization goal.

## Validation Architecture
1. **Baseline Generation:** Run the existing `scratch/classify_559.py` to ensure `scratch/ground_truth.json` is generated and accurate using the Gemini model.
2. **Local Implementation:** Create `scratch/classify_qwen_local.py` implementing the Qwen3-VL approach.
3. **Execution & Comparison:** Run the new script on the same `pdfs/559.pdf` file and output predictions to `scratch/qwen_predictions.json`.
4. **Scoring:** Write a simple evaluator (or manual check) to compare `qwen_predictions.json` against `ground_truth.json` to calculate the accuracy percentage.
5. **Success Criteria:** The local Qwen model must achieve comparable or superior accuracy to the Gemini baseline while successfully running fully offline.
