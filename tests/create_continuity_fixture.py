
import json

# Base data extracted from 567_report.json
data = {
    "1": {
        "category": "letters",
        "content_explanation": "This document is an official administrative letter from the Kingdom of Bahrain's Ministry of Interior...",
        "subject": "الموضوع : الوحدات السكنية",
        "date": "15 ديسمبر 2020م",
        "expected_tenant_name": "UAT Test Tenant"
    },
    "2": {
        "category": "letters",
        "content_explanation": "This official letter from the Kingdom of Bahrain's Ministry of Interior is issued by the Assistant Undersecretary...",
        "subject": "الموضوع: الوحدات السكنية (Subject: Housing Units)",
        "date": "7 ديسمبر 2020",
        "expected_tenant_name": "UAT Test Tenant"
    },
    "3": {
        "category": "letters",
        "content_explanation": "This official letter is issued by the Kingdom of Bahrain's Ministry of Interior, specifically the Police Housing Branch...",
        "subject": "الوحدة رقم 567 طريق 944 سافرة",
        "date": "23 يناير 2020",
        "expected_tenant_name": "عبدالله شمسان البوعينين"
    },
    "4": {
        "category": "letters",
        "content_explanation": "This document is an official administrative letter from the Ministry of Interior, Kingdom of Bahrain...",
        "subject": "Deduction for First Lieutenant 1579, Abdullah Shamsan Abdullah Salman Al-Buainain",
        "date": "19 January 2020",
        "expected_tenant_name": "Abdullah Shamsan Abdullah Salman Al-Buainain"
    },
    "5": {
        "category": "letters",
        "content_explanation": "This official document is a formal letter issued by the Police Housing Branch of the Ministry of Interior...",
        "subject": "وقf علاوة بدل السكن (Suspension of housing allowance)",
        "date": "19 January 2020",
        "expected_tenant_name": "عبدالله شمسان عبدالله سلمان البوعينين"
    },
    "6": {
        "category": "letters",
        "content_explanation": "This official letter from the Kingdom of Bahrain, Ministry of Interior, Police Housing Branch...",
        "subject": "Colonel Abdullah Shamsan Al-Buainain (regarding Colonel Abdullah Ali Rashid Muantar's housing assignment)",
        "date": "15 January 2020",
        "expected_tenant_name": "Abdullah Ali Rashid Muantar"
    },
    "7": {
        "category": "forms",
        "content_explanation": "This document is a 'Residential Unit Handover Form' issued by the Ministry of Interior...",
        "subject": "Handover Form",
        "date": "16 January 2020",
        "expected_tenant_name": "UAT Test Tenant"
    },
    "8": {
        "category": "letters",
        "content_explanation": "This official letter from the Kingdom of Bahrain's Ministry of Interior (Police Housing Branch) is addressed to the Electricity and Water Authority...",
        "subject": "Unit 567, Road 4411, Safra 944, Account Number: (13-18634)",
        "date": "16 January 2020",
        "expected_tenant_name": "Abdullah Shamsan Abdullah Salman Al-Buainain"
    },
    "9": {
        "category": "contract",
        "content_explanation": "The document is the cover page of a contract issued by the Ministry of Interior in the Kingdom of Bahrain.",
        "subject": "Residential Unit Usufruct Contract",
        "date": "16 January 2020",
        "expected_tenant_name": "UAT Test Tenant"
    },
    "10": {
        "category": "contract",
        "content_explanation": "This document is an administrative contract for residential unit usage dated January 16, 2020.",
        "subject": "Residential Unit Usage Contract",
        "date": "16 January 2020",
        "expected_tenant_name": "عبدالله شمسان عبدالله سلمان البوعينين"
    }
}

with open("tests/fixtures/uat_08_continuity_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
