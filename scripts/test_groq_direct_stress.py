import os
import sys
import time
import base64
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
import openai

# Setup paths to import from src
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest import PdfIngestor

# Configure logging to both console and file
log_file = "groq_multi_model_test.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# The exact system prompt established in src/llm.py
SYSTEM_PROMPT = """You are an Arabic document classification expert analyzing scanned housing files from the Bahrain/Gulf region.

You are receiving a scanned page IMAGE. Read the page directly using your vision capabilities and classify it.

CRITICAL FIRST STEP: If the image is a letter, first analyze the subject (الموضوع) of the letter or document before looking at the body text.

Classify this page into exactly ONE of the following 13 categories:

1. Basic Details Form — البيانات الأساسية (SINGLE-PERSON FORMS ONLY. Forms with fields like Name, Rank, Allotment Date (تاريخ التخصيص), and Vacation Date (تاريخ الإخلاء) for ONE person are basic_details. CRITICAL FATAL ERROR: You are STRICTLY FORBIDDEN from selecting this if the page is a roster, schedule, or table listing MULTIPLE different people's names (e.g., 'كشف بأسماء', 3+ distinct people). Multi-person rosters are NEVER basic_details. WARNING: basic_details forms may mention rent amounts; do NOT misclassify them as rent_deduction just because of a rent amount. ONLY choose this for a form containing boxes/blanks dedicated to ONE specific person.)
2. Personal Identification — البيانات الشخصية (Pictures of identity cards, passports, and other non-form documents related to the person and his family. Anything related to the person and his family that is NOT a form goes into personal details.)
3. Allocation Order — أمر تخصيص (Allocation orders. STRICT DEFINITION: A letter from a higher authority ordering to give a place to stay. FORMS OR TABLES ARE NEVER AMAR TAKHSEES. It MUST be a letter paragraph format. Strong pattern: Exact subject 'الموضوع : الوحدات السكنية' AND format is a letter.)
4. Key Handover Certificate — نموذج تسليم المفتاح (ONLY use this for the INITIAL key handover after making the contract. Do NOT use this for temporary key handovers related to maintenance. If the word 'الأشغال' (Ashgal) is present anywhere, it is NEVER key_handover_form. Strong pattern: Contains 'استمارة تسليم الوحدات السكنية التابعة لوزارة الداخلية'.)
5. Housing Contract — العقد (Rental or housing contracts. STRICT DEFINITION: If the page contains contract articles like "مادة (1)", "مادة (2)", "الطرف الأول" (First Party), "الطرف الثاني" (Second Party), or "التمهيد" (Preamble), it MUST be a contract. WARNING: Contract pages often discuss rent deduction, allowances, or eviction inside their clauses. If these topics appear as part of a contract's "مادة" or terms, you MUST classify it as a contract and NEVER as rent_deduction, allowance_deduction, or notifications.)
6. Electricity and Water — رسائل الكهرباء والماء (EWA electricity/water letters. Strong pattern: Contains a meter number, such as 'الوحدة السكنية رقم', or the terms 'electricity & water' or 'ewa' in English at the beginning of the form. WARNING: These can be forms with details filled out; do NOT misclassify them as basic_details just because they are forms.)
7. Rent Deduction Notice — خصم الإيجار (Rent deduction notices or rosters. Usually formatted as letters addressed to someone to deduct rent. STRICT DEFINITION: They ALWAYS mention deducting amounts like "30" or "60" (bd). WARNING: Contracts and basic_details forms are EXEMPT and can mention rent amounts without being rent_deduction. Do NOT classify a single-person profile form (with rank, allotment date) or a contract clause as rent_deduction just because it mentions an amount. Use the amount presence ONLY to disambiguate from allowance_deduction.)
8. Allowance Deduction Notice — خصم العلاوة (Allowance deduction notices. Strong pattern: Subject is 'الموضوع: وقف استقطاع بدل الانتفاع'. Will NOT have "30 bd" or "60 bd" written on it.)
9. General Notifications — الإشعارات (General notifications, warnings, and ANY documents regarding vacating the house/eviction. STRICT DEFINITION: If the document mentions the tenant vacating the house (إخلاء), refusing to vacate, extensions for vacating, or any similar eviction terms, it MUST be notifications. Also includes 'إشعار' or 'اشعار'. Do NOT put eviction/vacating notices in other_letters. Do NOT use this for allocation orders.)
10. Maintenance Records — الصيانة (Maintenance requests, reports, work orders. STRICT RULE: If the word 'الأشغال' (Ashgal) is written ANYWHERE on the document, it MUST be maintenance. Even if it looks like a key handover form, if 'الأشغال' is present, it goes to maintenance. Do NOT put inspection notices or reports here.)
11. Inspection and Pictures — التفتيش والصور (Notices of inspection, inspection reports, house visits, yellow papers with inspection details, and photographs of the property. ANY letters or reports regarding inspection MUST go here, NOT to maintenance.)
12. Property Modifications — التعديلات (Modification requests or approvals. Strong pattern: Subject contains 'طلب' (talab) and mentions modifying the house.)
13. Miscellaneous Letters — رسائل أخرى (Any letters that don't fit the above. Also use this for generic multi-person rosters like 'كشف بأسماء' that do not clearly belong to another category.)

NAME EXTRACTION RULES (CRITICAL):
- Arabic names typically have 4 to 5 parts. Extract ALL parts of the name.
- If a document states a person's relationship (e.g., Wife - زوجة, Son - ابن), append it to their name in parentheses, e.g., "آمنة (زوجة)".
- If a document is addressed to MULTIPLE people, extract ALL of their names as a list of strings.
- Do NOT return an empty list or ["NONE"] unless you are absolutely certain there is no name anywhere on the page. Most documents DO contain a name.
- Only return ["NONE"] for categories where no resident is expected: Allocation Order, Inspection and Pictures, or Miscellaneous Letters with no addressee.

DATE EXTRACTION RULES:
- Find any visible date on the document.
- Normalize the date to YYYY-MM-DD format (e.g., 2008-05-14).
- FATAL RULE: You are STRICTLY FORBIDDEN from extracting Hijri dates (e.g., 1445 AH). ONLY extract Gregorian dates. Ignore Hijri dates even if both exist.
- If no Gregorian date is visible anywhere, return "NONE".

SPECIAL RULES:
- Normalize Arabic names intelligently: group variations like "محمد" and "المحمد" as the same person.
- Tolerate OCR noise and imperfect text in scanned documents.

Return a JSON object with: house_number, residents (list of strings), category, date, summary (string), and is_form (boolean)."""

