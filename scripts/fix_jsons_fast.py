import json
import os
import re
from pathlib import Path

def sanitize_filename(name: str) -> str:
    # Match the sanitize_filename logic in the codebase
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    return name.strip()

def fix_house(house_id: str, area_dir: Path):
    print(f"\n--- Fixing {house_id} ---")
    house_dir = None
    for d in area_dir.iterdir():
        if d.is_dir() and d.name.startswith(f"{house_id} -"):
            house_dir = d
            break
            
    if not house_dir:
        print(f"House directory not found for {house_id}")
        return
        
    source_dir = house_dir / ".source_files"
    cleaned_path = source_dir / f"{house_id}_1_cleaned.json"
    grouped_path = source_dir / f"{house_id}_2_grouped.json"
    routed_path = source_dir / f"{house_id}_3_routed_and_finalized.json"
    report_path = source_dir / f"{house_id}_report.json"
    
    if not cleaned_path.exists():
        print(f"Missing {cleaned_path.name}")
        return
        
    # 1. Fix _report.json using _1_cleaned.json
    with open(cleaned_path, 'r', encoding='utf-8') as f:
        cleaned_data = json.load(f)
        
    report_data = []
    for c in cleaned_data:
        report_data.append({
            "status": "classified",
            "category": c.get("category", "others"),
            "dates": [c.get("resolved_date", "1900-01-01")] if c.get("resolved_date") else [],
            "expected_tenant_name": c.get("canonical_tenant", "Unassigned"),
            "content_explanation": "Restored mechanically from cleaned json"
        })
        
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print("Fixed _report.json")
    
    # 2. Fix _3_routed_and_finalized.json
    if not routed_path.exists() or not grouped_path.exists():
        print(f"Missing routed or grouped json for {house_id}")
        return
        
    with open(routed_path, 'r', encoding='utf-8') as f:
        routed_data = json.load(f)
        
    with open(grouped_path, 'r', encoding='utf-8') as f:
        grouped_data = json.load(f)
        
    old_per_page = routed_data.get("per_page", [])
    
    # Map old per_page by page_index
    per_page_map = {p["page_index"]: p for p in old_per_page}
    
    total_pages = len(cleaned_data)
    used_pdf_paths = set()
    group_to_pdf = {} # Maps id(group) to the assigned pdf_path
    new_per_page = []
    
    for page_idx in range(total_pages):
        # Find the group containing this page
        group = None
        for g in grouped_data:
            if g["start_page"] <= page_idx <= g["end_page"]:
                group = g
                break
                
        if not group:
            print(f"Warning: Page {page_idx} not found in grouped data!")
            continue
            
        tenant = group.get("primary_tenant", "Unknown")
        folder = group.get("folder_path")
        if not folder:
            # default to category
            GLOBAL_CATEGORY_MAP = {
                "forms": "01_بيانات أساسية",
                "id_cards": "02_بيانات شخصية",
                "letters": "13_رسائل متنوعة",
                "pictures": "11_صور ومعاينات",
                "utility_bills": "06_كهرباء وماء",
                "contracts": "05_عقود"
            }
            cat = group.get("category", "forms")
            folder = GLOBAL_CATEGORY_MAP.get(cat, "00_Unknown")
            
        current_house_dir = area_dir / f"{house_id} - {tenant}"
        if not current_house_dir.exists():
            # Try to find it
            for d in area_dir.iterdir():
                if d.is_dir() and d.name.startswith(house_id):
                    current_house_dir = d
                    break
                    
        # Find the actual tenant folder on disk that starts with this tenant's name
        actual_tenant_folder = tenant
        for d in current_house_dir.iterdir():
            if d.is_dir() and d.name.startswith(tenant):
                actual_tenant_folder = d.name
                break
        
        target_folder = f"{actual_tenant_folder}/{folder}"
        date_str = group["dates"][0] if group.get("dates") else "1900-01-01"
        title = group.get("brief_arabic_title")
        
        full_target_dir = current_house_dir / target_folder
        pdf_path = None
        
        expected_page_count = (group["end_page"] - group["start_page"]) + 1
        
        group_id = id(group)
        if group_id in group_to_pdf:
            pdf_path = group_to_pdf[group_id]
        else:
            if full_target_dir.exists():
                for p in full_target_dir.glob("*.pdf"):
                    if date_str in p.name and p not in used_pdf_paths:
                        try:
                            import fitz
                            doc = fitz.open(str(p))
                            pc = len(doc)
                            doc.close()
                            if pc == expected_page_count:
                                pdf_path = p
                                group_to_pdf[group_id] = pdf_path
                                used_pdf_paths.add(pdf_path)
                                break
                        except Exception:
                            pass
                            
            if not pdf_path:
                if title:
                    expected_filename = f"{date_str} - {sanitize_filename(title)}.pdf"
                else:
                    expected_filename = f"{date_str}.pdf"
                pdf_path = full_target_dir / expected_filename
                group_to_pdf[group_id] = pdf_path
                used_pdf_paths.add(pdf_path)
        
        rel_output_file = f"{current_house_dir.name}/{target_folder}/{pdf_path.name}"
        
        page_in_output = (page_idx - group["start_page"]) + 1
        
        new_entry = {
            "page_index": page_idx,
            "tenant": tenant,
            "date": date_str,
            "output_file": rel_output_file,
            "page_in_output": page_in_output,
            "target_folder": target_folder
        }
        new_per_page.append(new_entry)
            
    # Fix the old per_page entries that might have missing date suffixes
    for entry in new_per_page:
        tenant = entry["tenant"]
        actual_tenant_folder = tenant
        for d in house_dir.iterdir():
            if d.is_dir() and d.name.startswith(tenant):
                actual_tenant_folder = d.name
                break
        # Replace the base tenant name with the actual one in the target_folder and output_file
        parts = entry["target_folder"].split("/", 1)
        if len(parts) == 2 and parts[0] == tenant and actual_tenant_folder != tenant:
            entry["target_folder"] = f"{actual_tenant_folder}/{parts[1]}"
            
        parts = entry["output_file"].split(f"/{tenant}/")
        if len(parts) == 2 and actual_tenant_folder != tenant:
            entry["output_file"] = f"{parts[0]}/{actual_tenant_folder}/{parts[1]}"
            
    # Sort the new per_page list by page_index just to be clean
    new_per_page.sort(key=lambda x: x["page_index"])
    
    routed_data["per_page"] = new_per_page
    if "summary" in routed_data:
        routed_data["summary"]["total_input_pages"] = total_pages
        routed_data["summary"]["total_output_pages"] = total_pages
        routed_data["summary"]["output_file_count"] = len(set(p["output_file"] for p in new_per_page))
        
    with open(routed_path, 'w', encoding='utf-8') as f:
        json.dump(routed_data, f, ensure_ascii=False, indent=2)
        
    print(f"Fixed _3_routed_and_finalized.json (Restored {len(new_per_page) - len(old_per_page)} missing pages)")

if __name__ == "__main__":
    area = Path("D:/Areas/Safra C")
    houses = ["510", "512", "514"]
    for h in houses:
        try:
            fix_house(h, area)
        except Exception as e:
            print(f"Error processing {h}: {e}")
