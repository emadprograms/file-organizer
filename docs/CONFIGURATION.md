<!-- generated-by: gsd-doc-writer -->
# Configuration

## Environment Variables

The application's core infrastructure is configured through environment variables. Use a `.env` file in the root directory for local development.

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `GEMINI_API_KEY` | **Yes** | None | Primary API key for Google Gemini. Required for the core pipeline. |
| `OPENROUTER_API_KEY` | No | None | Fallback API key for OpenRouter. Used if Gemini failover is triggered. |
| `GROQ_API_KEY` | No | None | Fallback API key for Groq. Used if Gemini failover is triggered. |
| `OPENROUTER_MODEL` | No | `google/gemma-4-31b-it` | The model used when routing through OpenRouter. |
| `GROQ_MODEL` | No | `qwen3.6-27b` | The model used when routing through Groq. |

## User Configuration File (YAML/JSON)

The core logic of extraction, classification, and routing is fully driven by a user-supplied configuration file (passed via the `-c` flag). This allows the tool to process any type of document, not just housing records.

### Configuration Sections

1. **`categories`**: Defines the target classes for the document pages. Each category needs an `id`, a `name`, and a detailed `description` used by the AI to make classification decisions.
2. **`extraction`**: Provides the AI with a `prompt_template` instructing it on how to process the pages. It also defines custom `fields` (names, types, and descriptions) to extract from each page.
3. **`grouping`**: Configures how individual pages are grouped into logical documents. For instance, using `strategy: "python"` allows referencing a custom `script_path`.
4. **`routing`**: Determines the output directory structure. It specifies `destination_format` (e.g., `{primary_tenant}/{category}`), a `fallback_folder`, and potentially a custom `script_path` to resolve metadata.
5. **`cleaning`**: Instructs the pipeline on data normalization strategies (e.g., `strategy: "hybrid"`).

See `sample-config.yaml` for a complete example.

## Required vs Optional Settings
- **GEMINI_API_KEY**: Required. The application will error out if this key is missing upon startup.
- **Fallback Keys**: Optional. If missing, the system logs a warning that cloud failover may be limited.

## Defaults
- **API Quota**: <!-- VERIFY: The system tracks API usage with a default QUOTA_LIMIT of 1500 calls per 24 hours. --> The system tracks API usage in `.tracking/api_calls.log` with a default `QUOTA_LIMIT` of 1500 calls per 24 hours.
- **Output Directory**: Defaults to `./output` if the `-o` flag is not provided via CLI.

## Per-Environment Overrides
For different environments, you can maintain separate `.env` files (e.g., `.env.dev`, `.env.prod`) and load the appropriate one before running the application.
