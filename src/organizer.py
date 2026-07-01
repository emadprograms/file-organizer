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

from src.schemas import Category, DocumentGroup
from src.split import extract_pdf_segment, compress_pdf
import src.utils as utils

CATEGORY_FOLDERS = {
    Category.BASIC_DETAILS: "01_البيانات الاساسية",
    Category.PERSONAL_DETAILS: "02_بيانات المنتفع",
    Category.AMAR_TAKHSEES: "03_أمر التخصيص",
    Category.KEY_HANDOVER: "04_استمارات تسليم مفاتيح الوحدة",
    Category.CONTRACT: "05_عقد الانتفاع",
    Category.EWA_LETTERS: "06_مراسلات الكهرباء و الجهاز المركزي",
    Category.RENT_DEDUCTION: "07_الاستقطاعات",
    Category.ALLOWANCE_DEDUCTION: "08_وقف علاوة السكن",
    Category.NOTIFICATIONS: "09_الاشعارات",
    Category.MAINTENANCE: "10_طلبات وتقارير الصيانه",
    Category.INSPECTION_PICTURES: "11_تقارير التفتيش والصور",
    Category.MODIFICATIONS: "12_طلب الاضافة",
    Category.OTHER_LETTERS: "13_أخرى",
}

class FileOrganizer:
    """Organizer responsible for writing documents to disk in a structured hierarchy."""
    
    def _resolve_house_number(self, source_pdf: Union[str, Path]) -> str:
        """Extract the house number from the source PDF filename.
        
        Args:
            source_pdf (Union[str, Path]): Path to the original PDF.
            
        Returns:
            str: The extracted house number or 'unknown_house' if not found.
        """
        filename = Path(source_pdf).name
        match = re.search(r'\d+', filename)
        if match:
            return match.group(0)
        return "unknown_house"

    def _compute_tenant_timelines(self, documents: list[DocumentGroup]) -> dict[str, str]:
        """Compute the residency timeline for each tenant.
        
        Args:
            documents (list[DocumentGroup]): The grouped documents.
            
        Returns:
            dict[str, str]: A mapping of tenant names to their chronological suffix.
        """
        tenant_dates: dict[str, list[str]] = defaultdict(list)
        
        for doc in documents:
            tenant = doc.primary_tenant
            if not tenant or tenant.upper() in ("UNKNOWN", "NONE"):
                continue
            for d_str in doc.dates:
                if d_str and d_str != "NONE":
                    # Parse YYYY-MM from YYYY-MM-DD
                    if len(d_str) >= 7 and d_str[:4].isdigit() and d_str[5:7].isdigit():
                        tenant_dates[tenant].append(d_str[:7])
                        
        if not tenant_dates:
            return {}
            
        tenant_ranges: dict[str, tuple[str, str]] = {}
        for tenant, dates in tenant_dates.items():
            if dates:
                tenant_ranges[tenant] = (min(dates), max(dates))
                
        if not tenant_ranges:
            return {}
            
        # Find the max end_date across ALL tenants to determine the "Current Resident"
        global_max_date = max(end for start, end in tenant_ranges.values())
        
        result: dict[str, str] = {}
        for tenant, (start, end) in tenant_ranges.items():
            if end == global_max_date:
                suffix = f" ({start} to {end}) - الساكن الحالي"
            else:
                suffix = f" ({start} to {end})"
            result[tenant] = suffix
            
        return result

    def _build_resident_order(self, documents: list[DocumentGroup]) -> list[tuple[int, str]]:
        """Determine the chronological order of residents for folder numbering.
        
        Args:
            documents (list[DocumentGroup]): The grouped documents.
            
        Returns:
            list[tuple[int, str]]: A list of tuples containing the resident index and name.
        """
        seen_tenants: set[str] = set()
        ordered_tenants: list[tuple[int, str]] = []
        
        # Collect all tenants and what categories they have
        tenant_categories: dict[str, set[Category]] = defaultdict(set)
        for doc in documents:
            tenant = doc.primary_tenant
            if not tenant or not tenant.strip() or tenant.upper() in ("UNKNOWN", "NONE"):
                continue
            tenant_categories[tenant].add(doc.category)

        index = 1
        for doc in documents:
            tenant = doc.primary_tenant
            if not tenant or not tenant.strip() or tenant.upper() in ("UNKNOWN", "NONE"):
                continue
            
            if tenant in seen_tenants:
                continue
                
            # Skip if ONLY amar takhsees
            cats = tenant_categories[tenant]
            if len(cats) == 1 and Category.AMAR_TAKHSEES in cats:
                continue
                
            ordered_tenants.append((index, tenant))
            seen_tenants.add(tenant)
            index += 1
            
        return ordered_tenants

    def _generate_pdf_name(self, doc: DocumentGroup, category_counter: int, used_names: set[str], is_global_amar: bool = False) -> str:
        """Generate a unique filename for a document segment.
        
        Args:
            doc (DocumentGroup): The document group being written.
            category_counter (int): The current count for this category and tenant.
            used_names (set[str]): A set of already assigned filenames in the target directory.
            is_global_amar (bool): Whether the document goes to the global allocation folder. Defaults to False.
            
        Returns:
            str: A unique sanitized filename.
        """
        category_name = doc.category.name.lower()
        
        tenant_str = ""
        if is_global_amar and doc.primary_tenant and doc.primary_tenant not in ("UNKNOWN", "NONE"):
            sanitized_tenant = utils.sanitize_filename(doc.primary_tenant)
            tenant_str = f"_{sanitized_tenant}"

        if doc.dates:
            normalized_date = utils.normalize_date(doc.dates[0])
            base_name = f"{normalized_date}_{category_name}{tenant_str}.pdf"
        else:
            base_name = f"{category_name}{tenant_str}_{category_counter}.pdf"
            
        base_name = utils.sanitize_filename(base_name)
        
        if base_name not in used_names:
            return base_name
            
        name_without_ext = base_name[:-4] if base_name.endswith(".pdf") else base_name
        counter = 2
        while True:
            new_name = f"{name_without_ext}_{counter}.pdf"
            if new_name not in used_names:
                return new_name
            counter += 1

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
            if not routing_cfg.script_path:
                raise ValueError("Python routing strategy requires a script_path in config.")
            import importlib.util
            spec = importlib.util.spec_from_file_location("routing_script", routing_cfg.script_path)
            if spec and spec.loader:
                routing_script = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(routing_script)
                if hasattr(routing_script, "organize"):
                    return routing_script.organize(documents, source_pdf, output_base_dir)
                else:
                    raise ValueError("Python routing script must define an 'organize(documents, source_pdf, output_base_dir)' function.")
            else:
                raise ValueError(f"Could not load python script: {routing_cfg.script_path}")
        elif routing_cfg.strategy == "template":
            summary: dict[str, tuple[int, int]] = {}
            used_names_per_dir: dict[str, set[str]] = defaultdict(set)
            
            for doc in documents:
                tenant = doc.primary_tenant
                if not tenant or tenant.strip().upper() in ("UNKNOWN", "NONE"):
                    relative_dir = routing_cfg.fallback_folder
                else:
                    category_name = doc.category.name if hasattr(doc.category, 'name') else str(doc.category)
                    date_val = doc.dates[0] if doc.dates and doc.dates[0] != "NONE" else "UNKNOWN_DATE"
                    
                    # Sanitize variables for path formatting
                    sanitized_tenant = utils.sanitize_filename(tenant)
                    
                    try:
                        relative_dir = routing_cfg.destination_format.format(
                            primary_tenant=sanitized_tenant,
                            category=category_name,
                            date=date_val
                        )
                    except KeyError as e:
                        logger.error(f"Missing key in destination_format: {e}")
                        relative_dir = routing_cfg.fallback_folder
                
                target_dir = output_base_dir / relative_dir
                os.makedirs(target_dir, exist_ok=True)
                
                # Generate a simple filename based on category, date, tenant
                cat_str = doc.category.name.lower() if hasattr(doc.category, 'name') else str(doc.category).lower()
                tenant_str = utils.sanitize_filename(tenant) if tenant and tenant.strip().upper() not in ("UNKNOWN", "NONE") else "unknown"
                date_str = utils.normalize_date(doc.dates[0]) if doc.dates and doc.dates[0] != "NONE" else "nodate"
                
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
