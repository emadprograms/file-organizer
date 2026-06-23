import os
import shutil
from pathlib import Path
from collections import Counter
from collections import defaultdict
import re

from src.schemas import Category, DocumentGroup
from src.split import extract_pdf_segment

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
    Category.PICTURES: "11_تقارير التفتيش",
    Category.MODIFICATIONS: "12_طلب الاضافة",
    Category.OTHER_LETTERS: "13_أخرى",
}

class FileOrganizer:
    def _resolve_house_number(self, source_pdf: str | Path) -> str:
        import re
        from pathlib import Path
        filename = Path(source_pdf).name
        match = re.search(r'\d+', filename)
        if match:
            return match.group(0)
        return "unknown_house"

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

    def _normalize_date(self, date_str: str) -> str:
        if not date_str or date_str.upper() == "NONE":
            return "NONE"
            
        import re
        
        # 1. Convert Eastern Arabic numerals to Western
        eastern_to_western = {
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
        }
        for e, w in eastern_to_western.items():
            date_str = date_str.replace(e, w)
            
        # 2. Clean up string
        date_str = date_str.strip()
        # Remove 'م' or 'هـ' at the end (sometimes separated by space)
        date_str = re.sub(r'\s*[مهـ]\s*$', '', date_str)
        # Remove days of the week
        date_str = re.sub(r'(?i)^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)[, ]+', '', date_str)
        date_str = date_str.strip()
        
        # 3. Handle Already YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
            
        # Helper for 2-digit years
        def fix_year(y: int) -> int:
            if y < 100:
                return y + 2000 if y < 50 else y + 1900
            return y

        # 4. Numeric formats
        # YYYY/MM/DD, YYYY-MM-DD, YYYY.MM.DD, YYYY MM DD
        m = re.match(r'^(\d{4})[./\-\s]+(\d{1,2})[./\-\s]+(\d{1,2})$', date_str)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            
        # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD MM YYYY (and YY versions)
        m = re.match(r'^(\d{1,2})[./\-\s]+(\d{1,2})[./\-\s]+(\d{2,4})$', date_str)
        if m:
            y = fix_year(int(m.group(3)))
            return f"{y}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

        # 5. Month name formats
        months = {
            "jan": "01", "january": "01", "يناير": "01", "جانفي": "01",
            "feb": "02", "february": "02", "فبراير": "02", "فيفري": "02",
            "mar": "03", "march": "03", "مارس": "03",
            "apr": "04", "april": "04", "أبريل": "04", "ابريل": "04", "افريل": "04",
            "may": "05", "مايو": "05", "ماي": "05",
            "jun": "06", "june": "06", "يونيو": "06", "جوان": "06",
            "jul": "07", "july": "07", "يوليو": "07", "جويلية": "07",
            "aug": "08", "august": "08", "أغسطس": "08", "اغسطس": "08", "اوت": "08", "أوت": "08",
            "sep": "09", "september": "09", "sept": "09", "سبتمبر": "09",
            "oct": "10", "october": "10", "أكتوبر": "10", "اكتوبر": "10",
            "nov": "11", "november": "11", "نوفمبر": "11",
            "dec": "12", "december": "12", "ديسمبر": "12"
        }
        
        # DD [Month] YYYY or DD-[Month]-YYYY (e.g. 09 DEC 2006, 02-JUL-08)
        m = re.search(r'^(\d{1,2})[\s\-]+([A-Za-z\u0600-\u06FF]+)[\s\-]+(\d{2,4})$', date_str)
        if m:
            d = int(m.group(1))
            mon = m.group(2).lower()
            y = fix_year(int(m.group(3)))
            if mon in months:
                return f"{y}-{months[mon]}-{d:02d}"

        # YYYY [Month] DD (e.g. 2010 ابريل 7)
        m = re.search(r'^(\d{4})[\s\-]+([A-Za-z\u0600-\u06FF]+)[\s\-]+(\d{1,2})$', date_str)
        if m:
            y = int(m.group(1))
            mon = m.group(2).lower()
            d = int(m.group(3))
            if mon in months:
                return f"{y}-{months[mon]}-{d:02d}"
                
        # [Month] YYYY (e.g. نوفمبر 2009)
        m = re.search(r'^([A-Za-z\u0600-\u06FF]+)[\s\-]+(\d{4})$', date_str)
        if m:
            mon = m.group(1).lower()
            y = int(m.group(2))
            if mon in months:
                return f"{y}-{months[mon]}-01"

        # Fallback sanitize
        return re.sub(r'[/\\:*?"<>|\s]', '-', date_str).strip('-')

    def _generate_pdf_name(self, doc: DocumentGroup, category_counter: int, used_names: set) -> str:
        category_value = doc.category.value
        if doc.dates:
            normalized_date = self._normalize_date(doc.dates[0])
            base_name = f"{normalized_date}_{category_value}.pdf"
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

        house_number = self._resolve_house_number(source_pdf)
        house_dir = output_base_dir / house_number
        
        if house_dir.exists():
            shutil.rmtree(house_dir)
            
        # Phase B - Create ALL directories
        os.makedirs(house_dir, exist_ok=True)
        
        # Copy the original full PDF file for reference
        try:
            full_file_dest = house_dir / f"{house_number}.pdf"
            shutil.copy2(source_pdf, full_file_dest)
            print(f"  → Copied full original file to: {full_file_dest.name}")
        except Exception as e:
            print(f"⚠ Could not copy original PDF: {e}")
        
        resident_order = self._build_resident_order(documents)
        resident_folder_map = {}
        
        for index, name in resident_order:
            sanitized_name = self._sanitize_filename(name)
            resident_dir = house_dir / f"{index}_{sanitized_name}"
            os.makedirs(resident_dir, exist_ok=True)
            resident_folder_map[name] = resident_dir
            
            for folder_name in CATEGORY_FOLDERS.values():
                pass # removed eager folder creation
                
        amar_takhsees_dir = house_dir / "أمر التخصيص لغير المقيمين"
        house_letters_dir = house_dir / "رسائل عامة"

        # Phase C - Write PDFs
        summary = {}
        # directory path -> set of used names
        used_names_per_dir = defaultdict(set)
        # tenant -> category -> counter
        tenant_category_counters = defaultdict(lambda: defaultdict(int))
        
        for doc in documents:
            tenant = doc.primary_tenant
            target_dir = None
            
            # Check if this tenant is a verified resident (i.e. has a folder)
            resident_dir = None
            if tenant and tenant.strip() and tenant.upper() not in ("UNKNOWN", "NONE"):
                resident_dir = resident_folder_map.get(tenant)
            
            if doc.category == Category.AMAR_TAKHSEES:
                if resident_dir:
                    # Tenant is verified (has other documents), put in their personal amar_takhsees folder
                    target_dir = resident_dir / CATEGORY_FOLDERS[doc.category]
                else:
                    # Tenant never moved in (no other docs) or no tenant found, route to global amar takhsees folder
                    target_dir = amar_takhsees_dir
            elif not resident_dir:
                # No valid tenant found or tenant didn't qualify for a folder
                if tenant and tenant.upper() == "UNKNOWN":
                    target_dir = house_dir / "UNKNOWN"
                else:
                    target_dir = house_letters_dir
            else:
                target_dir = resident_dir / CATEGORY_FOLDERS[doc.category]

            tenant_category_counters[tenant][doc.category] += 1
            counter = tenant_category_counters[tenant][doc.category]
            
            filename = self._generate_pdf_name(doc, counter, used_names_per_dir[str(target_dir)])
            used_names_per_dir[str(target_dir)].add(filename)
            
            target_path = target_dir / filename
            os.makedirs(target_dir, exist_ok=True)
            extract_pdf_segment(str(source_pdf), doc.start_page, doc.end_page, str(target_path))
            print(f"  → {filename} (pages {doc.start_page}-{doc.end_page})")
            
            summary[str(target_path)] = (doc.start_page, doc.end_page)
            
        print(f"✓ Generated {len(summary)} PDFs across {len(resident_order)} residents in {house_dir}")
        return summary
