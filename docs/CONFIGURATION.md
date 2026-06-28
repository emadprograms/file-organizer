<!-- generated-by: gsd-doc-writer -->
# Configuration

## Environment Variables

The application is configured primarily through environment variables. Use a `.env` file in the root directory for local development.

| Variable | Required | Default | Description |
|:---|:---:|:---|:---|
| `GEMINI_API_KEY` | **Yes** | None | Primary API key for Google Gemini. Required for the core pipeline. |
| `OPENROUTER_API_KEY` | No | None | Fallback API key for OpenRouter. Used if Gemini failover is triggered. |
| `GROQ_API_KEY` | No | None | Fallback API key for Groq. Used if Gemini failover is triggered. |
| `OPENROUTER_MODEL` | No | `google/gemma-4-31b-it` | The model used when routing through OpenRouter. |
| `GROQ_MODEL` | No | `qwen3.6-27b` | The model used when routing through Groq. |

## Config File Format
The application does not use external configuration files (like JSON or YAML) for its core logic, relying instead on the `AppConfig` dataclass in `src/config.py` which is populated from the environment.

## Required vs Optional Settings
- **GEMINI_API_KEY**: Required. The application will call `sys.exit(1)` if this key is missing upon startup.
- **Fallback Keys**: Optional. If missing, the system logs a warning that cloud failover may be limited, but the application will still function using the primary key.

## Defaults
- **API Quota**: The system tracks API usage in `.tracking/api_calls.log` with a default `QUOTA_LIMIT` of 1500 calls per 24 hours.
- **Output Directory**: Defaults to `./output` if the `-o` flag is not provided via CLI.

## Per-Environment Overrides
For different environments, you can maintain separate `.env` files (e.g., `.env.dev`, `.env.prod`) and load the appropriate one before running the application.
