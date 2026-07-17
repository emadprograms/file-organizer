<!-- generated-by: gsd-doc-writer -->
# Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes* | - | The primary Google GenAI API key used by the application. *(Required by `src/main.py`)* |
| `GEMINI_API_KEYS` | No | - | Included in `.env.example`. When using `rotate_process.py`, multiple keys can be specified. |
| `OPENROUTER_API_KEY` | No | - | Placeholder API key in `.env.example` (currently unused). |
| `GROQ_API_KEY` | No | - | Placeholder API key in `.env.example` (currently unused). |
| `OPENROUTER_MODEL` | No | `google/gemma-4-31b-it` | Model identifier when OpenRouter is used. |
| `GROQ_MODEL` | No | `qwen/qwen3.6-27b` | Model identifier when Groq is used. |
| `GEMINI_MODEL` | No | `gemma-4-31b-it` | Default model identifier for Gemini orchestration. |
| `ROUTING_MODEL` | No | `google/gemma-4-31b-it` | Default routing model for categorization. |

### Config File Format

The project relies on environment variables for configuration. The primary mechanism is a `.env` file located in the root directory.

```env
GEMINI_API_KEYS=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

**Wrapper Configuration (`rotate_process.py`)**
If running batch jobs using the `rotate_process.py` wrapper script, the `.env` file parsing is uniquely flexible. It supports either standard `KEY=VALUE` pairs (extracting all values as keys) or a list of raw Google API keys (starting with `AIza`), with each key on a separate line. The wrapper cycles through these extracted keys, passing them individually as `GEMINI_API_KEY` to each subprocess.

The batch target directory for `rotate_process.py` is configured directly inside the script rather than through environment variables (e.g., `target_dir = r"D:\\Safra D"`). <!-- VERIFY: Ensure the target directory path is correct for the deployment environment -->

### Required vs Optional Settings

- **Required**: The `GEMINI_API_KEY` must be set for the application to function. If omitted when executing `src/main.py`, the system throws an early validation error: `ConfigurationError("GEMINI_API_KEY is missing from the environment.")`.
- **Optional**: All model-specific environment variables are optional. The system gracefully falls back to sensible defaults.

### Defaults

Optional settings have predefined fallback defaults defined in `src/core/config.py`:
- `OPENROUTER_MODEL`: `google/gemma-4-31b-it`
- `GROQ_MODEL`: `qwen/qwen3.6-27b`
- `GEMINI_MODEL`: `gemma-4-31b-it`
- `ROUTING_MODEL`: `google/gemma-4-31b-it`

The CLI entry point (`src/main.py`) also applies a default value for the `--model` argument: `gemma-4-31b-it`.

### Per-Environment Overrides

The application uses `python-dotenv` to automatically load configuration values from the `.env` file at startup.
For continuous integration, Docker environments, or specific runtime environments (development, staging, production), you can set native environment variables directly in your host shell or platform secret manager. Native environment variables injected directly into the shell session take precedence over `.env` declarations.
