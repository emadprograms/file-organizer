import os
import re

base_uh = r"D:\Um alhasam"
additions_dir = r"D:\uh additions"

additions = [f for f in os.listdir(additions_dir) if f.lower().endswith(".pdf")]
results = []

for sub in ["Officer", "Other Ranks"]:
    sub_path = os.path.join(base_uh, sub)
    for folder in sorted(os.listdir(sub_path)):
        fpath = os.path.join(sub_path, folder)
        if not os.path.isdir(fpath):
            continue
        m = re.match(r"^(\d+)", folder)
        h_no = m.group(1) if m else folder

        root_files = [f for f in os.listdir(fpath) if os.path.isfile(os.path.join(fpath, f))]
        root_pdfs = [f for f in root_files if f.lower().endswith(".pdf")]

        all_pdfs = []
        for root, dirs, files in os.walk(fpath):
            for f in files:
                if f.lower().endswith(".pdf"):
                    all_pdfs.append(os.path.join(root, f))

        matching_add = [a for a in additions if a.startswith(h_no)]

        house_pdf = None
        for p in root_pdfs:
            if p.lower() == (h_no + ".pdf").lower():
                house_pdf = p
                break

        results.append({
            "sub": sub,
            "folder": folder,
            "house": h_no,
            "root_pdfs": root_pdfs,
            "house_pdf": house_pdf,
            "total_pdfs": len(all_pdfs),
            "matching_add": matching_add,
            "all_pdfs": [os.path.relpath(p, fpath) for p in all_pdfs]
        })

print(f"Total folders: {len(results)}")
with_house_pdf = [r for r in results if r["house_pdf"]]
without_house_pdf = [r for r in results if not r["house_pdf"]]

print(f"Folders WITH direct house.pdf: {len(with_house_pdf)}")
print(f"Folders WITHOUT direct house.pdf: {len(without_house_pdf)}")

print("\n--- Folders WITHOUT direct house.pdf ---")
for r in without_house_pdf:
    print(f"[{r['sub']}] {r['folder']}")
    print(f"   Matching additions: {r['matching_add']}")
    print(f"   Total PDFs inside: {r['total_pdfs']}")
    print(f"   Root PDFs: {r['root_pdfs']}")
    if r["all_pdfs"]:
        print(f"   Sample PDFs: {r['all_pdfs'][:3]}")

print("\n--- Summary of Additions Matching ---")
all_house_numbers = {r["house"] for r in results}
for add in sorted(additions):
    m = re.match(r"^(\d+)", add)
    h_num = m.group(1) if m else None
    matched_folder = [r for r in results if r["house"] == h_num]
    folder_info = matched_folder[0]["folder"] if matched_folder else "NO MATCHING FOLDER"
    has_house_pdf = matched_folder[0]["house_pdf"] if matched_folder else None
    print(f"Addition {add:35} -> House {h_num:5} in folder '{folder_info}' | has_house_pdf={has_house_pdf}")
