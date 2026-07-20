import os
import time
import logging
import shutil
from pathlib import Path
from typing import Any

from src.inbox.parser import parse_filename_syntax
from src.inbox.resolver import infer_missing_data, resolve_area, resolve_tenant, ConflictError
from src.categorization.categorization import process_unclassified_pdf
from src.main import run_cleaning_pass, run_grouping_pass, run_routing_pass, run_generation_pass

logger = logging.getLogger(f"file_organizer.{__name__}")

class FSUIOrchestrator:
    def __init__(self, config: Any, llm_client: Any):
        self.config = config
        self.llm_client = llm_client
        self.file_sizes: dict[str, int] = {}

    def process_inbox(self) -> None:
        inbox_dir = Path(self.config.inbox_path)
        while True:
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

        try:
            inferred = infer_missing_data(filepath, parsed_cmd, self.llm_client)
        except Exception as e:
            logger.error(f"Inference failed for {filepath}: {e}")
            new_name = filepath.stem + "_Failed.pdf"
            os.rename(filepath, filepath.parent / new_name)
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
            return
        except ValueError as e:
            logger.error(f"Failed to resolve area for {filepath}: {e}")
            new_name = filepath.stem + "_Failed.pdf"
            os.rename(filepath, filepath.parent / new_name)
            return
            
        house_dir = areas_root / area_id / house_to_resolve
        tenant_to_resolve = inferred.get("tenant_hint", parsed_cmd.tenant_hint)
        tenant = resolve_tenant(house_dir, tenant_to_resolve, self.llm_client)
        
        # Build proposed name
        doc_date = inferred.get("document_date", parsed_cmd.document_date or "UnknownDate")
        doc_type = inferred.get("document_type", parsed_cmd.document_type or "UnknownType")
        
        resolved_name = f"{area_id} {house_to_resolve} {tenant} {doc_date} {doc_type}"
        
        new_pdf_path = filepath.parent / f"{resolved_name}_Proposed.pdf"
        os.rename(filepath, new_pdf_path)
        
        # Check if _report.json exists
        json_path = filepath.parent / f"{filepath.stem}_report.json"
        if json_path.exists():
            new_json_path = filepath.parent / f"{resolved_name}_Proposed_report.json"
            os.rename(json_path, new_json_path)

    def finalize(self, filepath: Path) -> None:
        clean_name = filepath.name.replace(" OK.pdf", "").replace("_Proposed", "")
        # The clean name format: "Area House Tenant Date Type"
        parts = clean_name.split(" ", 2)
        if len(parts) < 3:
            logger.error(f"Cannot parse house from finalized name: {clean_name}")
            return
            
        area_id = parts[0]
        house_id = parts[1]
        
        areas_root = Path(self.config.areas_root_path).resolve(strict=True)
        house_dir = (areas_root / area_id / house_id).resolve(strict=True)
        
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
