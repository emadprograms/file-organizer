import json

with open(r'C:\Users\Emad\Documents\Safra C\1249.pdf.cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

pages = sorted([(int(k), v) for k, v in cache.items()], key=lambda x: x[0])

with open(r'C:\Users\Emad\Documents\GitHub\File-Categorizer\check_output.txt', 'w', encoding='utf-8') as out:
    for i in range(len(pages)-1):
        idx1, p1 = pages[i]
        idx2, p2 = pages[i+1]
        if p1['category'] == p2['category'] and p1['date'] != 'NONE' and p2['date'] != 'NONE' and p1['date'] != p2['date']:
            out.write("Consecutive pages with same category but DIFFERENT dates:\n")
            out.write(f"Page {idx1}: {p1['category']} | Date: {p1['date']}\n")
            out.write(f"Page {idx2}: {p2['category']} | Date: {p2['date']}\n")
            out.write('-'*40 + '\n')
