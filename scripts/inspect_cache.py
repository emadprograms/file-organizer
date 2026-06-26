import json

with open('621.pdf.cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

print("Basic Details Pages:")
for page_idx, page_data in sorted(cache.items(), key=lambda x: int(x[0])):
    res = page_data.get('residents', [])
    cat = page_data.get('category')
    date = page_data.get('date')
    if cat == 'basic_details':
        print(f"Page {page_idx}: {cat} | {res} | {date}")

print("\nMajid Pages:")
for page_idx, page_data in sorted(cache.items(), key=lambda x: int(x[0])):
    res = page_data.get('residents', [])
    cat = page_data.get('category')
    date = page_data.get('date')
    res_str = " ".join(res).upper()
    if 'MAJID' in res_str or 'ماجد' in res_str:
        print(f"Page {page_idx}: {cat} | {res} | {date}")
