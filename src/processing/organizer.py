"""File organization and PDF segmentation.

This module translates logically grouped documents into a structured
filesystem hierarchy based on house numbers, residents, and categories.
"""
import logging
import os
import shutil
import re
logger = logging.getLogger(__name__)
from pathlib import Path
from collections import defaultdict
from typing import Union, Optional, Any, Set

from src.core.schemas import DocumentGroup
from src.processing.split import extract_pdf_segment, compress_pdf
import src.core.utils as utils

class FileOrganizer:
    """Organizer responsible for writing documents to disk in a structured hierarchy."""

    def organize(self, documents: list[DocumentGroup], source_pdf: str, output_base_dir: Path, config: 'UserConfig') -> dict[str, tuple[int, int]]:
        """Organize the extracted documents into a structured directory hierarchy.
        
        Args:
            documents (list[DocumentGroup]): The grouped documents from the pipeline.
            source_pdf (str): Path to the source PDF.
            output_base_dir (Path): The root output directory.
            config (UserConfig): User configuration containing routing rules.
            
        Returns:
            dict[str, tuple[int, int]]: A mapping of output file paths to their page ranges.
        """
        if not documents:
            logger.warning("⚠ No documents to organize. Exiting.")
            return {}

        routing_cfg = config.routing
        if routing_cfg.strategy == "python":
            try:
                if not routing_cfg.script_path:
                    raise ValueError("Python routing strategy requires a script_path in config.")
                
                script_path = Path(routing_cfg.script_path).resolve()
                if not script_path.is_relative_to(Path.cwd()):
                    raise PermissionError(f"Script path {script_path} is outside the allowed directory.")

                import importlib.util
                spec = importlib.util.spec_from_file_location("routing_script", str(script_path))
                if spec and spec.loader:
                    routing_script = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(routing_script)
                    if hasattr(routing_script, "organize"):
                        return routing_script.organize(documents, source_pdf, output_base_dir)
                    else:
                        raise ValueError("Python routing script must define an 'organize(documents, source_pdf, output_base_dir)' function.")
                else:
                    raise ValueError(f"Could not load python script: {routing_cfg.script_path}")
            except Exception as e:
                logger.error(f"Routing script failed: {e}")
                raise
                
        # Declarative Strategy (Fallback or explicit)
        if routing_cfg.strategy == "declarative" or routing_cfg.strategy == "template":
            summary: dict[str, tuple[int, int]] = {}
            used_names_per_dir: dict[str, set[str]] = defaultdict(set)
            
            for doc in documents:
                tenant = doc.primary_tenant
                category_name = str(doc.category)
                
                if not tenant or tenant.strip().upper() in ("UNKNOWN", "NONE"):
                    relative_dir = routing_cfg.fallback_folder
                elif category_name in routing_cfg.rules:
                    sanitized_tenant = utils.sanitize_filename(tenant)
                    relative_dir = f"{routing_cfg.rules[category_name]}/{sanitized_tenant}"
                else:
                    relative_dir = routing_cfg.fallback_folder
                    
                target_dir = output_base_dir / relative_dir
                os.makedirs(target_dir, exist_ok=True)
                
                date_str = utils.normalize_date(doc.dates[0]) if doc.dates and doc.dates[0] != "NONE" else "nodate"
                tenant_str = utils.sanitize_filename(tenant) if tenant and tenant.strip().upper() not in ("UNKNOWN", "NONE") else "unknown"
                cat_str = category_name.lower()
                
                base_name = utils.sanitize_filename(f"{date_str}_{cat_str}_{tenant_str}.pdf")
                
                if base_name not in used_names_per_dir[str(target_dir)]:
                    filename = base_name
                else:
                    counter = 2
                    name_without_ext = base_name[:-4] if base_name.endswith(".pdf") else base_name
                    while True:
                        new_name = f"{name_without_ext}_{counter}.pdf"
                        if new_name not in used_names_per_dir[str(target_dir)]:
                            filename = new_name
                            break
                        counter += 1
                        
                used_names_per_dir[str(target_dir)].add(filename)
                target_path = target_dir / filename
                
                extract_pdf_segment(str(source_pdf), doc.start_page, doc.end_page, str(target_path))
                logger.info(f"  → {filename} (pages {doc.start_page}-{doc.end_page})")
                
                summary[str(target_path)] = (doc.start_page, doc.end_page)
                
            return summary
        else:
            raise ValueError(f"Unknown routing strategy: {routing_cfg.strategy}")
