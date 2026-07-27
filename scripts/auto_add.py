import argparse
import os
import sys
import shutil
from pathlib import Path
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config import AppConfig
from src.llm.llm import LLMClient
from src.watcher.orchestrator import FSUIOrchestrator
from src.reconcile.core import run_reconcile_mode
from src.utils.logger import setup_logging
from dotenv import load_dotenv

class DummyArgs:
    pass

def main():
    parser = argparse.ArgumentParser(description="Auto Add Workflow: Reconcile -> Copy -> Propose -> Finalize")
    parser.add_argument("house_id", help="House ID (e.g. 502)")
    parser.add_argument("area", help="Area name (e.g. 'Safra D')")
    parser.add_argument("--additions-dir", type=Path, default=Path("D:/Safra D additions"), help="Path to additions folder")
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger("file_organizer.auto_add")
    load_dotenv()
    
    config_path = Path("config.yaml")
    if not config_path.exists():
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"
        
    config = AppConfig.load(config_path)
    areas_root = Path(config.areas_root_path)
    
    # 1. Find House Folder
    area_dir = areas_root / args.area
    if not area_dir.exists():
        logger.error(f"Area dir does not exist: {area_dir}")
        return 1
        
    house_dir = None
    for child in area_dir.iterdir():
        if child.is_dir() and (child.name == args.house_id or child.name.startswith(f"{args.house_id} - ")):
            house_dir = child
            break
            
    if not house_dir:
        logger.error(f"Could not find house folder for {args.house_id} in {area_dir}")
        return 1
        
    logger.info(f"Found house directory: {house_dir}")
    
    # 2. Reconcile
    logger.info("Running reconciliation...")
    rec_args = DummyArgs()
    rec_args.target_dir = house_dir
    rec_args.dry_run = False
    rec_args.command = "reconcile"
    rec_args.tenants = True
    
    res = run_reconcile_mode(rec_args)
    if res != 0:
        logger.error("Reconciliation failed!")
        return res
    
    # Re-find the house folder in case it was renamed during reconciliation
    house_dir = None
    for child in area_dir.iterdir():
        if child.is_dir() and (child.name == args.house_id or child.name.startswith(f"{args.house_id} - ")):
            house_dir = child
            break
            
    if not house_dir:
        logger.error(f"Could not find house folder after reconciliation!")
        return 1
    
    # 3. Copy Addition PDF
    source_pdf = args.additions_dir / f"{args.house_id}.pdf"
    if not source_pdf.exists():
        logger.error(f"Source PDF does not exist: {source_pdf}")
        return 1
        
    inbox_dir = Path(config.inbox_path)
    inbox_dir.mkdir(parents=True, exist_ok=True)
    
    dest_pdf = inbox_dir / f"{args.house_id}.pdf"
    shutil.copy2(source_pdf, dest_pdf)
    logger.info(f"Copied {source_pdf} to {dest_pdf}")
    
    # 4. Propose
    llm_client = LLMClient(api_key=os.getenv("GEMINI_API_KEY"))
    orchestrator = FSUIOrchestrator(config, llm_client)
    
    logger.info("Running Propose phase...")
    orchestrator.propose(dest_pdf)
    
    # 5. Rename Proposed to OK and Finalize
    logger.info("Renaming Proposed to OK and Finalizing...")
    proposed_files = list(inbox_dir.glob(f"*{args.house_id}*Proposed.pdf"))
    if not proposed_files:
        logger.error("No Proposed files found! Propose might have failed.")
        return 1
        
    for p_file in proposed_files:
        ok_name = p_file.name.replace(" Proposed.pdf", " OK.pdf")
        ok_file = p_file.parent / ok_name
        p_file.rename(ok_file)
        logger.info(f"Finalizing {ok_file.name}...")
        try:
            orchestrator.finalize(ok_file)
        except Exception as e:
            logger.error(f"Failed to finalize {ok_file.name}: {e}")
            
    logger.info("Workflow completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
