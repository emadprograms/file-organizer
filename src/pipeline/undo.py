import logging
import json
import shutil
from pathlib import Path
import fitz

logger = logging.getLogger(f"file_organizer.{__name__}")

def run_undo(target_dir: Path) -> int:
    """Run the undo command to reconstruct the original PDF and clean up.
    
    Args:
        target_dir (Path): The directory to run the undo operation on.
        
    Returns:
        int: 0 on success, 1 on failure.
    """
    try:
        if not target_dir.is_dir():
            logger.error(f"Target directory does not exist or is not a directory: {target_dir}")
            return 1
            
        house_id = target_dir.name.split(" - ")[0]
        
        state_dir = target_dir / ".source_files"
        state_file = state_dir / f"{house_id}_state.json"
        
        if not state_file.exists():
            logger.error(f"State file not found: {state_file}")
            return 1
            
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            
        routed_documents = state_data.get("routed_documents")
        if not routed_documents:
            logger.error("No routed documents found in state file.")
            return 1
            
        # Sort documents by start_page to reconstruct in order
        routed_documents.sort(key=lambda x: x.get("start_page", 0))
        
        vault_dir = state_dir / "vault"
        output_pdf_path = target_dir / f"{house_id}.pdf"
        
        reconstructed_pdf = fitz.open()
        
        for doc in routed_documents:
            vault_id = doc.get("vault_id")
            if not vault_id:
                logger.error(f"Document missing vault_id for pages {doc.get('start_page')}-{doc.get('end_page')}")
                reconstructed_pdf.close()
                return 1
                
            vault_pdf_path = vault_dir / f"doc_{vault_id}.pdf"
            if not vault_pdf_path.exists():
                logger.error(f"Vault PDF not found: {vault_pdf_path}")
                reconstructed_pdf.close()
                return 1
                
            try:
                with fitz.open(str(vault_pdf_path)) as vault_doc:
                    reconstructed_pdf.insert_pdf(vault_doc)
            except Exception as e:
                logger.error(f"Failed to read vault PDF {vault_pdf_path}: {e}")
                reconstructed_pdf.close()
                return 1
                
        try:
            reconstructed_pdf.save(str(output_pdf_path))
        finally:
            reconstructed_pdf.close()
            
        import tempfile
        
        # Collect files to preserve before wiping
        temp_dir = Path(tempfile.mkdtemp())
        preserved = []
        try:
            for search_dir in [target_dir, state_dir]:
                if not search_dir.exists():
                    continue
                for item in search_dir.iterdir():
                    if item.is_file():
                        name = item.name.lower()
                        if ("raw_dump" in name) or ("report" in name and name.endswith(".json")) or ("tenant" in name and name.endswith(".yaml")) or ("categorization" in name and name.endswith(".json")):
                            dest = temp_dir / item.name
                            shutil.copy2(item, dest)
                            preserved.append(item.name)

            # Wipe out everything except the newly created reconstructed PDF
            for item in target_dir.iterdir():
                if item.resolve() == output_pdf_path.resolve():
                    continue
                    
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {item}: {e}")
                    
            # Restore preserved files into .source_files/
            if preserved:
                new_state_dir = target_dir / ".source_files"
                new_state_dir.mkdir(exist_ok=True)
                for fname in set(preserved):
                    shutil.copy2(temp_dir / fname, new_state_dir / fname)
                    
            logger.info(f"Successfully reconstructed {output_pdf_path.name} and cleaned up {target_dir.name} (preserved {len(set(preserved))} files)")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        return 0
        
    except Exception as e:
        logger.exception(f"Undo failed: {e}")
        return 1
