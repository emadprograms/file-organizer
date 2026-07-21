import os
import time
import logging
import shutil
import json
from pathlib import Path
from typing import Any

from src.inbox.parser import parse_filename_syntax
from src.inbox.resolver import infer_missing_data, resolve_area, resolve_tenant, ConflictError, resolve_group_mode
from src.categorization.categorization import process_unclassified_pdf
from src.main import run_cleaning_pass, run_grouping_pass, run_routing_pass, run_generation_pass
from src.pipeline.pipeline import Pipeline
from src.core.schemas import DocumentGroup

logger = logging.getLogger(f"file_organizer.{__name__}")

class FSUIOrchestrator:
    def __init__(self, config: Any, llm_client: Any):
        self.config = config
        self.llm_client = llm_client
        self.file_sizes: dict[str, int] = {}

    def process_inbox(self) -> None:
        inbox_dir = Path(self.config.inbox_path)
        while True:
            current_time = time.time()
            for tmp_dir in inbox_dir.glob(".tmp_*"):
                if not tmp_dir.is_dir():
                    continue
                try:
                    mtime = os.stat(tmp_dir).st_mtime
                    if current_time - mtime > 300:
                        stem = tmp_dir.name[5:]
                        if not ((inbox_dir / f"{stem}_Proposed.pdf").exists() or 
                                (inbox_dir / f"{stem}_Proposed OK.pdf").exists() or 
                                (inbox_dir / f"{stem}.pdf").exists()):
                            shutil.rmtree(tmp_dir)
                except Exception as e:
                    logger.error(f"Failed to cleanup temp dir {tmp_dir}: {e}")

            for pdf_path in inbox_dir.glob("*.pdf"):
                name = pdf_path.name
                
                if name.endswith("_Proposed.pdf") or name.endswith("_Failed.pdf") or name.endswith("_Error_Invalid_Format.pdf") or name.endswith(" - please choose area.pdf"):
                    continue

                if name.endswith(" OK.pdf"):
                    self.finalize(pdf_path)
                    continue

                try:
                    size = os.path.getsize(pdf_path)
                except OSError:
                    continue

                if size == 0:
                    continue
                    
                path_str = str(pdf_path)
                prev_size = self.file_sizes.get(path_str)
                self.file_sizes[path_str] = size
                
                if prev_size != size:
                    continue
                    
                self.propose(pdf_path)
                
            time.sleep(2)

    def propose(self, filepath: Path) -> None:
        name = filepath.name
        
        try:
            parsed_cmd = parse_filename_syntax(name)
        except ValueError:
            new_name = filepath.stem + "_Error_Invalid_Format.pdf"
            os.rename(filepath, filepath.parent / new_name)
            return

        tmp_dir = filepath.parent / f".tmp_{filepath.stem}"
        tmp_dir.mkdir(exist_ok=True)

        try:
            process_unclassified_pdf(tmp_dir, self.llm_client, specific_pdf_path=filepath, create_categorized_copy=False)
            
            orig_report_path = tmp_dir / f"{filepath.stem}_report.json"
            tmp_report_path = tmp_dir / "_report_append_mode.json"
            if orig_report_path.exists():
                orig_report_path.rename(tmp_report_path)
            
            inferred = infer_missing_data(filepath, parsed_cmd, self.llm_client)
        except Exception as e:
            logger.error(f"Inference/Categorization failed for {filepath}: {e}")
            new_name = filepath.stem + "_Failed.pdf"
            os.rename(filepath, filepath.parent / new_name)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return
            
        house_to_resolve = inferred.get("expected_house_number", parsed_cmd.house)
        if house_to_resolve == 'U':
            house_to_resolve = parsed_cmd.house # Fallback
            
        try:
            areas_root = Path(self.config.areas_root_path)
            area_id = resolve_area(house_to_resolve, areas_root)
        except ConflictError:
            new_name = filepath.stem + " - please choose area.pdf"
            os.rename(filepath, filepath.parent / new_name)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return
        except ValueError as e:
            logger.error(f"Failed to resolve area for {filepath}: {e}")
            new_name = filepath.stem + "_Failed.pdf"
            os.rename(filepath, filepath.parent / new_name)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return
            
        area_dir = areas_root / area_id
        house_dir = None
        for child in area_dir.iterdir():
            if child.is_dir() and (child.name == house_to_resolve or child.name.startswith(f"{house_to_resolve} - ")):
                house_dir = child
                break
        
        if not house_dir:
            logger.error(f"Failed to find full house dir for {house_to_resolve} in {area_dir}")
            new_name = filepath.stem + "_Failed.pdf"
            os.rename(filepath, filepath.parent / new_name)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return

        yaml_path = house_dir / ".source_files" / f"{house_to_resolve}_tenants.yaml"
        if not yaml_path.exists():
            logger.error(f"Missing YAML config for {house_to_resolve}")
            new_name = filepath.stem + "_Error_Missing_YAML.pdf"
            os.rename(filepath, filepath.parent / new_name)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return

        tenant_to_resolve = inferred.get("tenant_hint", parsed_cmd.tenant_hint)
        tenant = resolve_tenant(house_dir, tenant_to_resolve, self.llm_client)
        
        # Build proposed name
        doc_date = inferred.get("date", parsed_cmd.date or "UnknownDate")
        if doc_date == "U":
            doc_date = "UnknownDate"
            
        doc_type = inferred.get("title", getattr(parsed_cmd, "title", "")) or "UnknownType"
        if doc_type == "U" or not doc_type:
            doc_type = "UnknownType"
        
        resolved_name = f"{area_id} {house_to_resolve} {tenant} {parsed_cmd.group} {doc_date} {doc_type}"
        

        pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY") or "dummy")
        pipeline.client = self.llm_client
        
        cleaned_pages, _ = pipeline._clean_documents(tmp_report_path, house_dir, house_to_resolve)
        
        cleaned_json_path = tmp_dir / "_cleaned_append_mode.json"
        with open(cleaned_json_path, 'w', encoding='utf-8') as f:
            json.dump([p.model_dump() for p in cleaned_pages], f, ensure_ascii=False, indent=2)
            
        group_mode = resolve_group_mode(parsed_cmd.group)
        
        if group_mode.get("skip_grouping"):
            if cleaned_pages:
                first_page = cleaned_pages[0]
                category = getattr(first_page, "category", "Unknown")
                title = getattr(first_page, "brief_arabic_title", "Unknown")
                dates = [getattr(p, "date") for p in cleaned_pages if getattr(p, "date", None)]
                group = DocumentGroup(
                    start_page=min(p.original_index for p in cleaned_pages),
                    end_page=max(p.original_index for p in cleaned_pages),
                    primary_tenant=tenant,
                    category=category,
                    dates=dates,
                    brief_arabic_title=title
                )
            else:
                group = DocumentGroup(
                    start_page=0, end_page=0, primary_tenant=tenant, category="Unknown", dates=[], brief_arabic_title="Unknown"
                )
            
            with open(tmp_dir / "_grouped_append_mode.json", 'w', encoding='utf-8') as f:
                json.dump([group.model_dump()], f, ensure_ascii=False, indent=2)
                
            if group_mode.get("skip_routing"):
                group.folder_path = group_mode["folder_name"]
                group.is_direct_routed = True
                routed_docs = [group]
            else:
                routed_docs = pipeline._route_documents([group])
                
            with open(tmp_dir / "_routed_append_mode.json", 'w', encoding='utf-8') as f:
                json.dump([doc.model_dump() for doc in routed_docs], f, ensure_ascii=False, indent=2)
        else:
            raw_pages = [(p.original_index, p) for p in cleaned_pages]
            documents = pipeline._group_documents(raw_pages)
            with open(tmp_dir / "_grouped_append_mode.json", 'w', encoding='utf-8') as f:
                json.dump([doc.model_dump() for doc in documents], f, ensure_ascii=False, indent=2)
                
            routed_docs = pipeline._route_documents(documents)
            
            if parsed_cmd.tenant_hint != 'U':
                for doc in routed_docs:
                    doc.primary_tenant = tenant
                    
            with open(tmp_dir / "_routed_append_mode.json", 'w', encoding='utf-8') as f:
                json.dump([doc.model_dump() for doc in routed_docs], f, ensure_ascii=False, indent=2)
                
        new_pdf_path = filepath.parent / f"{resolved_name}_Proposed.pdf"
        os.rename(filepath, new_pdf_path)
        
        new_tmp_dir = filepath.parent / f".tmp_{resolved_name}"
        os.rename(tmp_dir, new_tmp_dir)

    def finalize(self, filepath: Path) -> None:
        clean_name = filepath.name.replace(" OK.pdf", "").replace("_Proposed", "")
        
        areas_root = Path(self.config.areas_root_path).resolve(strict=True)
        
        area_id = None
        for a in areas_root.iterdir():
            if a.is_dir() and clean_name.startswith(a.name + " "):
                area_id = a.name
                break
                
        if not area_id:
            logger.error(f"Cannot parse area from finalized name: {clean_name}")
            return
            
        area_dir = areas_root / area_id
        house_dir = None
        house_id = None
        rest_of_name = clean_name[len(area_id) + 1:]
        
        for h in area_dir.iterdir():
            if not h.is_dir():
                continue
            # Try to match the exact house ID first (e.g. 504)
            # The house ID is the part before ' - ' in the folder name, or the folder name itself
            h_id = h.name.split(" - ")[0]
            if rest_of_name.startswith(h_id + " "):
                house_dir = h
                house_id = h_id
                break
                
        if not house_dir:
            logger.error(f"Cannot parse house from finalized name: {clean_name}")
            return
        
        dest_dir = house_dir / ".source_files"
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure dest_dir is within areas_root (mitigates T-24-02-01)
        if not dest_dir.is_relative_to(areas_root):
            logger.error(f"Destination directory {dest_dir} is outside areas root.")
            return

        base_name = f"{clean_name}.pdf"
        dest_pdf = dest_dir / base_name
        
        # Handle collision (append counter)
        counter = 1
        while dest_pdf.exists():
            dest_pdf = dest_dir / f"{clean_name} ({counter}).pdf"
            counter += 1
            
        try:
            shutil.move(str(filepath), str(dest_pdf))
        except Exception as e:
            logger.error(f"Move failed for {filepath}: {e}")
            return
            
        # Move json if exists
        original_stem_proposed = filepath.name.replace(" OK.pdf", "_Proposed")
        json_path = filepath.parent / f"{original_stem_proposed}_report.json"
        
        if json_path.exists():
            dest_json = dest_dir / f"{dest_pdf.stem}_report.json"
            shutil.move(str(json_path), str(dest_json))
            
        # Run pipeline passes
        # Explicitly trigger process_unclassified_pdf to synthesize _report.json if missing
        if not (dest_dir / f"{dest_pdf.stem}_report.json").exists():
            process_unclassified_pdf(dest_dir, self.llm_client)
            
        json_report_path = dest_dir / f"{dest_pdf.stem}_report.json"
        
        # Run pipeline
        try:
            output_json_path = dest_dir / f"{house_id}_1_cleaned.json"
            cleaned_pages, yaml_data = run_cleaning_pass(json_report_path, output_json_path, self.llm_client, logger, False, house_id, dest_dir)
            documents = run_grouping_pass(cleaned_pages, house_id, house_dir, self.llm_client, logger, False)
            documents = run_routing_pass(documents, house_id, house_dir, self.llm_client, logger, False)
            run_generation_pass(documents, dest_dir, house_id, house_dir, logger, False, yaml_data=yaml_data, pdf_path=dest_pdf)
        except Exception as e:
            logger.exception(f"Pipeline failed for {dest_pdf}: {e}")
