import json
from pathlib import Path
import sys

def main(old_path, new_path):
    with open(old_path, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    with open(new_path, 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    # Build a map of page -> old document
    old_page_map = {}
    for d in old_data:
        for p in range(d.get('start_page', 0), d.get('end_page', 0) + 1):
            old_page_map[p] = d

    # Build a map of page -> new document
    new_page_map = {}
    for d in new_data:
        for p in range(d.get('start_page', 0), d.get('end_page', 0) + 1):
            new_page_map[p] = d

    print("--- DIRECT COMPARISON (Only Showing Differences) ---")
    
    current_page = 0
    while current_page < 125: # 125 pages total
        old_doc = old_page_map.get(current_page)
        new_doc = new_page_map.get(current_page)
        
        if not old_doc or not new_doc:
            current_page += 1
            continue
            
        old_bounds = (old_doc.get('start_page', 0), old_doc.get('end_page', 0))
        new_bounds = (new_doc.get('start_page', 0), new_doc.get('end_page', 0))
        
        old_cat = old_doc.get('folder_path', 'Unrouted')
        new_cat = new_doc.get('folder_path', 'Unrouted')
        
        if old_bounds != new_bounds or old_cat != new_cat:
            # It's a difference!
            # Let's find the max bound of the differing block
            max_bound = max(old_bounds[1], new_bounds[1])
            
            print(f"\nConflict Block: Pages {current_page} to {max_bound}")
            
            # Print old groupings in this block
            print("  OLD PIPELINE DID:")
            p = current_page
            while p <= max_bound:
                od = old_page_map.get(p)
                if od:
                    print(f"    - Grouped {od.get('start_page')}-{od.get('end_page')} -> {od.get('folder_path', 'Unrouted')}")
                    p = od.get('end_page') + 1
                else:
                    p += 1
                    
            # Print new groupings in this block
            print("  NEW PIPELINE DID:")
            p = current_page
            while p <= max_bound:
                nd = new_page_map.get(p)
                if nd:
                    print(f"    - Grouped {nd.get('start_page')}-{nd.get('end_page')} -> {nd.get('folder_path', 'Unrouted')}")
                    p = nd.get('end_page') + 1
                else:
                    p += 1
            
            current_page = max_bound + 1
        else:
            current_page = old_bounds[1] + 1

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
