import requests

import os
import time
import base64
import fitz  # PyMuPDF
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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

Return ONLY a JSON object with: house_number, residents (list of strings), category, date, summary (string), and is_form (boolean). Do not use markdown formatting."""

USER_PROMPT = "Classify this scanned document page."

def extract_first_page_image(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=150)
    image_bytes = pix.tobytes("jpeg")
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    doc.close()
    return image_base64

def test_local_model(base_url, model, image_base64):
    start_time = time.time()
    try:
        # Strip data URL prefix if present, Ollama expects raw base64
        if image_base64.startswith("data:"):
            image_base64 = image_base64.split(",")[1]
            
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT,
                    "images": [image_base64]
                }
            ],
            "options": {
                "num_ctx": 16384,
                "temperature": 0.0
            },
            "stream": False
        }
        response = requests.post(f"{base_url.replace('/v1', '')}/api/chat", json=payload)
        response.raise_for_status()
        end_time = time.time()
        return response.json().get("message", {}).get("content", ""), end_time - start_time
    except Exception as e:
        return str(e), time.time() - start_time

def main():
    pdf_path = "pdfs/559.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return

    print(f"Extracting image from the first page of {pdf_path}...")
    image_base64 = extract_first_page_image(pdf_path)

    local_base_url = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
    print(f"Connecting to Local API at {local_base_url}...")
    
    model = "qwen3.5:9b"
    print(f"\nTesting Local model: {model}")
    print("=" * 50)

    result, duration = test_local_model(local_base_url, model, image_base64)
    print(f"Response Time: {duration:.2f}s")
    print(f"Output:\n{result}")
    print("-" * 50)

if __name__ == "__main__":
    main()
