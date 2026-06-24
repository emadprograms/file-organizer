# Phase 7 Research: Local Pass 1 Inference via Mac Mini M4

## Question
**What do I need to know to PLAN this phase well?**

To plan this phase effectively, you must understand the architectural shift from a fully cloud-reliant OCR extraction pipeline to a hybrid local-first approach. This reduces API rate limits and drastically speeds up Pass 1 Vision Extraction.

## Core Objectives & Requirements
This phase must address the following phase requirements:
- **PERF-01**: Drastically speed up Pass 1 Vision Extraction.
- **PERF-02**: Bypass Google API rate limits.
- **ARCH-01**: Implement local inference using Qwen2.5-VL-7B-Instruct via LM Studio.
- **ARCH-02**: Establish a robust hybrid fallback strategy to the cloud.

## Technical Context & Implementation Details

### 1. Local Server Stack & Tooling
- **Inference Engine**: Use **LM Studio** running on the Mac Mini M4. The built-in OpenAI-compatible API server will be utilized.
- **Model**: **Qwen2.5-VL-7B-Instruct**, chosen for its excellent Arabic document OCR capabilities.
- **Storage Constraint (CRITICAL)**: The model files **MUST** be installed and stored strictly on the `micron-e0256a` external drive, NOT on the Mac Mini's main internal drive.
- **Client Integration**: The application will interface with the local LM Studio endpoint using the official `openai` Python package. This package ensures robust handling of schemas and retries, and supports structured JSON outputs via `response_format`.

### 2. Code Refactoring Strategy
- **File `src/llm.py`**:
  - Refactor `GemmaClient.classify_page` to attempt local extraction first via the OpenAI client pointing to the LM Studio endpoint.
  - Update `_route_llm_call` to manage the new routing logic, handle timeouts appropriately, and trigger fallbacks.
- **File `src/schemas.py`**:
  - Ensure the `PageClassification` Pydantic schema maps cleanly to the `openai` client's structured output capabilities.

### 3. Fallback Mechanism Updates
- **Hybrid Strategy**: If the local Qwen2.5-VL inference fails (e.g., hangs, crashes, or produces invalid schema output), the system must seamlessly fall back to cloud inference.
- **Cloud Model Changes**: Exclusively use **Gemini 4 26b** for cloud fallbacks. 
- **Retirements**: **Gemini 4 31b** and **Gemini 2.5 Flash** are officially retired from the fallback mechanism and all associated routing logic must be cleanly removed.

## Validation Architecture

To satisfy the Nyquist validation requirement, testing and validation must be structured as follows:

1. **Local Endpoint Integration Testing**
   - Create unit tests for the `openai` client wrapper to verify that the structured output correctly populates the `PageClassification` schema without dropping fields.
   - Verify that timeouts are respected when the local LM Studio server is unresponsive.

2. **Fallback Strategy Verification**
   - Simulate a hung connection or LM Studio 500 error to guarantee the pipeline successfully catches the exception and immediately reroutes the request to **Gemini 4 26b**.
   - Assert that no fallback requests attempt to route to the retired Gemini 4 31b or 2.5 Flash models under any error conditions.

3. **Arabic OCR Fidelity Testing**
   - Run integration tests with sample Arabic documents to ensure Qwen2.5-VL-7B-Instruct correctly extracts the required data accurately and handles single-word names and "ال" prefixes without data corruption (aligning with ARABIC-01 considerations if applicable).

4. **Environment & Storage Audit**
   - Include a manual validation checklist item verifying that the LM Studio's model cache directory path resolves strictly to the `micron-e0256a` external drive, ensuring the Mac Mini's main storage remains untouched.
