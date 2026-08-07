# scripts/list_models.py
"""
Utility script to list all Gemini/Google Generative AI models available for each API key
found in .env or .env2. It uses the legacy `google.generativeai` library (still functional)
and prints the key name together with the model names returned by `genai.list_models()`.
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

ENV_FILES = [".env", ".env2"]

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

def main():
    project_root = Path(__file__).resolve().parent.parent
    all_keys = []
    for env_file in ENV_FILES:
        all_keys.extend(load_keys(project_root / env_file))
    if not all_keys:
        print("No API keys found in .env/.env2.")
        sys.exit(1)

    for name, key in all_keys:
        print(f"=== Models for {name} ===")
        try:
            genai.configure(api_key=key)
            models = genai.list_models()
            for m in models:
                print(f"- {m.name}")
        except Exception as e:
            print(f"Error retrieving models for {name}: {e}")
        print()

if __name__ == "__main__":
    main()
