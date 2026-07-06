<!-- generated-by: gsd-doc-writer -->
# Configuration

## Environment Variables

The application's core infrastructure is configured through environment variables. Use a `.env` file in the root directory for local development.

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `GEMINI_API_KEY` | **Yes** | None | Primary API key for Google Gemini. Required for the core pipeline. |
| `OPENROUTER_API_KEY` | No | None | Fallback API key for OpenRouter. Used if Gemini failover is triggered. |
| `GROQ_API_KEY` | No | None | Fallback API key for Groq. Used if Gemini failover is triggered. |
| `GEMINI_MODEL` | No | `gemma-4-26b-a4b-it` | The model used when routing through Gemini. |
| `OPENROUTER_MODEL` | No | `google/gemma-4-26b-a4b-it` | The model used when routing through OpenRouter. |
| `GROQ_MODEL` | No | `qwen/qwen3.6-27b` | The model used when routing through Groq. |

## User Configuration File Format

The core logic of extraction, classification, grouping, and routing is fully driven by a user-supplied configuration file (passed via the `-c` flag, default: `config.yaml`). The file can be YAML or JSON format.

```yaml
categories:
  - id: CONTRACT
    name: "Housing Contract"
    description: "Rental or housing contracts."

extraction:
  prompt_template: "You are an Arabic document classification expert..."
  fields:
    - name: residents
      type: "list[str]"
      description: "List of resident names in Arabic..."

grouping:
  strategy: "python"
  script_path: "./scripts/sample-grouping.py"

routing:
  strategy: "python"
  fallback_folder: "UNKNOWN"
  script_path: "./scripts/sample-routing.py"

cleaning:
  strategy: "hybrid"
```

### Configuration Sections

1. **`categories`**: Defines the target classes for the document pages. Each category needs an `id`, a `name`, and a detailed `description` used by the AI to make classification decisions.
2. **`extraction`**: Provides the AI with a `prompt_template` instructing it on how to process the pages. It also defines custom `fields` (names, types, and descriptions) to extract from each page.
3. **`grouping`**: Configures how individual pages are grouped into logical documents. For instance, using `strategy: "python"` allows referencing a custom `script_path`.
4. **`routing`**: Determines the output directory structure. It specifies `destination_format` (e.g., `{primary_tenant}/{category}`), a `fallback_folder`, and potentially a custom `script_path` to resolve metadata.
5. **`cleaning`**: Instructs the pipeline on data normalization strategies (e.g., `strategy: "hybrid"`).

## Required vs Optional Settings

- **GEMINI_API_KEY**: **Required**. The application will throw a fatal error on startup if this key is missing.
- **Fallback Keys (OPENROUTER_API_KEY, GROQ_API_KEY)**: **Optional**. If missing, the system logs a warning that cloud failover may be limited, but will still start and attempt to use Gemini exclusively.

## Defaults

- **API Quota**: The system tracks API usage in `.tracking/api_calls.log` with a default `QUOTA_LIMIT` of `1500` calls per 24 hours.
- **Models**:
  - `GEMINI_MODEL`: `gemma-4-26b-a4b-it`
  - `OPENROUTER_MODEL`: `google/gemma-4-26b-a4b-it`
  - `GROQ_MODEL`: `qwen/qwen3.6-27b`
- **Output Directory**: Defaults to `./output` if the `-o` or `--output` flag is not provided via CLI.
- **Config File**: Defaults to `config.yaml` if the `-c` or `--config` flag is not provided via CLI.

## Per-Environment Overrides

For different environments, you can maintain separate `.env` files (e.g., `.env.development`, `.env.production`) and load the appropriate one before running the application, or set these variables natively in your platform's environment variable manager.
