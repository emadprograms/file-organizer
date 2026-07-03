import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def validate_environment():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY is missing from the environment.", file=sys.stderr)
        sys.exit(1)

def get_parser():
    parser = argparse.ArgumentParser(description="File Organizer Post-Processor")
    parser.add_argument("target_dir", type=Path, help="Path to the target directory containing the categorized PDF and report JSON")
    parser.add_argument("--model", type=str, default="gemma-4-26b-a4b-it", help="LLM model to use")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    validate_environment()
    # Further logic will be attached here
    return 0

if __name__ == "__main__":
    sys.exit(main())
