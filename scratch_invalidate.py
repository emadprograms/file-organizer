import json
import os
import shutil

house_dir = r"D:\areas\Safra D\568 - محمد عمران محمد أسلم"
state_file = os.path.join(house_dir, ".source_files", "568_state.json")
checkpoint_file = os.path.join(house_dir, ".source_files", "568_categorization.json")

# 1. Read state.json
with open(state_file, "r", encoding="utf-8") as f:
    state = json.load(f)

# 2. Extract fine_categorized_pages and build _categorization.json
fine_pages = state.get("fine_categorized_pages", [])
pages_data = {}
processed_indices = []

keys_to_delete = []

for idx, page in enumerate(fine_pages):
    cat = page.get("fine_category", "")
    if "01-بيانات أساسية" in cat or "02-بيانات شخصية" in cat:
        # Invalidated! Don't add to processed_indices
        keys_to_delete.append(str(idx))
    else:
        # Valid, keep it in cache
        pages_data[str(idx)] = page
        processed_indices.append(idx)

# Save the surgical checkpoint
checkpoint_data = {
    "processed_indices": processed_indices,
    "pages_data": pages_data
}
with open(checkpoint_file, "w", encoding="utf-8") as f:
    json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

print(f"Surgically invalidated {len(keys_to_delete)} pages: {keys_to_delete}")

# 3. Wipe downstream state so pipeline re-runs from Pass 2
if "fine_categorized_pages" in state:
    del state["fine_categorized_pages"]
if "grouped_documents" in state:
    del state["grouped_documents"]
if "routed_documents" in state:
    del state["routed_documents"]

with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

print("state.json downstream steps wiped. Ready for ultra-fast rerun!")
