import json
import os
from pathlib import Path

target_dir = Path(r"D:\areas\Safra D\568 - محمد عمران محمد أسلم")
source_files = target_dir / ".source_files"
report_path = source_files / "568_report.json"
cache_path = source_files / "568_categorization.json"

FOLDER_PREFIXES = {
    "بيانات أساسية": "01",
    "بيانات شخصية": "02",
    "أمر تخصيص": "03",
    "محضر تسليم مفتاح": "04",
    "عقود": "05",
    "كهرباء وماء": "06",
    "استقطاع إيجار": "07",
    "وقف استقطاع بدل": "08",
    "إشعارات": "09",
    "صيانة": "10",
    "صور ومعاينات": "11",
    "تعديلات": "12",
    "رسائل متنوعة": "13",
}

if not report_path.exists():
    print(f"Report not found at {report_path}")
    exit(1)

with open(report_path, "r", encoding="utf-8") as f:
    report = json.load(f)

processed_indices = []
pages_data = {}

for doc in report:
    folder_path = doc.get("folder_path", "")
    prefix = FOLDER_PREFIXES.get(folder_path, "")
    if not prefix:
        continue
        
    category = f"{prefix}-{folder_path}"
    
    if category in ["01-بيانات أساسية", "02-بيانات شخصية"]:
        # Skip these to force LLM to re-evaluate
        continue
        
    start_page = doc.get("start_page", 0)
    end_page = doc.get("end_page", 0)
    reason = doc.get("reason", "")
    
    for i in range(start_page, end_page + 1):
        processed_indices.append(i)
        pages_data[str(i)] = {
            "category": category,
            "reason": reason
        }

with open(cache_path, "w", encoding="utf-8") as f:
    json.dump({
        "processed_indices": processed_indices,
        "pages_data": pages_data
    }, f, ensure_ascii=False, indent=2)

print(f"Reconstructed cache saved to {cache_path}. Skipped pages routed to 01 and 02. Total preserved pages: {len(processed_indices)}.")
