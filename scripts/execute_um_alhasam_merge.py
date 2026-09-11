import os
import re
import fitz

base_uh = r'D:\Um alhasam'
add_dir = r'D:\uh additions'
out_dir = r'D:\Um Al Hasam Merged'

os.makedirs(out_dir, exist_ok=True)

additions = [f for f in os.listdir(add_dir) if f.lower().endswith('.pdf')]

folders = {}
for sub in ['Officer', 'Other Ranks']:
    sub_path = os.path.join(base_uh, sub)
    for f in sorted(os.listdir(sub_path)):
        m = re.match(r'^(\d+)', f)
        if m:
            folders[m.group(1)] = (sub, f, os.path.join(sub_path, f))

skip_houses = {'1150', '1165', '1174', '1460', '1470', '1474'}

success_count = 0
fail_count = 0

for h_no in sorted(folders.keys(), key=lambda x: int(x)):
    sub, f_name, fpath = folders[h_no]

    if h_no in skip_houses:
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

    expected_pages = 0
    doc_out = fitz.open()

    # Prepend addition if present
    if add_file:
        d_add = fitz.open(add_file)
        expected_pages += len(d_add)
        doc_out.insert_pdf(d_add)
        d_add.close()

    # Then insert parts
    for p in parts:
        d_p = fitz.open(p)
        expected_pages += len(d_p)
        doc_out.insert_pdf(d_p)
        d_p.close()

    out_file = os.path.join(out_dir, f'{h_no}.pdf')
    doc_out.save(out_file, garbage=3, deflate=True)
    doc_out.close()

    # Verify
    doc_check = fitz.open(out_file)
    actual_pages = len(doc_check)
    doc_check.close()

    if actual_pages == expected_pages:
        add_desc = f' (with {os.path.basename(add_file)})' if add_file else ''
        print(f'[OK] House {h_no:5} -> {actual_pages:3} pages{add_desc}')
        success_count += 1
    else:
        print(f'[FAIL] House {h_no:5} -> expected {expected_pages}, got {actual_pages}')
        fail_count += 1

print(f'\nFinished: {success_count} succeeded, {fail_count} failed.')
