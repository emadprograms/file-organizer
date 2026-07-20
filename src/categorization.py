import os
import json
import logging
from pathlib import Path
from typing import Any, Literal
import yaml
from pydantic import create_model, Field

from src.pdf.image_processing import process_pdf
from src.core.schemas import CategorizationResult
from src.utils.fs import atomic_write
import shutil

logger = logging.getLogger(f"file_organizer.{__name__}")

def process_unclassified_pdf(target_dir: Path, llm_client: Any) -> None:
    """
    Scans the target directory for raw PDFs, bypasses if _report.json exists,
    otherwise processes images, queries LLM, and creates outputs.
    """
    # Load categories configuration
    categories_path = Path(__file__).parent / "core" / "categories.yaml"
    if not categories_path.exists():
        logger.error(f"Categories file not found at {categories_path}")
        return
        
    with open(categories_path, 'r', encoding='utf-8') as f:
        categories = yaml.safe_load(f)

    # Prebuild classification prompt instructions
    classification_instructions = "Categories and Identification Rules:\n"
    for cat_name, cat_rules in categories.items():
        if not isinstance(cat_rules, dict):
            continue
        classification_instructions += f"Category: {cat_name}\n"
        desc = cat_rules.get("description", "")
        if desc:
            classification_instructions += f"Description: {desc}\n"
        ident_rules = cat_rules.get("identification_rules", [])
        for rule in ident_rules:
            classification_instructions += f"  - {rule}\n"
        classification_instructions += "\n"

    for pdf_path in target_dir.glob("*.pdf"):
        # Skip if already a categorized PDF
        if "_categorized" in pdf_path.name:
            continue
            
        if not pdf_path.is_file() or pdf_path.name.startswith("."):
            continue
            
        basename = pdf_path.stem
        report_path = target_dir / f"{basename}_report.json"
        categorized_pdf_path = target_dir / f"{basename}_categorized.pdf"
        
        if report_path.exists() or (target_dir / "_report.json").exists():
            logger.info(f"Bypassing categorization for {pdf_path.name}: {report_path.name} already exists.")
            continue
            
        logger.info(f"Processing unclassified PDF: {pdf_path}")
        
        # 1. Process PDF into images
        status, tmp_dir = process_pdf(str(pdf_path), str(target_dir))
        if status is None:
            continue
            
        # 2. Query LLM for each page
        for page_key, page_status in status.items():
            if page_status.get("status") == "classified":
                continue
                
            image_path = os.path.join(tmp_dir, f"{page_key}.png")
            if not os.path.exists(image_path):
                continue
                
            image_obj = None
            try:
                # Use GenAI File API via our LLMClient wrapper instead of inline Base64
                image_obj = llm_client.upload_file(image_path)
                
                # STEP 1: CLASSIFY ONLY
                class_prompt = (
                    "Categorize this Arabic PDF page. "
                    f"You must select EXACTLY ONE category from the following list: {list(categories.keys())}. "
                    "Respond with a JSON object containing ONLY the 'category' key."
                )
                class_prompt = f"{classification_instructions}\n\n{class_prompt}"
                
                # Use Literal to strictly enforce the enum in the API schema
                CategoryLiteral = Literal[tuple(categories.keys())]
                CategorySchema = create_model('CategorySchema', category=(CategoryLiteral, Field(..., description="The category name")))
                
                class_result = llm_client.generate_content(
                    contents=[image_obj, class_prompt],
                    response_schema=CategorySchema,
                    is_boundary_call=False
                )
                
                category = class_result.category
                if category not in categories:
                    logger.warning(f"Invalid category '{category}' returned for {page_key}")
                    continue
                    
                # STEP 2: EXTRACT SPECIFIC FIELDS
                extract_rules = categories[category].get("extract", [])
                extract_instructions = f"Extract information for category '{category}'.\nRules:\n"
                
                extracted_fields = {
                    "content_explanation": (str, Field(..., description="Detailed explanation of the document contents")),
                    "expected_tenant_name": (str | None, Field(None, description="The person living in or responsible for the house")),
                    "expected_house_number": (str | None, Field(None, description="The house number associated with the tenant"))
                }
                
                for field in extract_rules:
                    key = field.split(":")[0].strip()
                    extract_instructions += f"  - {field}\n"
                    extracted_fields[key] = (str | None, Field(None))
                    
                ext_prompt = (
                    "Extract the required information from this Arabic PDF page based on the rules. "
                    "Respond with a JSON object containing the exact requested fields."
                )
                ext_prompt = f"{extract_instructions}\n\n{ext_prompt}"
                
                ExtractionSchema = create_model('ExtractionSchema', **extracted_fields)
                
                ext_result = llm_client.generate_content(
                    contents=[image_obj, ext_prompt],
                    response_schema=ExtractionSchema,
                    is_boundary_call=False
                )
                
                page_status["status"] = "classified"
                page_status["category"] = category
                
                # convert to dict excluding None
                result_dict = ext_result.model_dump(exclude_none=True)
                for k, v in result_dict.items():
                    page_status[k] = v
                    
                status[page_key] = page_status
                
            except Exception as e:
                logger.error(f"LLM Classification failed for {page_key}: {e}")
                status[page_key]["status"] = "error"
                status[page_key]["error"] = str(e)
            finally:
                if image_obj:
                    try:
                        llm_client.delete_file(image_obj)
                    except Exception as e:
                        logger.warning(f"Failed to delete uploaded file: {e}")
                
            # Save progress incrementally after each LLM call
            progress_file = os.path.join(tmp_dir, "progress.json")
            with atomic_write(progress_file) as tmp_progress:
                with open(tmp_progress, "w", encoding="utf-8") as f:
                    json.dump(status, f)

        # Build final report as a list sorted by page index
        final_report = []
        for i in range(len(status)):
            key = f"page_{i}"
            if key in status:
                final_report.append(status[key])
        
        # Write _report.json atomically
        with atomic_write(str(report_path)) as tmp_path:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(final_report, f, indent=2, ensure_ascii=False)
                
        # Rename original PDF to _categorized.pdf
        shutil.copy(str(pdf_path), str(categorized_pdf_path))
        logger.info(f"Successfully processed and categorized: {categorized_pdf_path.name}")
        
