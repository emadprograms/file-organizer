import os, sys, shutil, json, subprocess
from pathlib import Path

def repair_house(house_id: str, area_dir: Path):
    print(f"\n--- Repairing {house_id} ---")
    
    # 1. Find the house folder
    house_dir = None
    for d in area_dir.iterdir():
        if d.is_dir() and d.name.startswith(f"{house_id} -"):
            house_dir = d
            break
            
    if not house_dir:
        print(f"House {house_id} not found in {area_dir}")
        return
        
    source_dir = house_dir / ".source_files"
    cleaned_json = source_dir / f"{house_id}_1_cleaned.json"
    tenants_yaml = next(source_dir.glob("*_tenants.yaml"))
    finalized_pdf = house_dir / f"{house_id}_finalized.pdf"
    
    if not cleaned_json.exists():
        print("Missing _1_cleaned.json")
        return
        
    # 2. Generate _report.json from _1_cleaned.json
    with open(cleaned_json, 'r', encoding='utf-8') as f:
        cleaned_data = json.load(f)
        
    report = []
    for c in cleaned_data:
        report.append({
            "status": "classified",
            "category": c.get("category", "others"),
            "dates": [c.get("resolved_date", "1900-01-01")] if c.get("resolved_date") else [],
            "expected_tenant_name": c.get("canonical_tenant", "Unassigned"),
            "content_explanation": "Rebuilt from cleaned JSON"
        })
        
    # 3. Save critical files to a safe temp location
    safe_dir = area_dir / f"{house_id}_repair"
    safe_dir.mkdir(exist_ok=True)
    
    safe_pdf = safe_dir / f"{house_id}_categorized.pdf"
    shutil.copy2(finalized_pdf, safe_pdf)
    
    safe_yaml = safe_dir / f"{house_id}_tenants.yaml"
    shutil.copy2(tenants_yaml, safe_yaml)
    
    with open(safe_dir / f"{house_id}_report.json", "w", encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    # 4. Nuke the old house folder completely
    print(f"Deleting corrupted house folder: {house_dir.name}")
    shutil.rmtree(house_dir)
    
    # 5. Run main pipeline on the repair folder
    print(f"Running main pipeline on {safe_dir.name}")
    cmd = [sys.executable, "src/main.py", "create", str(safe_dir)]
    subprocess.run(cmd, check=True)
    
    print(f"Repair complete for {house_id}!")

if __name__ == "__main__":
    area = Path("D:/Areas/Safra C")
    houses = ["508", "510", "512", "514"]
    for h in houses:
        repair_house(h, area)
