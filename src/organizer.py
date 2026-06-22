import os
import shutil
from pathlib import Path
from collections import Counter
from collections import defaultdict
import re

from src.schemas import Category, DocumentGroup
from src.split import extract_pdf_segment

CATEGORY_FOLDERS = {
    Category.BASIC_DETAILS: "1_basic_details",
    Category.PERSONAL_DETAILS: "2_personal_details",
    Category.AMAR_TAKHSEES: "3_amar_takhsees",
    Category.KEY_HANDOVER: "4_key_handover_form",
    Category.CONTRACT: "5_contract",
    Category.EWA_LETTERS: "6_ewa_related_letters",
    Category.RENT_DEDUCTION: "7_rent_deduction",
    Category.ALLOWANCE_DEDUCTION: "8_allowance_deduction",
    Category.NOTIFICATIONS: "9_notifications",
    Category.MAINTENANCE: "10_maintenance",
    Category.PICTURES: "11_pictures",
    Category.MODIFICATIONS: "12_modifications",
    Category.OTHER_LETTERS: "13_other_letters",
}

class FileOrganizer:
    def _resolve_house_number(self, documents: list[DocumentGroup]) -> str:
        house_numbers = [doc.house_number for doc in documents if doc.house_number]
        if not house_numbers:
            return "unknown_house"
        
        counter = Counter(house_numbers)
        most_common = counter.most_common(1)[0][0]
        
        unique_numbers = set(house_numbers)
        if len(unique_numbers) > 1:
            print(f"⚠ Inconsistent house numbers detected: {list(unique_numbers)}. Using majority: {most_common}")
            
        return most_common

    def _build_resident_order(self, documents: list[DocumentGroup]) -> list[tuple[int, str]]:
        seen_tenants = set()
        ordered_tenants = []
        
        # Collect all tenants and what categories they have
        tenant_categories = defaultdict(set)
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

    def _sanitize_filename(self, name: str, max_length: int = 50) -> str:
        # Replace illegal characters with underscore
        sanitized = re.sub(r'[/\\:*?"<>|]', '_', name)
        sanitized = sanitized.strip()
        # Collapse multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Ensure truncation doesn't split a multi-byte UTF-8 character
        encoded = sanitized.encode('utf-8')
        if len(encoded) > max_length:
            # We truncate based on characters, not bytes to avoid splitting multi-byte characters
            sanitized = sanitized[:max_length]
            
        return sanitized

    def _generate_pdf_name(self, doc: DocumentGroup, category_counter: int, used_names: set) -> str:
        category_value = doc.category.value
        if doc.dates:
            base_name = f"{doc.dates[0]}_{category_value}.pdf"
        else:
            base_name = f"{category_value}_{category_counter}.pdf"
            
        base_name = self._sanitize_filename(base_name)
        
        if base_name not in used_names:
            return base_name
            
        name_without_ext = base_name[:-4] if base_name.endswith(".pdf") else base_name
        counter = 2
        while True:
            new_name = f"{name_without_ext}_{counter}.pdf"
            if new_name not in used_names:
                return new_name
            counter += 1

    def organize(self, documents: list[DocumentGroup], source_pdf: str, output_base_dir: Path) -> dict:
        if not documents:
            print("⚠ No documents to organize. Exiting.")
            return {}

        house_number = self._resolve_house_number(documents)
        house_dir = output_base_dir / house_number
        
        if house_dir.exists():
            shutil.rmtree(house_dir)
            
        # Phase B - Create ALL directories
        os.makedirs(house_dir, exist_ok=True)
        
        resident_order = self._build_resident_order(documents)
        resident_folder_map = {}
        
        for index, name in resident_order:
            sanitized_name = self._sanitize_filename(name)
            resident_dir = house_dir / f"{index}_{sanitized_name}"
            os.makedirs(resident_dir, exist_ok=True)
            resident_folder_map[name] = resident_dir
            
            for folder_name in CATEGORY_FOLDERS.values():
                os.makedirs(resident_dir / folder_name, exist_ok=True)
                
        amar_takhsees_dir = house_dir / "amar_takhsees"
        os.makedirs(amar_takhsees_dir, exist_ok=True)
        
        house_letters_dir = house_dir / "house_letters"
        os.makedirs(house_letters_dir, exist_ok=True)

        # Phase C - Write PDFs
        summary = {}
        # directory path -> set of used names
        used_names_per_dir = defaultdict(set)
        # tenant -> category -> counter
        tenant_category_counters = defaultdict(lambda: defaultdict(int))
        
        for doc in documents:
            tenant = doc.primary_tenant
            target_dir = None
            
            if doc.category == Category.AMAR_TAKHSEES:
                target_dir = amar_takhsees_dir
            elif not tenant or not tenant.strip() or tenant.upper() in ("UNKNOWN", "NONE"):
                target_dir = house_letters_dir
            else:
                resident_dir = resident_folder_map.get(tenant)
                if resident_dir:
                    target_dir = resident_dir / CATEGORY_FOLDERS[doc.category]
                else:
                    # Fallback if somehow resident was skipped
                    target_dir = house_letters_dir

            tenant_category_counters[tenant][doc.category] += 1
            counter = tenant_category_counters[tenant][doc.category]
            
            filename = self._generate_pdf_name(doc, counter, used_names_per_dir[str(target_dir)])
            used_names_per_dir[str(target_dir)].add(filename)
            
            target_path = target_dir / filename
            extract_pdf_segment(str(source_pdf), doc.start_page, doc.end_page, str(target_path))
            print(f"  → {filename} (pages {doc.start_page}-{doc.end_page})")
            
            summary[str(target_path)] = (doc.start_page, doc.end_page)
            
        print(f"✓ Generated {len(summary)} PDFs across {len(resident_order)} residents in {house_dir}")
        return summary
