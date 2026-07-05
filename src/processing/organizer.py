"""File organization and PDF segmentation.

This module translates logically grouped documents into a structured
filesystem hierarchy based on house numbers, residents, and categories.
"""
import logging
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Any

from src.core.schemas import DocumentGroup
from src.processing.split import extract_pdf_segment
import src.core.utils as utils

logger = logging.getLogger(__name__)

class FileOrganizer:
    """Organizer responsible for writing documents to disk in a structured hierarchy."""

    def organize(self, documents: list[DocumentGroup], source_pdf: str, house_id: str, output_base_dir: Path, config: Any = None, dry_run: bool = False) -> list[dict]:
        """Organize the extracted documents into a structured directory hierarchy.
        
        Args:
            documents (list[DocumentGroup]): The grouped documents from the pipeline.
            source_pdf (str): Path to the source PDF.
            house_id (str): The house ID to set the house-level root dir.
            output_base_dir (Path): The root output directory.
            config: User configuration (unused here).
            
        Returns:
            list[dict]: A per-page mapping of page_index to relative output_file.
        """
        if not documents:
            logger.warning("⚠ No documents to organize. Exiting.")
            return []

        # 1. Aggregation pass to compute (min_year, max_year) per tenant
        tenant_years: dict[str, set[int]] = defaultdict(set)
        for doc in documents:
            tenant = doc.primary_tenant
            if not tenant:
                tenant = "Unassigned"
            if tenant.startswith("Unassigned") or tenant.startswith("غير محدد"):
                group_tenant = "Unassigned"
            else:
                group_tenant = tenant
            
            # Ensure the group_tenant exists in the dictionary even if it has no dates
            tenant_years[group_tenant]
            
            for d in doc.dates:
                if d and d != "NONE":
                    year_match = re.search(r'(\d{4})', d.strip())
                    if year_match:
                        tenant_years[group_tenant].add(int(year_match.group(1)))

        # 2. Build tenant folder names
        tenant_folder_names = {}
        for tenant, years in tenant_years.items():
            if years:
                min_year = min(years)
                max_year = max(years)
                if tenant == "Unassigned":
                    tenant_folder_names[tenant] = f"غير مخصص (فترة مستنتجة) {min_year}-{max_year}"
                else:
                    safe_name = utils.sanitize_filename(tenant)
                    tenant_folder_names[tenant] = f"{safe_name} {min_year}-{max_year}"
            else:
                if tenant == "Unassigned":
                    tenant_folder_names[tenant] = "غير مخصص"
                else:
                    safe_name = utils.sanitize_filename(tenant)
                    tenant_folder_names[tenant] = f"{safe_name}"

        # Proactively create all 13 subdirectories for each tenant
        if not dry_run:
            from src.processing.routing import FOLDER_ROUTING
            house_dir = output_base_dir / house_id
            for folder_name in tenant_folder_names.values():
                for topic in FOLDER_ROUTING.keys():
                    target_dir = (house_dir / folder_name / topic).resolve()
                    if str(target_dir).startswith(str(output_base_dir.resolve())):
                        os.makedirs(target_dir, exist_ok=True)

        per_page = []
        used_names_per_dir: dict[str, set[str]] = defaultdict(set)
        
        house_dir = output_base_dir / house_id
        
        for doc in documents:
            tenant = doc.primary_tenant
            if not tenant:
                tenant = "Unassigned"
            if tenant.startswith("Unassigned") or tenant.startswith("غير محدد"):
                group_tenant = "Unassigned"
            else:
                group_tenant = tenant
                
            tenant_folder = tenant_folder_names.get(group_tenant, utils.sanitize_filename(group_tenant))
            
            topic_folder = doc.folder_path if doc.folder_path else "13_others"
            
            target_dir = (house_dir / tenant_folder / topic_folder).resolve()
            if not str(target_dir).startswith(str(output_base_dir.resolve())):
                raise ValueError(f"Path traversal detected: {target_dir}")
                
            if not dry_run:
                os.makedirs(target_dir, exist_ok=True)
            
            date_str = "nodate"
            if doc.dates and len(doc.dates) > 0 and doc.dates[0] and doc.dates[0] != "NONE":
                date_str = utils.normalize_date(doc.dates[0])
            
            if doc.is_direct_routed:
                base_name = utils.sanitize_filename(f"{date_str}.pdf")
            else:
                title = doc.brief_arabic_title if doc.brief_arabic_title else "بدون عنوان"
                base_name = utils.sanitize_filename(f"{date_str} - {title}.pdf")
            
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
            
            if not dry_run:
                extract_pdf_segment(str(source_pdf), doc.start_page, doc.end_page, str(target_path))
                logger.info(f"  → {filename} (pages {doc.start_page}-{doc.end_page})")
            else:
                logger.info(f"  [DRY RUN] Would extract: {filename} (pages {doc.start_page}-{doc.end_page}) to {target_dir}")
            
            relative_path = target_path.relative_to(output_base_dir).as_posix()
            
            page_in_output = 1
            for page_index in range(doc.start_page, doc.end_page + 1):
                doc_date = doc.dates[page_index - doc.start_page] if doc.dates and len(doc.dates) > (page_index - doc.start_page) else "NONE"
                per_page.append({
                    "page_index": page_index,
                    "tenant": doc.primary_tenant,
                    "date": doc_date,
                    "output_file": relative_path,
                    "page_in_output": page_in_output
                })
                page_in_output += 1
            
        return per_page

def run_reconciliation(summary: dict, per_page: list, total_input_pages: int, house_id: str, output_dir: Path, dry_run: bool = False):
    """Write reconciliation manifest and assert page counts."""
    unaccounted_pages = []
    accounted_page_indices = {p["page_index"] for p in per_page}
    for i in range(total_input_pages):
        if i not in accounted_page_indices:
            unaccounted_pages.append(i)
            
    manifest = {
        "summary": {
            "house_id": house_id,
            "total_input_pages": total_input_pages,
            "total_output_pages": summary.get("total_output_pages", len(per_page)),
            "output_file_count": summary.get("output_file_count", len({p["output_file"] for p in per_page})),
            "unaccounted_pages": unaccounted_pages
        },
        "per_page": per_page
    }
    
    if not dry_run:
        from src.fs_utils import atomic_write
        manifest_path = output_dir / f"{house_id}_manifest.json"
        with atomic_write(str(manifest_path)) as tmp_path:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
    else:
        logger.info(f"  [DRY RUN] Would write manifest to {output_dir / f'{house_id}_manifest.json'}")
    
    from rich.console import Console
    from rich.table import Table
    console = Console()
    table = Table(title="Reconciliation Report")
    table.add_column("House ID")
    table.add_column("Total Input Pages")
    table.add_column("Total Output Pages")
    table.add_column("Output File Count")
    table.add_column("Unaccounted Pages")
    table.add_row(
        str(manifest["summary"]["house_id"]),
        str(manifest["summary"]["total_input_pages"]),
        str(manifest["summary"]["total_output_pages"]),
        str(manifest["summary"]["output_file_count"]),
        str(len(manifest["summary"]["unaccounted_pages"]))
    )
    console.print(table)
    
    if total_input_pages != manifest["summary"]["total_output_pages"]:
        raise RuntimeError("Reconciliation failed: total input pages != total output pages")
