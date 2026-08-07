# scripts/check_gemma_keys.py
"""
Utility script that tests every Gemini/Google AI API key for compatibility with
the model `gemma-4-31b-it`.

For each key it:
  • Configures the legacy `google.generativeai` client.
  • Verifies that `gemma-4-31b-it` appears in the list of available models.
  • Sends a tiny "hi" prompt to the model.
  • Reports success or failure (with the error message when a key cannot reach the model).

Usage:
    python scripts/check_gemma_keys.py
"""

import os
import sys
from pathlib import Path

# Import the legacy library that supports `configure` and `list_models`.
try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeai package not found. Installing it now…")
    os.system("pip install --quiet google-generativeai")
    import google.generativeai as genai

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ENV_FILES = [".env", ".env2"]
TARGET_MODEL = "gemma-4-31b-it"        # exact model name to test


def load_keys(file_path: Path):
    """Read API keys from a .env‑style file.

    Returns a list of (key_name, key_value) tuples.
    """
    keys = []
    if not file_path.exists():
        return keys
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip().strip('"')
            if name.upper().endswith("API_KEY") and value:
                keys.append((name, value))
        else:
            # raw key without a variable name
            if len(line) > 20:
                keys.append(("RAW_KEY", line))
    return keys


def model_available(api_key: str) -> bool:
    """Return True if `TARGET_MODEL` appears in the key's model list."""
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if m.name == TARGET_MODEL:
                return True
    except Exception:
        pass
    return False


def test_key(key_name: str, api_key: str):
    """Send a tiny prompt to TARGET_MODEL using the given API key.

    Returns (True, None) on success, (False, error_msg) on failure.
    """
    if not model_available(api_key):
        return False, f"Model '{TARGET_MODEL}' not available for this key"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(TARGET_MODEL)
        response = model.generate_content("hi")
        _ = response.text  # force evaluation
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    project_root = Path(__file__).resolve().parent.parent
    all_keys = []
    for env_file in ENV_FILES:
        all_keys.extend(load_keys(project_root / env_file))

    if not all_keys:
        print("No API keys found in .env/.env2.")
        sys.exit(1)

    successes = []
    failures = []

    for name, key in all_keys:
        print(f"Testing key '{name}' …", end=" ")
        ok, err = test_key(name, key)
        if ok:
            print("OK")
            successes.append(name)
        else:
            print("FAIL")
            failures.append((name, err))

    # ---------- Summary ----------
    print("\n--- Summary ---")
    print(f"Successful keys ({len(successes)}): {', '.join(successes) if successes else 'None'}")
    if failures:
        print(f"Failed keys ({len(failures)}):")
        for name, err in failures:
            print(f"  - {name}: {err}")
    else:
        print("All keys succeeded.")


if __name__ == "__main__":
    main()