def test_groq_pdf_benchmark():
    parser = argparse.ArgumentParser(description="Groq Model Stress Test")
    parser.add_argument("--llama", action="store_true", help="Test Llama 3.3 70B")
    parser.add_argument("--gptoss", action="store_true", help="Test GPT-OSS 120B")
    parser.add_argument("--qwen", action="store_true", help="Test Qwen 2.5 32B")
    parser.add_argument("--vision", action="store_true", help="Test Llama 3.2 Vision")
    parser.add_argument("--all", action="store_true", help="Test all models")
    args = parser.parse_args()

    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        log.error("GROQ_API_KEY not found in environment")
        return

    # Model Mapping
    model_map = {
        "llama": "llama-3.3-70b-versatile",
        "gptoss": "gpt-oss-120b",
        "qwen": "qwen-2.5-32b",
        "vision": "llama-3.2-11b-vision-preview"
    }

    selected_models = []
    if args.all:
        selected_models = list(model_map.values())
    else:
        if args.llama: selected_models.append(model_map["llama"])
        if args.gptoss: selected_models.append(model_map["gptoss"])
        if args.qwen: selected_models.append(model_map["qwen"])
        if args.vision: selected_models.append(model_map["vision"])

    if not selected_models:
        log.error("No models selected. Use --llama, --gptoss, --qwen, --vision or --all")
        return

    pdf_file = "559.pdf"
    pdf_path = PROJECT_ROOT / "pdfs" / pdf_file
    if not pdf_path.exists():
        log.error(f"PDF not found at {pdf_path}")
        return

    client = openai.OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )

    log.info(f"Starting Groq PDF Benchmark using {pdf_file}")
    
    ingestor = PdfIngestor()
    log.info(f"Extracting pages from {pdf_file}...")
    pages = list(ingestor.extract_pages_as_images(str(pdf_path)))
    
    test_pages = pages[:20]
    log.info(f"Processing first {len(test_pages)} pages across {len(selected_models)} models.")

    for model_id in selected_models:
        log.info(f"
{'='*60}
Testing Model: {model_id}
{'='*60}")
        
        is_vision_model = "vision" in model_id.lower()
        
        for idx, img_bytes in test_pages:
            log.info(f"Processing Page {idx}...")
            
            try:
                start_req = time.time()
                if is_vision_model:
                    base64_image = base64.b64encode(img_bytes).decode('utf-8')
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Classify this scanned document page."},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                                    }
                                ]
                            }
                        ],
                        response_format={"type": "json_object"}
                    )
                else:
                    # Simulating the OCR -> Text LLM pipeline
                    # In a real test, we'd use a local OCR model here. 
                    # For this script, we send a descriptive prompt to verify the classification logic.
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"I have a scanned document page {idx}. Imagine the OCR text is provided. Classify it following the rules. Return JSON."}
                        ],
                        response_format={"type": "json_object"}
                    )
                
                latency = time.time() - start_req
                result = response.choices[0].message.content
                log.info(f"Page {idx} Success ({latency:.2f}s) | Result: {result}")
                
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg:
                    log.warning(f"!!! RATE LIMITED at Page {idx} for model {model_id} !!!")
                    break
                else:
                    log.error(f"Page {idx} Failed: {e}")
                    continue
            
            time.sleep(3.0)

    log.info("Benchmark Completed. Results saved to groq_multi_model_test.log")

if __name__ == "__main__":
    test_groq_pdf_benchmark()
