import fitz
import json
import os
import shutil
from pathlib import Path

def fix_pdf(pdf_path, num_pages_to_move):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Not found: {pdf_path}")
        return
        
    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count
    
    if num_pages_to_move >= total_pages:
        print(f"Skipping {pdf_path}, too few pages.")
        return
        
    new_doc = fitz.open()
    
    # 1. Insert last N pages
    new_doc.insert_pdf(doc, from_page=total_pages - num_pages_to_move, to_page=total_pages - 1)
    
    # 2. Insert rest of pages
    new_doc.insert_pdf(doc, from_page=0, to_page=total_pages - num_pages_to_move - 1)
    
    # 3. Fix TOC
    toc = doc.get_toc()
    new_toc = []
    
    old_pages_start = total_pages - num_pages_to_move + 1
    
    for item in toc:
        lvl, title, page = item
        if page >= old_pages_start:
            new_page = page - old_pages_start + 1
        else:
            new_page = page + num_pages_to_move
        new_toc.append([lvl, title, new_page])
        
    front_toc = []
    back_toc = []
    for item in new_toc:
        if item[2] <= num_pages_to_move:
            front_toc.append(item)
        else:
            back_toc.append(item)
            
    final_toc = front_toc + back_toc
    new_doc.set_toc(final_toc)
    
    fixed_path = str(pdf_path) + ".fixed.pdf"
    new_doc.save(fixed_path)
    new_doc.close()
    doc.close()
    
    shutil.move(fixed_path, str(pdf_path))
    print(f"Fixed PDF {pdf_path}")
    
def fix_json_structure(house_dir, house_id, num_pages_to_move, total_pages):
    source_dir = house_dir / ".source_files"
    old_pages_start = total_pages - num_pages_to_move
    
    # 1. report.json
    rep_path = source_dir / f"{house_id}_report.json"
    if rep_path.exists():
        with open(rep_path, 'r', encoding='utf-8') as f:
            rep = json.load(f)
        if isinstance(rep, list) and len(rep) == total_pages:
            rep = rep[-num_pages_to_move:] + rep[:-num_pages_to_move]
            with open(rep_path, 'w', encoding='utf-8') as f:
                json.dump(rep, f, ensure_ascii=False, indent=2)
                
    # 2. grouped.json
    grp_path = source_dir / f"{house_id}_2_grouped.json"
    if grp_path.exists():
        with open(grp_path, 'r', encoding='utf-8') as f:
            grp = json.load(f)
        if isinstance(grp, list):
            for doc in grp:
                if doc['start_page'] >= old_pages_start:
                    doc['start_page'] -= old_pages_start
                    doc['end_page'] -= old_pages_start
                else:
                    doc['start_page'] += num_pages_to_move
                    doc['end_page'] += num_pages_to_move
            grp.sort(key=lambda x: x['start_page'])
            with open(grp_path, 'w', encoding='utf-8') as f:
                json.dump(grp, f, ensure_ascii=False, indent=2)
                
    # 3. routed_and_finalized.json
    rout_path = source_dir / f"{house_id}_3_routed_and_finalized.json"
    if rout_path.exists():
        with open(rout_path, 'r', encoding='utf-8') as f:
            rout = json.load(f)
        
        if 'per_page' in rout:
            for p in rout['per_page']:
                if p['page_index'] >= old_pages_start:
                    p['page_index'] -= old_pages_start
                else:
                    p['page_index'] += num_pages_to_move
            rout['per_page'].sort(key=lambda x: x['page_index'])
            
        if 'grouped' in rout:
            for doc in rout['grouped']:
                if 'original_index' in doc:
                    if doc['original_index'] >= old_pages_start:
                        doc['original_index'] -= old_pages_start
                    else:
                        doc['original_index'] += num_pages_to_move
                        
                if 'start_page' in doc:
                    if doc['start_page'] >= old_pages_start:
                        doc['start_page'] -= old_pages_start
                        doc['end_page'] -= old_pages_start
                    else:
                        doc['start_page'] += num_pages_to_move
                        doc['end_page'] += num_pages_to_move
            rout['grouped'].sort(key=lambda x: x.get('start_page', 0))
            
        with open(rout_path, 'w', encoding='utf-8') as f:
            json.dump(rout, f, ensure_ascii=False, indent=2)

def fix_house(house_dir, num_pages_to_move, house_id, fix_pdf_flag=True):
    pdf_path = house_dir / f"{house_id}_finalized.pdf"
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return
        
    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count
    doc.close()
    
    if fix_pdf_flag:
        fix_pdf(pdf_path, num_pages_to_move)
    
    fix_json_structure(house_dir, house_id, num_pages_to_move, total_pages)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    house_dir_504 = Path("D:/Areas/Safra D/504 - أحمد يوسف المريسل")
    fix_house(house_dir_504, 5, "504", fix_pdf_flag=False)
    
    fix_house(Path("D:/Areas/Safra D/502 - أحمد الحبر الشيخ"), 54, "502", fix_pdf_flag=True)
