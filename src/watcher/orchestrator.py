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
from src.pipeline.runner import run_cleaning_pass, run_grouping_pass, run_routing_pass, run_generation_pass
from src.pipeline.pipeline import Pipeline
from src.core.schemas import DocumentGroup

logger = logging.getLogger(f"file_organizer.{__name__}")

class FSUIOrchestrator:
    def __init__(self, config: Any, llm_client: Any):
        self.config = config
        self.llm_client = llm_client
        import sys
        if 'pytest' in sys.modules:
            self.cache_dir = Path(config.inbox_path).parent / ".file-organizer-cache"
        else:
            self.cache_dir = Path.home() / ".file-organizer" / "cache"
        self.file_sizes: dict[str, int] = {}

    def process_inbox(self) -> None:
        inbox_dir = Path(self.config.inbox_path)
        cache_dir = self.cache_dir
        
        while True:
            current_time = time.time()
            if cache_dir.exists():
                for tmp_dir in cache_dir.glob(".tmp_*"):
                    if not tmp_dir.is_dir():
                        continue
                    try:
                        mtime = os.stat(tmp_dir).st_mtime
                        if current_time - mtime > 300:
                            stem = tmp_dir.name[5:]
                            if not ((inbox_dir / f"{stem}.pdf").exists() or 
                                    (inbox_dir / f"{stem} OK.pdf").exists() or
                                    (inbox_dir / f"{stem.replace(' Proposed', '')}.pdf").exists() or
                                    (inbox_dir / f"{stem.replace(' Proposed', '')} OK.pdf").exists()):
                                shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception as e:
                        logger.error(f"Failed to cleanup temp dir {tmp_dir}: {e}")

            for pdf_path in inbox_dir.glob("*.pdf"):
                name = pdf_path.name
                
                if name.endswith(" Proposed.pdf") or name.endswith("_Failed.pdf") or name.endswith("_Error_Invalid_Format.pdf") or name.endswith(" - please choose area.pdf"):
                    continue

                if name.endswith(" OK.pdf"):
                    try:
                        self.finalize(pdf_path)
                    except Exception as e:
                        logger.error(f"Error finalizing {pdf_path}: {e}")
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
                    
                try:
                    self.propose(pdf_path)
                except Exception as e:
                    logger.error(f"Error proposing {pdf_path}: {e}")
                
            time.sleep(2)

    def propose(self, filepath: Path) -> None:
        name = filepath.name
        
        try:
            parsed_cmd = parse_filename_syntax(name)
        except ValueError:
            new_name = filepath.stem + "_Error_Invalid_Format.pdf"
            os.rename(filepath, filepath.parent / new_name)
            return

        cache_dir = self.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        master_tmp_dir = cache_dir / f".tmp_{filepath.stem}_master"
        master_tmp_dir.mkdir(exist_ok=True)

        try:
            process_unclassified_pdf(master_tmp_dir, self.llm_client, specific_pdf_path=filepath, create_categorized_copy=False)
            
            orig_report_path = master_tmp_dir / f"{filepath.stem}_report.json"
            if not orig_report_path.exists():
                logger.error(f"Missing report JSON for {filepath}")
                new_name = filepath.stem + "_Failed.pdf"
                os.rename(filepath, filepath.parent / new_name)
                shutil.rmtree(master_tmp_dir, ignore_errors=True)
                return
            
            import json
            with open(orig_report_path, 'r', encoding='utf-8') as f:
                full_report_data = json.load(f)
            
            inferred = infer_missing_data(filepath, parsed_cmd, self.llm_client, report_path=orig_report_path)
        except Exception as e:
            logger.error(f"Inference/Categorization failed for {filepath}: {e}")
            new_name = filepath.stem + "_Failed.pdf"
            os.rename(filepath, filepath.parent / new_name)
            shutil.rmtree(master_tmp_dir, ignore_errors=True)
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
            shutil.rmtree(master_tmp_dir, ignore_errors=True)
            return
        except ValueError as e:
            logger.error(f"Failed to resolve area for {filepath}: {e}")
            new_name = filepath.stem + "_Failed.pdf"
            os.rename(filepath, filepath.parent / new_name)
            shutil.rmtree(master_tmp_dir, ignore_errors=True)
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
            shutil.rmtree(master_tmp_dir, ignore_errors=True)
            return

        yaml_path = house_dir / ".source_files" / f"{house_to_resolve}_1_tenants.yaml"
        if not yaml_path.exists():
            yaml_path = house_dir / ".source_files" / f"{house_to_resolve}_tenants.yaml" # Fallback
        if not yaml_path.exists():
            logger.error(f"Missing YAML config for {house_to_resolve}")
            new_name = filepath.stem + "_Error_Missing_YAML.pdf"
            os.rename(filepath, filepath.parent / new_name)
            shutil.rmtree(master_tmp_dir, ignore_errors=True)
            return

        tenant_to_resolve = inferred.get("tenant_hint", parsed_cmd.tenant_hint)
        tenant = resolve_tenant(house_dir, tenant_to_resolve, self.llm_client)

        pipeline = Pipeline(api_key=os.getenv("GEMINI_API_KEY") or "dummy")
        pipeline.client = self.llm_client
        
        cleaned_pages, _ = pipeline._clean_documents(orig_report_path, house_dir, house_to_resolve)
        
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
            documents = [group]
        else:
            raw_pages = [(p.original_index, p) for p in cleaned_pages]
            documents = pipeline._group_documents(raw_pages)
            
        if group_mode.get("skip_routing"):
            for doc in documents:
                doc.folder_path = group_mode.get("folder_name")
                doc.is_direct_routed = True
            routed_docs = documents
        else:
            routed_docs = pipeline._route_documents(documents)
            
        if parsed_cmd.tenant_hint != 'U':
            for doc in routed_docs:
                doc.primary_tenant = tenant

        import fitz
        import hashlib
        
        try:
            with fitz.open(str(filepath)) as doc_pdf:
                for doc_idx, doc in enumerate(routed_docs):
                    doc_group_str = "G"
                    if doc.folder_path:
                        parts = doc.folder_path.split('.')
                        if parts[0].isdigit():
                            doc_group_str = parts[0]
                        else:
                            from src.routing.config import FOLDER_PREFIXES
                            prefix = FOLDER_PREFIXES.get(doc.folder_path)
                            if prefix:
                                doc_group_str = str(int(prefix))
                    
                    doc_date = doc.dates[0] if doc.dates else "UnknownDate"
                    doc_date = doc_date if doc_date else "UnknownDate"
                    doc_title = doc.brief_arabic_title or "UnknownType"
                    
                    doc_title = "".join(c for c in doc_title if c.isalnum() or c in " -_")
                    
                    doc_resolved_name = f"{area_id} {house_to_resolve} {doc.primary_tenant} {doc_group_str} {doc_date} {doc_title}"
                    
                    new_pdf_name = f"{doc_resolved_name} Proposed.pdf"
                    new_pdf_path = filepath.parent / new_pdf_name
                    
                    counter = 1
                    while new_pdf_path.exists():
                        new_pdf_name = f"{doc_resolved_name}_{counter} Proposed.pdf"
                        new_pdf_path = filepath.parent / new_pdf_name
                        counter += 1
                        
                    doc_tmp_dir = cache_dir / f".tmp_{new_pdf_path.stem}"
                    doc_tmp_dir.mkdir(exist_ok=True)
                    
                    new_doc_pdf = fitz.open()
                    start_idx = doc.start_page
                    end_idx = min(doc.end_page, doc_pdf.page_count - 1)
                    if start_idx <= end_idx:
                        new_doc_pdf.insert_pdf(doc_pdf, from_page=start_idx, to_page=end_idx)
                    new_doc_pdf.save(str(new_pdf_path))
                    new_doc_pdf.close()
                    
                    hasher = hashlib.sha256()
                    with open(new_pdf_path, 'rb') as f:
                        hasher.update(f.read())
                    pdf_hash = hasher.hexdigest()
                    
                    with open(doc_tmp_dir / "pdf_hash.txt", 'w') as f:
                        f.write(pdf_hash)
                    
                    doc_report = full_report_data[start_idx:end_idx+1]
                    doc_cleaned = [p.model_dump() for p in cleaned_pages if start_idx <= p.original_index <= end_idx]
                    for p_dict in doc_cleaned:
                        p_dict["original_index"] -= start_idx
                    doc_group = doc.model_copy()
                    doc_group.start_page = 0
                    doc_group.end_page = end_idx - start_idx
                    
                    with open(doc_tmp_dir / "_report_append_mode.json", 'w', encoding='utf-8') as f:
                        json.dump(doc_report, f, ensure_ascii=False, indent=2)
                    with open(doc_tmp_dir / "_cleaned_append_mode.json", 'w', encoding='utf-8') as f:
                        json.dump(doc_cleaned, f, ensure_ascii=False, indent=2)
                    with open(doc_tmp_dir / "_grouped_append_mode.json", 'w', encoding='utf-8') as f:
                        json.dump([doc_group.model_dump()], f, ensure_ascii=False, indent=2)
                    with open(doc_tmp_dir / "_routed_append_mode.json", 'w', encoding='utf-8') as f:
                        json.dump([doc_group.model_dump()], f, ensure_ascii=False, indent=2)
                        
        except Exception as e:
            logger.error(f"Error splitting proposed PDF {filepath}: {e}")
            new_name = filepath.stem + "_Failed.pdf"
            os.rename(filepath, filepath.parent / new_name)
            
        finally:
            shutil.rmtree(master_tmp_dir, ignore_errors=True)
            try:
                os.remove(filepath)
            except OSError:
                pass

    def finalize(self, filepath: Path) -> None:
        clean_name = filepath.name
        if clean_name.endswith(" OK.pdf"):
            clean_name = clean_name[:-7]
        if clean_name.endswith(" Proposed"):
            clean_name = clean_name[:-9]
            
        try:
            parsed_cmd = parse_filename_syntax(clean_name)
        except ValueError:
            parsed_cmd = None
        
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
            h_id = h.name.split(" - ")[0]
            if rest_of_name.startswith(h_id + " "):
                house_dir = h
                house_id = h_id
                break
                
        if not house_dir:
            logger.error(f"Cannot parse house from finalized name: {clean_name}")
            return
            
        import hashlib
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        file_hash = hasher.hexdigest()
        
        cache_dir = self.cache_dir
        tmp_dir = None
        if cache_dir.exists():
            for d in cache_dir.glob(".tmp_*"):
                if not d.is_dir():
                    continue
                
                # First try by name
                d_stem = d.name[5:]
                if d_stem == f"{clean_name} Proposed":
                    tmp_dir = d
                    break
                    
                # Fallback to hash
                hash_file = d / "pdf_hash.txt"
                if hash_file.exists():
                    with open(hash_file, 'r') as f:
                        if f.read().strip() == file_hash:
                            tmp_dir = d
                            break
                        
        if not tmp_dir:
            logger.error(f"Temp directory missing for finalize: {clean_name} (Hash: {file_hash}). It may have been deleted.")
            return

        if parsed_cmd:
            routed_json = tmp_dir / "_routed_append_mode.json"
            if routed_json.exists():
                with open(routed_json, 'r', encoding='utf-8') as f:
                    docs_data = json.load(f)
                
                if docs_data:
                    doc = docs_data[0]
                    if parsed_cmd.tenant_hint != 'U':
                        doc['primary_tenant'] = resolve_tenant(house_dir, parsed_cmd.tenant_hint, self.llm_client)
                    if parsed_cmd.group not in ('U', 'G'):
                        group_mode = resolve_group_mode(parsed_cmd.group)
                        if "folder_name" in group_mode:
                            doc['folder_path'] = group_mode["folder_name"]
                    if parsed_cmd.date and parsed_cmd.date != 'U':
                        doc['dates'] = [parsed_cmd.date]
                    if parsed_cmd.title and parsed_cmd.title != 'U':
                        doc['brief_arabic_title'] = parsed_cmd.title
                        
                    with open(routed_json, 'w', encoding='utf-8') as f:
                        json.dump(docs_data, f, ensure_ascii=False, indent=2)
                        
                    grouped_json = tmp_dir / "_grouped_append_mode.json"
                    if grouped_json.exists():
                        with open(grouped_json, 'w', encoding='utf-8') as f:
                            json.dump(docs_data, f, ensure_ascii=False, indent=2)

        source_files_dir = house_dir / ".source_files"
        source_files_dir.mkdir(parents=True, exist_ok=True)
        
        import fitz
        
        raw_append_pdf = source_files_dir / f"{house_id}_raw_append.pdf"
        finalized_pdf = house_dir / f"{house_id}_finalized.pdf"
        
        if not raw_append_pdf.exists() and finalized_pdf.exists():
            shutil.copy(str(finalized_pdf), str(raw_append_pdf))
            
        page_shift = 0
        if raw_append_pdf.exists():
            import tempfile
            import uuid
            tmp_pdf = Path(tempfile.gettempdir()) / f"raw_append_{uuid.uuid4().hex}.tmp.pdf"
            try:
                with fitz.open(str(raw_append_pdf)) as doc_pdf:
                    page_shift = doc_pdf.page_count
                    with fitz.open(str(filepath)) as new_doc:
                        doc_pdf.insert_pdf(new_doc)
                    doc_pdf.save(str(tmp_pdf))
                import shutil
                shutil.move(str(tmp_pdf), str(raw_append_pdf))
            except Exception as e:
                logger.error(f"Failed to append to raw PDF: {e}")
                if tmp_pdf.exists():
                    os.remove(str(tmp_pdf))
                return
        else:
            shutil.copy(str(filepath), str(raw_append_pdf))

        try:
            os.remove(str(filepath))
        except OSError as e:
            logger.warning(f"Could not delete {filepath}: {e}")

        def merge_json(filename_base: str, tmp_filename: str, has_pages: bool, has_groups: bool):
            master_path = source_files_dir / filename_base
            tmp_json_path = tmp_dir / tmp_filename
            
            if not tmp_json_path.exists():
                return
                
            with open(tmp_json_path, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
                
            if has_pages:
                for item in new_data:
                    if "original_index" in item:
                        item["original_index"] += page_shift
            elif has_groups:
                for item in new_data:
                    item["start_page"] += page_shift
                    item["end_page"] += page_shift
                    
            if master_path.exists():
                with open(master_path, 'r', encoding='utf-8') as f:
                    try:
                        master_data = json.load(f)
                    except json.JSONDecodeError:
                        master_data = []
                if isinstance(master_data, list) and isinstance(new_data, list):
                    master_data.extend(new_data)
                else:
                    master_data = new_data
            else:
                master_data = new_data
                
            with open(master_path, 'w', encoding='utf-8') as f:
                json.dump(master_data, f, ensure_ascii=False, indent=2)

        merge_json(f"{house_id}_report.json", "_report_append_mode.json", False, False)
        merge_json(f"{house_id}_1_cleaned.json", "_cleaned_append_mode.json", True, False)
        merge_json(f"{house_id}_2_grouped.json", "_grouped_append_mode.json", False, True)
        merge_json(f"{house_id}_3_routed_and_finalized.json", "_routed_append_mode.json", False, True)

        shutil.rmtree(tmp_dir, ignore_errors=True)

        from src.core.schemas import DocumentGroup
        import yaml
        import fitz as _fitz
        
        routed_json_path = source_files_dir / f"{house_id}_3_routed_and_finalized.json"
        if not routed_json_path.exists():
            return

        # Load the routed JSON. It may be the full manifest (list) or a reconciliation
        # manifest dict ({"summary": ..., "per_page": ...}). Extract just the docs.
        with open(routed_json_path, 'r', encoding='utf-8') as f:
            raw_json = json.load(f)

        if isinstance(raw_json, dict) and "per_page" in raw_json:
            # Reconciliation manifest — rebuild docs from per_page entries is hard.
            # Instead fall back to the append-mode doc list if available.
            logger.warning("routed JSON is a reconciliation manifest; skipping generation pass re-run.")
            return

        all_docs_data = raw_json
        
        # We only want the newly appended documents (those whose start_page >= page_shift)
        new_docs_data = [d for d in all_docs_data if d.get("start_page", 0) >= page_shift]
        if not new_docs_data:
            logger.warning("No new documents found in routed JSON after finalize merge. Skipping generation.")
            return

        # Re-index the new documents to be zero-relative (they reference absolute positions
        # in raw_append.pdf, but we will extract a slice of that PDF)
        new_docs = []
        for d in new_docs_data:
            doc = DocumentGroup(**d)
            doc.start_page = doc.start_page - page_shift
            doc.end_page = doc.end_page - page_shift
            new_docs.append(doc)

        # Extract the new-pages-only slice into a temporary PDF
        import tempfile
        import uuid
        tmp_slice_path = Path(tempfile.gettempdir()) / f"new_slice_{uuid.uuid4().hex}.tmp.pdf"
        try:
            with _fitz.open(str(raw_append_pdf)) as full_doc:
                new_doc_pdf = _fitz.open()
                new_doc_pdf.insert_pdf(full_doc, from_page=page_shift, to_page=full_doc.page_count - 1)
                new_doc_pdf.save(str(tmp_slice_path))
                new_doc_pdf.close()
        except Exception as e:
            logger.error(f"Failed to extract new-pages slice for generation: {e}")
            return

        yaml_path = source_files_dir / f"{house_id}_1_tenants.yaml"
        if not yaml_path.exists():
            yaml_path = source_files_dir / f"{house_id}_tenants.yaml"
        yaml_data = None
        if yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)

        try:
            run_generation_pass(
                new_docs, 
                target_dir=house_dir, 
                house_id=house_id, 
                output_dir=area_dir, 
                logger=logger, 
                dry_run=False, 
                json_path=source_files_dir / f"{house_id}_report.json", 
                yaml_data=yaml_data, 
                pdf_path=tmp_slice_path
            )
        finally:
            if tmp_slice_path.exists():
                try:
                    os.remove(str(tmp_slice_path))
                except OSError:
                    pass

        # Rebuild finalized.pdf from the full raw_append.pdf with updated TOC (all docs)
        import fitz as _fitz2
        from src.pdf.compress import compress_pdf

        # Re-resolve house_dir in case it was renamed by organize()
        for h in area_dir.iterdir():
            if h.is_dir() and (h.name == house_id or h.name.startswith(f"{house_id} - ")):
                house_dir = h
                break
        source_files_dir = house_dir / ".source_files"
        raw_append_pdf = source_files_dir / f"{house_id}_raw_append.pdf"

        all_docs_for_toc = [DocumentGroup(**d) for d in all_docs_data]
        finalized_path = house_dir / f"{house_id}_finalized.pdf"
        import tempfile
        import uuid
        tmp_finalized = Path(tempfile.gettempdir()) / f"finalized_{uuid.uuid4().hex}.tmp.pdf"
        try:
            toc = []
            for doc in all_docs_for_toc:
                title = doc.brief_arabic_title or doc.folder_path or "بدون عنوان"
                toc.append([1, title, doc.start_page + 1])
            with _fitz2.open(str(raw_append_pdf)) as full_pdf:
                full_pdf.set_toc(toc)
                full_pdf.save(str(tmp_finalized))
            compress_pdf(str(tmp_finalized), str(finalized_path))
            if tmp_finalized.exists():
                os.remove(str(tmp_finalized))
            logger.info(f"Rebuilt finalized PDF: {finalized_path.name} ({finalized_path.stat().st_size} bytes)")
        except Exception as e:
            logger.error(f"Failed to rebuild finalized PDF: {e}")

