import json
from pathlib import Path

groups = [
  {
    "start_page": 0,
    "end_page": 1,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2025-06-11"],
    "reason": "Official letter regarding housing units maintenance and handover",
    "brief_arabic_title": "رسالة صيانة وتسليم وحدات",
    "folder_path": "10_صيانة",
    "is_direct_routed": False
  },
  {
    "start_page": 2,
    "end_page": 3,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2024-11-11"],
    "reason": "Internal memo regarding house 502",
    "brief_arabic_title": "مذكرة داخلية",
    "folder_path": "13_رسائل متنوعة",
    "is_direct_routed": False
  },
  {
    "start_page": 4,
    "end_page": 5,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2025-02-27"],
    "reason": "Urgent letter regarding special housing units requests",
    "brief_arabic_title": "طلب وحدة سكنية خاصة",
    "folder_path": "13_رسائل متنوعة",
    "is_direct_routed": False
  },
  {
    "start_page": 6,
    "end_page": 7,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2025-02-17"],
    "reason": "Letter regarding housing violations and modifications",
    "brief_arabic_title": "رسالة بشأن المخالفات",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 8,
    "end_page": 8,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "others",
    "dates": ["2025-02-11"],
    "reason": "Report on engineering violations",
    "brief_arabic_title": "تقرير هندسي للمخالفات",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 9,
    "end_page": 9,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2025-01-01"],
    "reason": "Form for submitting engineering drawings",
    "brief_arabic_title": "تقديم رسومات هندسية",
    "folder_path": "12_تعديلات",
    "is_direct_routed": False
  },
  {
    "start_page": 10,
    "end_page": 10,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2025-02-05"],
    "reason": "Letter regarding violations",
    "brief_arabic_title": "رسالة بشأن المخالفات",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 11,
    "end_page": 11,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2025-01-30"],
    "reason": "Letter regarding violations in Safra",
    "brief_arabic_title": "رسالة بشأن المخالفات",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 12,
    "end_page": 12,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2024-01-28"],
    "reason": "Letter regarding inspection visits",
    "brief_arabic_title": "تقرير الزيارات التفتيشية",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 13,
    "end_page": 15,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2025-01-27"],
    "reason": "Violation report with photos for house 1322",
    "brief_arabic_title": "رصد مخالفة وصور",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 16,
    "end_page": 18,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2025-01-26"],
    "reason": "Violation report with photos for house 502",
    "brief_arabic_title": "رصد مخالفة وصور",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 19,
    "end_page": 22,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2025-01-26"],
    "reason": "Violation report with photos for house 975",
    "brief_arabic_title": "رصد مخالفة وصور",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 23,
    "end_page": 24,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2024-01-30"],
    "reason": "Letter regarding violations for multiple houses",
    "brief_arabic_title": "رسالة مخالفات مجمعة",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 25,
    "end_page": 27,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2025-01-26"],
    "reason": "Violation report with photos for house 502",
    "brief_arabic_title": "رصد مخالفة وصور",
    "folder_path": "09_إشعارات",
    "is_direct_routed": False
  },
  {
    "start_page": 28,
    "end_page": 28,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2024-11-20"],
    "reason": "Rent deduction request",
    "brief_arabic_title": "استقطاع إيجار",
    "folder_path": "07_استقطاع إيجار",
    "is_direct_routed": False
  },
  {
    "start_page": 29,
    "end_page": 29,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2024-11-19"],
    "reason": "Housing unit handover form",
    "brief_arabic_title": "استمارة تسليم الوحدة",
    "folder_path": "04_محضر تسليم مفتاح",
    "is_direct_routed": False
  },
  {
    "start_page": 30,
    "end_page": 30,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2024-11-17"],
    "reason": "EWA connection request letter",
    "brief_arabic_title": "توصيل تيار كهربائي",
    "folder_path": "06_كهرباء وماء",
    "is_direct_routed": False
  },
  {
    "start_page": 31,
    "end_page": 40,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "id_cards",
    "dates": ["2024-01-01"],
    "reason": "Personal ID cards and passports",
    "brief_arabic_title": "بيانات شخصية",
    "folder_path": "02_بيانات شخصية",
    "is_direct_routed": True
  },
  {
    "start_page": 41,
    "end_page": 48,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "contract",
    "dates": ["2024-11-19"],
    "reason": "Housing allocation contract",
    "brief_arabic_title": "عقد انتفاع",
    "folder_path": "05_عقود",
    "is_direct_routed": True
  },
  {
    "start_page": 49,
    "end_page": 49,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "letters",
    "dates": ["2024-11-11"],
    "reason": "Internal memo regarding maintenance",
    "brief_arabic_title": "مذكرة داخلية",
    "folder_path": "13_رسائل متنوعة",
    "is_direct_routed": False
  },
  {
    "start_page": 50,
    "end_page": 51,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2024-08-22"],
    "reason": "House handover checklist",
    "brief_arabic_title": "قائمة استلام منزل",
    "folder_path": "04_محضر تسليم مفتاح",
    "is_direct_routed": False
  },
  {
    "start_page": 52,
    "end_page": 52,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2024-09-10"],
    "reason": "Service request form",
    "brief_arabic_title": "طلب خدمة",
    "folder_path": "10_صيانة",
    "is_direct_routed": False
  },
  {
    "start_page": 53,
    "end_page": 53,
    "primary_tenant": "أحمد الحبر الشيخ",
    "category": "forms",
    "dates": ["2024-11-18"],
    "reason": "Key handover and receipt form",
    "brief_arabic_title": "إستمارة تسليم مفاتيح",
    "folder_path": "04_محضر تسليم مفتاح",
    "is_direct_routed": False
  }
]

report = []
for g in groups:
    for i in range(g["start_page"], g["end_page"] + 1):
        report.append({
            "status": "classified",
            "category": g["category"],
            "content_explanation": g["reason"],
            "expected_tenant_name": "أحمد الحبر الشيخ",
            "expected_house_number": "502",
            "date": g["dates"][0]
        })

out_dir = Path("D:/Areas/Safra D/502 - أحمد الحبر الشيخ/.source_files")
with open(out_dir / "502_addition_grouped.json", "w", encoding="utf-8") as f:
    json.dump(groups, f, ensure_ascii=False, indent=2)

with open(out_dir / "502_addition_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("JSON files created successfully!")
