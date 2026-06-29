import json
import os
import textwrap
import sys
import io
from tabulate import tabulate
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Use chr(10) to represent newline to avoid potential tool mangling of 

NL = chr(10)

def wrap_text(text, width):
    if not text:
        return ""
    lines = textwrap.wrap(str(text), width=width)
    return NL.join(lines)

def format_residents(residents_list, width):
    if not residents_list:
        return ""
    wrapped_lines = []
    for res in residents_list:
        if res.strip():
            wrapped_lines.append(wrap_text(res.strip(), width))
    return NL.join(wrapped_lines)

def compare_json_files(file1_path, file2_path, output_path):
    if not os.path.exists(file1_path):
        print(f"Error: File not found: {file1_path}")
        return
    if not os.path.exists(file2_path):
        print(f"Error: File not found: {file2_path}")
        return

    with open(file1_path, 'r', encoding='utf-8') as f1, open(file2_path, 'r', encoding='utf-8') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    all_pages = sorted(set(data1.keys()) | set(data2.keys()), key=lambda x: int(x))

    differences = []

    NAME_WIDTH = 30
    CAT_WIDTH = 25
    SUM_WIDTH = 50

    for page in all_pages:
        p_str = str(page)
        val1 = data1.get(p_str, {})
        val2 = data2.get(p_str, {})

        if val1 != val2:
            fields_to_compare = {
                "Residents": ("residents", NAME_WIDTH, format_residents),
                "Classification": ("category", CAT_WIDTH, wrap_text),
                "Summary": ("summary", SUM_WIDTH, wrap_text)
            }

            for field_label, (field_key, width, formatter) in fields_to_compare.items():
                v1 = val1.get(field_key) if isinstance(val1, dict) else None
                v2 = val2.get(field_key) if isinstance(val2, dict) else None

                if v1 != v2:
                    orig_display = ""
                    clean_display = ""

                    if v1 is not None:
                        orig_display = formatter(v1, width) if field_key == "residents" else wrap_text(v1, width)
                    
                    if v2 is not None:
                        clean_display = formatter(v2, width) if field_key == "residents" else wrap_text(v2, width)

                    differences.append([
                        page,
                        field_label,
                        orig_display,
                        clean_display
                    ])

    if differences:
        headers = ["Page", "Field", "Original (1281)", "Cleaned (1281_cleaned)"]
        table = tabulate(differences, headers=headers, tablefmt="grid")
        
        # Print the table first
        print(table)
        
        # Then show where the differences are
        print("\n" + "="*50)
        print("ANALYSIS OF DIFFERENCES")
        print("="*50)
        
        changes = {'Residents': [], 'Classification': [], 'Summary': []}
        for diff in differences:
            field_label = diff[1]
            orig_val = diff[2].replace(NL, ' ')
            clean_val = diff[3].replace(NL, ' ')
            if field_label in changes:
                changes[field_label].append((orig_val.strip(), clean_val.strip()))
        
        print('\nResidents changes:', len(changes['Residents']))
        print('Classification changes:', len(changes['Classification']))
        print('Summary changes:', len(changes['Summary']))

        print('\nSample Classification changes:')
        class_counter = Counter([(o, c) for o, c in changes['Classification']])
        for (o, c), count in class_counter.most_common(10):
            print(f'{count} times: {o} -> {c}')

        print('\nSample Residents changes:')
        res_counter = Counter([(o, c) for o, c in changes['Residents']])
        for (o, c), count in res_counter.most_common(10):
            print(f'{count} times: {o} -> {c}')
            
        # Write table to file as well
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(table)
        print(f"\nDifferences table written to {output_path}")
            
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("No differences found between the two files.")
        print(f"No differences found. Result written to {output_path}")

if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels since script is in scratch/3_uncleaned_vs_cleaned_data_study/
    BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    
    FILE1 = os.path.join(BASE_DIR, "pdfs", "1281.pdf.cache.json")
    FILE2 = os.path.join(BASE_DIR, "pdfs", "1281_cleaned.pdf.cache.json")
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "comparison_results.txt")

    compare_json_files(FILE1, FILE2, OUTPUT_FILE)
