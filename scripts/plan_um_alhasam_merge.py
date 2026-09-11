import os
import re
import fitz

base_uh = r'D:\Um alhasam'
add_dir = r'D:\uh additions'

additions = [f for f in os.listdir(add_dir) if f.lower().endswith('.pdf')]

folders = {}
for sub in ['Officer', 'Other Ranks']:
    sub_path = os.path.join(base_uh, sub)
    for f in sorted(os.listdir(sub_path)):
        m = re.match(r'^(\d+)', f)
        if m:
            folders[m.group(1)] = (sub, f, os.path.join(sub_path, f))

plan = []

for h_no in sorted(folders.keys(), key=lambda x: int(x)):
    sub, f_name, fpath = folders[h_no]

    if h_no in ['1150', '1165', '1174', '1460', '1470', '1474']:
        print(f'SKIP {h_no:5} ({f_name}) -> No base file')
        continue

    base_file = os.path.join(fpath, f'{h_no}.pdf')
    parts = []

    if os.path.exists(base_file):
        parts = [base_file]
    elif h_no == '1526':
        p4 = os.path.join(fpath, '4_Yousuf Ahmed Al Mansoori', 'Yousuf Ahmed Al Mansoori.pdf')
        p3 = os.path.join(fpath, '3_Khalifa Mohammad Ahmed Ajaj', 'Khalifa Mohammad Ahmed Ajaj.pdf')
        p3_1 = os.path.join(fpath, '3-1_Ali Faisal Sabhi - DIDNT STAY (scan only).pdf')
        p2 = os.path.join(fpath, "2_Abdul Rehman Abdullah Sa'ad Abdullah (scan only).pdf")
        p1 = os.path.join(fpath, '1_Nabeel Yousuf Al Kawari (scan only).pdf')
        parts = [p4, p3, p3_1, p2, p1]
    elif h_no == '1462':
        parts = [os.path.join(fpath, 'Noman Hassan Essa (Scan only).pdf')]
    else:
        subdirs = [d for d in os.listdir(fpath) if os.path.isdir(os.path.join(fpath, d))]
        for sd in subdirs:
            for f in os.listdir(os.path.join(fpath, sd)):
                if f.lower().endswith('.pdf') and not any(k in f for k in ['_10', '_11', '_12', '_13', '_1.', '_2.', '_3.', '_4.', '_5.', '_6.', '_7.', '_8.', '_9.', 'البيانات']):
                    parts.append(os.path.join(fpath, sd, f))

    add_file = None
    if h_no == '1536':
        add_file = os.path.join(add_dir, '1536 - new guy.pdf')
    else:
        m_add = [a for a in additions if a.startswith(h_no) and 'wrong' not in a]
        if m_add:
            add_file = os.path.join(add_dir, m_add[0])

    base_pages = 0
    for p in parts:
        try:
            d = fitz.open(p)
            base_pages += len(d)
            d.close()
        except Exception as e:
            print(f'Error opening {p}: {e}')

    add_pages = 0
    if add_file:
        try:
            d = fitz.open(add_file)
            add_pages = len(d)
            d.close()
        except Exception as e:
            print(f'Error opening addition {add_file}: {e}')

    plan.append({
        'house': h_no,
        'parts': parts,
        'base_pages': base_pages,
        'add_file': add_file,
        'add_pages': add_pages,
        'total_pages': base_pages + add_pages
    })

print(f'\nTotal houses to process: {len(plan)}')
for item in plan:
    add_name = os.path.basename(item['add_file']) if item['add_file'] else 'No addition'
    add_info = f'+ {add_name} ({item["add_pages"]} pgs)' if item['add_file'] else 'No addition'
    print(f'House {item["house"]:5} | Parts: {len(item["parts"]):1} | Base: {item["base_pages"]:3} pgs | {add_info:40} | Total: {item["total_pages"]:3} pgs')
