import json
import os
import fitz
from pathlib import Path

source_dir = Path(r'D:\Areas\Safra C\514 - أسماء خيام محمد الأنصاري\.source_files')
state_file = source_dir / '514_state.json'
vault_dir = source_dir / 'vault'

with open(state_file, 'r', encoding='utf-8') as f:
    state = json.load(f)

# We will read the current grouped_documents and expand them based on physical page counts
old_groups = state.get("grouped_documents", [])
old_manifest = state.get("manifest", {}).get("per_page", [])

# Map vault_id to its old metadata
meta_map = {}
for p in old_manifest:
    vid = p.get("vault_id")
    if vid and vid not in meta_map:
        meta_map[vid] = p

new_cleaned_pages = []
new_grouped_documents = []
new_per_page = []

current_page_idx = 0

# We need to process them in chronological order so the timeline is correct
# Let's sort by date just like reconcile does
sorted_vids = sorted(meta_map.keys(), key=lambda vid: (meta_map[vid].get('dates', [''])[0] if meta_map[vid].get('dates') else '', meta_map[vid].get('page_index', 0)))

for vid in sorted_vids:
    meta = meta_map[vid]
    pdf_path = vault_dir / f"doc_{vid}.pdf"
    
    if not pdf_path.exists():
        continue
        
    doc = fitz.open(str(pdf_path))
    c = doc.page_count
    doc.close()
    
    start_idx = current_page_idx
    end_idx = current_page_idx + c - 1
    
    new_grouped_documents.append({
        "start_page": start_idx,
        "end_page": end_idx,
        "primary_tenant": meta.get("tenant", "Unassigned"),
        "category": meta.get("target_folder", "").split("/")[-1] if "/" in meta.get("target_folder", "") else meta.get("target_folder", "Unassigned"),
        "dates": meta.get("dates", []),
        "brief_arabic_title": meta.get("brief_arabic_title", "Doc"),
        "vault_id": vid,
        "user_locked": True
    })
    
    for i in range(c):
        new_cleaned_pages.append({
            "original_index": current_page_idx,
            "content_explanation": "Restored from shortcut mapping (expanded)",
            "category": meta.get("target_folder", "").split("/")[-1] if "/" in meta.get("target_folder", "") else meta.get("target_folder", "Unassigned"),
            "date": meta.get("date", "nodate"),
            "resolved_date": meta.get("date") if meta.get("date", "nodate") != "nodate" else None,
            "user_locked": True,
            "canonical_tenant": meta.get("tenant", "Unassigned")
        })
        
        new_per_page.append({
            "page_index": current_page_idx,
            "vault_id": vid,
            "output_file": meta.get("output_file"),
            "target_folder": meta.get("target_folder"),
            "dates": meta.get("dates", []),
            "date": meta.get("date", "nodate"),
            "brief_arabic_title": meta.get("brief_arabic_title", "Doc"),
            "user_locked": True,
            "tenant": meta.get("tenant", "Unassigned")
        })
        
        current_page_idx += 1

state["cleaned_pages"] = new_cleaned_pages
state["grouped_documents"] = new_grouped_documents
state["manifest"]["per_page"] = new_per_page
state["manifest"]["summary"]["output_file_count"] = len(meta_map)

with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

print(f"Expanded to {len(new_cleaned_pages)} pages and {len(new_grouped_documents)} groups.")

