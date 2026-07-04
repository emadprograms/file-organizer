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

        summary: dict[str, tuple[int, int]] = {}
        used_names_per_dir: dict[str, set[str]] = defaultdict(set)
        
        for doc in documents:
            tenant = doc.primary_tenant
            tenant_str = utils.sanitize_filename(tenant) if tenant and tenant.strip().upper() not in ("UNKNOWN", "NONE") else "unknown"
            
            if doc.folder_path:
                relative_dir = f"{doc.folder_path}/{tenant_str}"
            else:
                relative_dir = f"13_others/{tenant_str}"
                
            target_dir = output_base_dir / relative_dir
            os.makedirs(target_dir, exist_ok=True)
            
            date_str = "nodate"
            if doc.dates and len(doc.dates) > 0 and doc.dates[0] and doc.dates[0] != "NONE":
                date_str = utils.normalize_date(doc.dates[0])
            
            if doc.is_direct_routed:
                base_name = utils.sanitize_filename(f"{date_str}.pdf")
            else:
                base_name = utils.sanitize_filename(f"{date_str} - {doc.brief_arabic_title}.pdf")
            
            if base_name not in used_names_per_dir[str(target_dir)] and not (target_dir / base_name).exists():
                filename = base_name
            else:
                counter = 2
                name_without_ext = base_name[:-4] if base_name.endswith(".pdf") else base_name
                while True:
                    new_name = f"{name_without_ext}_{counter}.pdf"
                    if new_name not in used_names_per_dir[str(target_dir)] and not (target_dir / new_name).exists():
                        filename = new_name
                        break
                    counter += 1
                    
            used_names_per_dir[str(target_dir)].add(filename)
            target_path = target_dir / filename
            
            extract_pdf_segment(str(source_pdf), doc.start_page, doc.end_page, str(target_path))
            logger.info(f"  → {filename} (pages {doc.start_page}-{doc.end_page})")
            
            summary[str(target_path)] = (doc.start_page, doc.end_page)
            
        return summary
