import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load .env manually because it has no KEY=value format
with open(".env", "r") as f:
    lines = f.readlines()
    if len(lines) > 1:
        os.environ["GEMINI_API_KEY"] = lines[1].strip()

from src.core.config import AppConfig
from src.llm.llm import LLMClient
from src.fs_ui.orchestrator import FSUIOrchestrator
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

config = AppConfig.load(Path("config.yaml"))
llm_client = LLMClient(api_key=os.getenv("GEMINI_API_KEY"))
orchestrator = FSUIOrchestrator(config, llm_client)
print("Processing inbox once...")

inbox_dir = Path(config.inbox_path)
for pdf_path in inbox_dir.glob("*.pdf"):
    print(f"Found {pdf_path}")
    if pdf_path.name.endswith(" OK.pdf"):
        orchestrator.finalize(pdf_path)
    elif not pdf_path.name.endswith("_Proposed.pdf") and not pdf_path.name.endswith("_Failed.pdf"):
        orchestrator.propose(pdf_path)

print("Done")
