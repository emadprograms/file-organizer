# scripts/check_api_keys.py
"""
Utility script to iterate over API keys defined in .env and .env2 files,
find a valid Gemma 4 31b model, send a minimal "hi" prompt, and report which
keys succeed or fail.

Usage:
    python scripts/check_api_keys.py
"""
import os
import sys
from pathlib import Path

try:
    import google.genai as genai
except ImportError:
    print("google-genai package not found. Installing...")
    os.system("pip install --quiet google-genai")
    import google.genai as genai

# Configuration
ENV_FILES = [".env", ".env2"]
# Model prefix we want – Gemma 4 31b (exact name may vary)
TARGET_MODEL_SUBSTRING = "gemini-2.5-flash"

def load_keys_from_file(file_path: Path):
    """Extract API keys from a .env style file.
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
            if len(line) > 20:
                keys.append(("RAW_KEY", line))
    return keys

def discover_model(api_key: str):
    """Return the first model name containing TARGET_MODEL_SUBSTRING.
    If none found, returns None.
    """
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        for m in models:
            if TARGET_MODEL_SUBSTRING.lower() in m.name.lower():
                return m.name
    except Exception:
        return None
    return None

def test_key(key_name: str, api_key: str):
    """Attempt a minimal request with the given API key using the discovered Gemma model.
    Returns (True, None) on success, (False, error_message) on failure.
    """
    model_name = discover_model(api_key)
    if not model_name:
        return False, f"No model containing '{TARGET_MODEL_SUBSTRING}' found for this key"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("hi")
        _ = response.text
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    project_root = Path(__file__).resolve().parent.parent
    all_keys = []
    for env_file in ENV_FILES:
        path = project_root / env_file
        all_keys.extend(load_keys_from_file(path))
    if not all_keys:
        print("No API keys found in .env/.env2 files.")
        sys.exit(1)

    successes = []
    failures = []
    for name, key in all_keys:
        print(f"Testing key '{name}' ...", end=" ")
        ok, err = test_key(name, key)
        if ok:
            print("OK")
            successes.append(name)
        else:
            print("FAIL")
            failures.append((name, err))

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
