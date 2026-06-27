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

    def organize(self, documents: list[DocumentGroup], source_pdf: str, output_base_dir: Path) -> dict[str, tuple[int, int]]:
        """Organize the extracted documents into a structured directory hierarchy.
        
        Creates directories based on the house number, residents, and document categories,
        and saves compressed PDF segments to their respective locations.
        
        Args:
            documents (list[DocumentGroup]): The grouped documents from the pipeline.
            source_pdf (str): Path to the source PDF.
            output_base_dir (Path): The root output directory.
            
        Returns:
            dict[str, tuple[int, int]]: A mapping of output file paths to their page ranges.
        """
        if not documents:
            logger.warning("⚠ No documents to organize. Exiting.")
            return {}

        house_number = self._resolve_house_number(source_pdf)
        house_dir = output_base_dir / house_number
        
        if house_dir.exists():
            shutil.rmtree(house_dir)
            
        # Phase B - Create ALL directories
        os.makedirs(house_dir, exist_ok=True)
        
        # Copy the original full PDF file for reference
        try:
            full_file_dest = house_dir / f"{house_number}.pdf"
            compress_pdf(str(source_pdf), str(full_file_dest))
            logger.info(f"  → Copied and compressed full original file to: {full_file_dest.name}")
        except Exception as e:
            logger.error(f"⚠ Could not copy original PDF: {e}")
        
        resident_order = self._build_resident_order(documents)
        tenant_suffixes = self._compute_tenant_timelines(documents)
        resident_folder_map: dict[str, Path] = {}
        
        for index, name in resident_order:
            sanitized_name = utils.sanitize_filename(name)
            suffix = tenant_suffixes.get(name, "")
            sanitized_suffix = utils.sanitize_filename(suffix)
            folder_name = f"{index}_{sanitized_name}{sanitized_suffix}"
            
            resident_dir = house_dir / folder_name
            os.makedirs(resident_dir, exist_ok=True)
            resident_folder_map[name] = resident_dir
            
        amar_takhsees_dir = house_dir / "أمر التخصيص لغير المقيمين"
        house_letters_dir = house_dir / "رسائل عامة"

        # Phase C - Write PDFs
        summary: dict[str, tuple[int, int]] = {}
        # directory path -> set of used names
        used_names_per_dir: dict[str, set[str]] = defaultdict(set)
        # tenant -> category -> counter
        tenant_category_counters: dict[str, dict[Category, int]] = defaultdict(lambda: defaultdict(int))
        
        for doc in documents:
            tenant = doc.primary_tenant
            target_dir: Optional[Path] = None
            is_global_amar = False
            
            # Check if this tenant is a verified resident (i.e. has a folder)
            doc_resident_dir: Optional[Path] = None
            if tenant and tenant.strip() and tenant.upper() not in ("UNKNOWN", "NONE"):
                doc_resident_dir = resident_folder_map.get(tenant)
            
            if doc.category == Category.AMAR_TAKHSEES:
                if doc_resident_dir:
                    # Tenant is verified (has other documents), put in their personal amar_takhsees folder
                    target_dir = doc_resident_dir / CATEGORY_FOLDERS[doc.category]
                else:
                    # Tenant never moved in (no other docs) or no tenant found, route to global amar takhsees folder
                    target_dir = amar_takhsees_dir
                    is_global_amar = True
            elif not doc_resident_dir:
                # No valid tenant found or tenant didn't qualify for a folder
                if tenant and tenant.upper() == "UNKNOWN":
                    target_dir = house_dir / "UNKNOWN"
                else:
                    target_dir = house_letters_dir
            else:
                target_dir = doc_resident_dir / CATEGORY_FOLDERS[doc.category]

            tenant_category_counters[tenant][doc.category] += 1
            counter = tenant_category_counters[tenant][doc.category]
            
            filename = self._generate_pdf_name(doc, counter, used_names_per_dir[str(target_dir)], is_global_amar)
            used_names_per_dir[str(target_dir)].add(filename)
            
            target_path = target_dir / filename
            os.makedirs(target_dir, exist_ok=True)
            extract_pdf_segment(str(source_pdf), doc.start_page, doc.end_page, str(target_path))
            logger.info(f"  → {filename} (pages {doc.start_page}-{doc.end_page})")
            
            summary[str(target_path)] = (doc.start_page, doc.end_page)
            
        logger.info(f"✓ Generated {len(summary)} PDFs across {len(resident_order)} residents in {house_dir}")
        return summary
