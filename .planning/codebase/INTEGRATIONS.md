# External Integrations & Services

## Overview
File Organizer integrates with external AI foundation models, local Windows COM/Shell APIs, and filesystem subsystems to deliver an automated, synchronized document processing and archiving pipeline.

---

## 1. LLM & Cloud AI Services

The application interacts with cloud-hosted Large Multimodal Models (LMMs) for image perception, page classification, Arabic metadata extraction, and semantic boundary detection. All provider calls are abstracted using the Strategy Pattern via the [`LLMProvider`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/llm/providers.py#L20) protocol.

### Primary Provider: Google Gemini API
- **Client SDK**: `google-genai` (Official modern Google GenAI Python SDK).
- **Authentication**: `GEMINI_API_KEY` (or multi-key distribution via `GEMINI_API_KEYS`).
- **Primary Model**: `gemini-3.5-flash` (default) / `gemini-2.5-flash` (legacy/override).
- **Fallback Models**:
  1. `gemini-3.5-flash-lite`
  2. `gemini-3.1-flash-lite`
  3. `gemini-3.6-flash`
  4. `gemini-3.5-flash`
  5. `gemini-3-flash-preview`
  6. `gemini-2.5-flash`
- **Structured Outputs**: Direct schema validation via Pydantic (`config=types.GenerateContentConfig(response_schema=..., response_mime_type="application/json")`).
- **Image Transport Optimization**: Due to Cloud Storage 403 quota restrictions on rapid file uploads, image payloads are processed as in-memory PIL Images and encoded inline within multi-modal request payloads.

### Secondary Providers & Fallbacks (OpenAI Protocol Compatible)
- **OpenRouter API**:
  - **Client**: `openai.OpenAI`
  - **Auth & Config**: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` (default: `google/gemini-3.5-flash`).
- **Groq API**:
  - **Client**: `openai.OpenAI`
  - **Auth & Config**: `GROQ_API_KEY`, `GROQ_MODEL` (default: `qwen/qwen3.6-27b`).

### Rate Limiting & Resilience Architecture
- **Application Throttle**: Enforces `delay_between_pages` (default: 7.0 seconds between image requests).
- **HTTP 429 Backoff**: Detects rate limiting and automatically triggers a 65-second cooldown before retrying.
- **Fail-Fast Policy**: Auth errors (400, 401, 403) halt immediately (`LLMFailureError`). Network read timeouts bypass retries to immediately cascade to the next fallback model.
- **Usage & Quota Logging**: Every successful API invocation appends timestamps to `.tracking/api_calls.log`. Detailed execution payloads and error diagnostics are captured in `logs/<run_id>/traces.jsonl`.

---

## 2. Windows OS & Shell Interop

File Organizer relies on native Windows subsystem features to generate and inspect `.lnk` shortcut files without requiring binary shortcut parser dependencies at runtime.

### PowerShell COM Interop (`windows_shortcut.ps1`)
- **Location**: [`src/utils/windows_shortcut.ps1`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/utils/windows_shortcut.ps1)
- **Mechanism**: Dynamic C# P/Invoke compilation via `Add-Type` interacting directly with Windows Shell COM interfaces:
  - `IShellLinkW` (`{000214F9-0000-0000-C000-000000000046}`)
  - `IPersistFile` (`{0000010b-0000-0000-C000-000000000046}`)
- **Operations**:
  - `create`: Creates a single `.lnk` file pointing to an absolute target file path.
  - `batch-create`: Consumes a JSON array of `[{"target": ..., "link": ...}]` to create dozens of shortcuts in a single sub-process invocation.
  - `batch-read`: Consumes a JSON array of link paths and resolves target locations in one batch pass for fast reconciliation.
- **Path Sanitization**: Strips Windows extended-length path prefixes (`\\?\` and `\\?\UNC\`) before COM invocation, which are incompatible with `WScript.Shell` / `IShellLinkW`.

---

## 3. Filesystem & Storage Layout

The application organizes and reconciles multi-tenant housing documents on local or network-attached NTFS/SMB file shares.

```
[House Root Directory] (e.g., Areas/123/703/)
├── .source_files/
│   ├── vault/
│   │   ├── doc_001.pdf
│   │   ├── doc_002.pdf
│   │   └── ...
│   ├── 703_state.json         <-- Single source of truth
│   ├── 703_tenants.yaml       <-- Optional tenant timeline configuration
│   └── 703.raw_dump.json      <-- OCR/LLM raw classification dump
├── 01_بيانات أساسية/
├── 02_بيانات شخصية/
├── 05_عقود/
│   └── 703 - 2024-01-15 - عقد إيجار.lnk  <-- Windows Shortcut pointing to vault
├── ...
└── [Timeline View]/
    ├── 001 - 2020-03-01 - بطاقة هوية.lnk
    ├── 002 - 2024-01-15 - عقد إيجار.lnk
    └── ...
```

### Storage Safety & Concurrency
- **Atomic File Writing**: [`atomic_write`](file:///C:/Users/Emad/Documents/GitHub/file-organizer/src/utils/fs.py#L13) writes content to `%TEMP%` and executes atomic replacement with a 10-attempt retry loop to handle Windows file locking from antivirus or OneDrive syncing.
- **Process Mutex Locks**: Inbox processing uses PID-based lock files in `~/.file-organizer/locks/inbox_<hash>.lock` to prevent concurrent overlapping executions on the same inbox directory.

---

## 4. Configuration & Domain Files

| Integration Point | File / Path | Schema / Purpose |
| :--- | :--- | :--- |
| **App Configuration** | `config.yaml` / `config.sample.yaml` | Defines `inbox_path`, `areas_root_path`, and `area_mappings` (Area Name $\rightarrow$ Area ID). |
| **Category Rules** | `src/core/categories.yaml` | Master document category definitions and descriptions used in classification prompts. |
| **Tenant Timeline Config** | `.source_files/{house_id}_tenants.yaml` | Overrides or supplements tenant discovery with explicit names, start dates, and end dates. |
| **Inbox Filename Interface** | Ingested PDF names in `inbox_path` | Space-separated command format: `[AREA] [HOUSE] [TENANT_HINT] [GROUP] [DATE] [TITLE].pdf` parsed by `inbox/parser.py`. |
