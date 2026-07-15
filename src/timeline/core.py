"""File organization and PDF segmentation.

This module translates logically grouped documents into a structured
filesystem hierarchy based on house numbers, residents, and categories.
"""
import logging
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Any

from src.core.schemas import DocumentGroup
from src.pdf import extract_pdf_segment
import src.core.utils as utils

logger = logging.getLogger(f"file_organizer.{__name__}")

class FileOrganizer:
    """Organizer responsible for writing documents to disk in a structured hierarchy."""

    def compute_tenant_folders(self, documents: list[DocumentGroup], yaml_data: list[dict] = None) -> tuple[dict[str, str], str]:
        """Compute the tenant folder names based on document dates or yaml data."""
        tenant_years: dict[str, set[Any]] = defaultdict(set)
        for doc in documents:
            tenant = doc.primary_tenant
            if not tenant:
                tenant = "Unassigned"
            if tenant.startswith("Unassigned") or tenant.startswith("غير محدد"):
                group_tenant = "Unassigned"
            else:
                group_tenant = tenant
            
            tenant_years[group_tenant]
            
            for d in doc.dates:
                if d and d != "NONE":
                    if group_tenant == "Unassigned":
                        ym_match = re.search(r'(\d{4}-\d{2})', d.strip())
                        if ym_match:
                            tenant_years[group_tenant].add(ym_match.group(1))
                    else:
                        year_match = re.search(r'(\d{4})', d.strip())
                        if year_match:
                            tenant_years[group_tenant].add(int(year_match.group(1)))

        yaml_tenant_map = {t['name']: t for t in yaml_data} if yaml_data else {}
        
        latest_tenant = None
        
        if yaml_tenant_map:
            for t_name, t_info in yaml_tenant_map.items():
                if t_info.get("end_date") == "present":
                    latest_tenant = t_name
                    break
                    
        if not latest_tenant:
            global_max_year = -1
            
            for tenant, years in tenant_years.items():
                if tenant != "Unassigned" and years:
                    try:
                        max_yr = max(int(y) for y in years)
                        if max_yr > global_max_year:
                            global_max_year = max_yr
                            latest_tenant = tenant
                    except ValueError:
                        pass

        tenant_folder_names = {}
        for tenant, years in tenant_years.items():
            if tenant == "Unassigned":
                if years:
                    min_val = min(years)
                    max_val = max(years)
                    tenant_folder_names[tenant] = f"غير مخصص (فترة مستنتجة) {min_val} to {max_val}"
                else:
                    tenant_folder_names[tenant] = "غير مخصص"
            else:
                safe_name = utils.sanitize_filename(tenant)
                if tenant in yaml_tenant_map:
                    t_info = yaml_tenant_map[tenant]
                    # Format: start_year-end_year
                    start_yr = t_info.get("start_date", "").split("-")[0] if t_info.get("start_date") else (min(years) if years else "unknown")
                    end_yr = t_info.get("end_date", "present")
                    if end_yr != "present":
                        end_yr = end_yr.split("-")[0]
                    tenant_folder_names[tenant] = f"{safe_name} {start_yr}-{end_yr}"
                else:
                    # Fallback if tenant not in yaml
                    if years:
                        min_val = min(years)
                        max_val = max(years)
                        tenant_folder_names[tenant] = f"{safe_name} {min_val}-{max_val}"
                    else:
                        tenant_folder_names[tenant] = f"{safe_name}"
                    
        return tenant_folder_names, latest_tenant

    def ensure_target_directories(self, target_dir: Path, tenant_folder_names: dict[str, str], full_house_id: str, output_base_dir: Path) -> Path:
        """Create target directories for organization."""
        house_dir = output_base_dir / full_house_id
        
        # Rename target_dir if it's different from house_dir
        if target_dir != house_dir and target_dir.exists():
            if not house_dir.exists():
                try:
                    target_dir.rename(house_dir)
                    logger.info(f"Renamed {target_dir.name} to {house_dir.name}")
                except Exception as e:
                    logger.warning(f"Could not rename {target_dir} to {house_dir}: {e}")
                    house_dir.mkdir(parents=True, exist_ok=True)
            else:
                house_dir.mkdir(parents=True, exist_ok=True)
        else:
            house_dir.mkdir(parents=True, exist_ok=True)

        from src.routing.config import FOLDER_ROUTING, FOLDER_PREFIXES
        for folder_name in tenant_folder_names.values():
            for topic in FOLDER_ROUTING.keys():
                prefix = FOLDER_PREFIXES.get(topic, "")
                topic_folder_name = f"{prefix}_{topic}" if prefix else topic
                target_subdir = (house_dir / folder_name / topic_folder_name).resolve()
                if str(target_subdir).startswith(str(output_base_dir.resolve())):
                    os.makedirs(target_subdir, exist_ok=True)
        return house_dir

    def process_documents(self, documents: list[DocumentGroup], source_pdf: str, house_id: str, output_base_dir: Path, tenant_folder_names: dict[str, str], dry_run: bool = False) -> list[dict]:
        """Extract and save document segments."""
        per_page = []
        used_names_per_dir: dict[str, set[str]] = defaultdict(set)
        tree_data = defaultdict(lambda: defaultdict(list))
        
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
            
            from src.routing.config import FOLDER_PREFIXES
            raw_topic_folder = doc.folder_path if doc.folder_path else "رسائل متنوعة"
            prefix = FOLDER_PREFIXES.get(raw_topic_folder, "")
            topic_folder = f"{prefix}_{raw_topic_folder}" if prefix else raw_topic_folder
            
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
                logger.info(f"  → {filename} (pages {doc.start_page + 1}-{doc.end_page + 1})")
            else:
                tree_data[tenant_folder][topic_folder].append(f"{filename} (pages {doc.start_page + 1}-{doc.end_page + 1})")
            
            relative_path = target_path.relative_to(output_base_dir.resolve()).as_posix()
            
            page_in_output = 1
            for page_index in range(doc.start_page, doc.end_page + 1):
                doc_date = doc.dates[page_index - doc.start_page] if doc.dates and len(doc.dates) > (page_index - doc.start_page) else "NONE"
                per_page.append({
                    "page_index": page_index,
                    "tenant": doc.primary_tenant,
                    "date": doc_date,
                    "output_file": relative_path,
                    "page_in_output": page_in_output,
                    "target_folder": f"{tenant_folder}/{topic_folder}"
                })
                page_in_output += 1
            
        if dry_run:
            from rich.tree import Tree
            from src.core.ui import vprint
            tree = Tree(f"[bold blue]{house_id}[/bold blue]")
            for t_folder, topics in tree_data.items():
                t_node = tree.add(f"[bold green]{t_folder}[/bold green]")
                for topic, files in topics.items():
                    topic_node = t_node.add(f"[bold yellow]{topic}[/bold yellow]")
                    for f in files:
                        topic_node.add(f)
            vprint(tree)
            
        return per_page

    def ensure_target_directories(self, target_dir: Path, tenant_folder_names: dict[str, str], full_house_id: str, output_base_dir: Path) -> Path:
        """Create target directories for organization."""
        house_dir = output_base_dir / full_house_id
        
        # Rename target_dir if it's different from house_dir
        if target_dir != house_dir and target_dir.exists():
            if not house_dir.exists():
                try:
                    target_dir.rename(house_dir)
                    logger.info(f"Renamed {target_dir.name} to {house_dir.name}")
                except Exception as e:
                    logger.warning(f"Could not rename {target_dir} to {house_dir}: {e}")
                    house_dir.mkdir(parents=True, exist_ok=True)
            else:
                house_dir.mkdir(parents=True, exist_ok=True)
        else:
            house_dir.mkdir(parents=True, exist_ok=True)

        from src.routing.config import FOLDER_ROUTING, FOLDER_PREFIXES
        for folder_name in tenant_folder_names.values():
            for topic in FOLDER_ROUTING.keys():
                prefix = FOLDER_PREFIXES.get(topic, "")
                topic_folder_name = f"{prefix}_{topic}" if prefix else topic
                target_subdir = (house_dir / folder_name / topic_folder_name).resolve()
                if str(target_subdir).startswith(str(output_base_dir.resolve())):
                    os.makedirs(target_subdir, exist_ok=True)
        return house_dir

    def process_documents(self, documents: list[DocumentGroup], source_pdf: str, house_id: str, output_base_dir: Path, tenant_folder_names: dict[str, str], dry_run: bool = False) -> list[dict]:
        """Extract and save document segments."""
        per_page = []
        used_names_per_dir: dict[str, set[str]] = defaultdict(set)
        tree_data = defaultdict(lambda: defaultdict(list))
        
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
            
            from src.routing.config import FOLDER_PREFIXES
            raw_topic_folder = doc.folder_path if doc.folder_path else "رسائل متنوعة"
            prefix = FOLDER_PREFIXES.get(raw_topic_folder, "")
            topic_folder = f"{prefix}_{raw_topic_folder}" if prefix else raw_topic_folder
            
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
                logger.info(f"  → {filename} (pages {doc.start_page + 1}-{doc.end_page + 1})")
            else:
                tree_data[tenant_folder][topic_folder].append(f"{filename} (pages {doc.start_page + 1}-{doc.end_page + 1})")
            
            relative_path = target_path.relative_to(output_base_dir.resolve()).as_posix()
            
            page_in_output = 1
            for page_index in range(doc.start_page, doc.end_page + 1):
                doc_date = doc.dates[page_index - doc.start_page] if doc.dates and len(doc.dates) > (page_index - doc.start_page) else "NONE"
                per_page.append({
                    "page_index": page_index,
                    "tenant": doc.primary_tenant,
                    "date": doc_date,
                    "output_file": relative_path,
                    "page_in_output": page_in_output,
                    "target_folder": f"{tenant_folder}/{topic_folder}"
                })
                page_in_output += 1
            
        if dry_run:
            from rich.tree import Tree
            from src.core.ui import vprint
            tree = Tree(f"[bold blue]{house_id}[/bold blue]")
            for t_folder, topics in tree_data.items():
                t_node = tree.add(f"[bold green]{t_folder}[/bold green]")
                for topic, files in topics.items():
                    topic_node = t_node.add(f"[bold yellow]{topic}[/bold yellow]")
                    for f in files:
                        topic_node.add(f)
            vprint(tree)
            
        return per_page

    def organize(self, documents: list[DocumentGroup], source_pdf: str, house_id: str, output_base_dir: Path, yaml_data: list[dict] = None, dry_run: bool = False) -> tuple[list[dict], str]:
        """Organize the extracted documents into a structured directory hierarchy."""
        if not documents:
            logger.warning("⚠ No documents to organize. Exiting.")
            return []

        target_dir = Path(source_pdf).parent

        tenant_folder_names, latest_tenant = self.compute_tenant_folders(documents, yaml_data)
        
        from src.utils.logger import log_decision_trace
        log_decision_trace("tenant_resolution", {"tenant_folders": tenant_folder_names})
        logger.info(f"Tenant resolution complete. Folders: {tenant_folder_names}")

        if latest_tenant:
            full_house_id = f"{house_id} - {utils.sanitize_filename(latest_tenant)}"
        else:
            full_house_id = house_id

        if not dry_run:
            # Create directories
            house_dir = self.ensure_target_directories(target_dir, tenant_folder_names, full_house_id, output_base_dir)

        per_page = self.process_documents(documents, source_pdf, full_house_id, output_base_dir, tenant_folder_names, dry_run)
        return per_page, full_house_id
