import sys
import json
import os

def merge_jsons(parts_info_json, output_grouped, output_report):
    # parts_info is a list of dicts: {"part_num": 1, "start_page_offset": 0, "grouped_json": "...", "report_json": "..."}
    parts_info = json.loads(parts_info_json)
    
    merged_grouped = []
    merged_report = []
    
    for part in parts_info:
        offset = part['start_page_offset']
        
        # Merge Grouped
        if os.path.exists(part['grouped_json']):
            with open(part['grouped_json'], 'r', encoding='utf-8') as f:
                grouped = json.load(f)
                for g in grouped:
                    g['start_page'] += offset
                    g['end_page'] += offset
                merged_grouped.extend(grouped)
                
        # Merge Report
        if os.path.exists(part['report_json']):
            with open(part['report_json'], 'r', encoding='utf-8') as f:
                report = json.load(f)
                merged_report.extend(report)
                
    # Sort grouped by start_page just in case
    merged_grouped.sort(key=lambda x: x['start_page'])
    
    with open(output_grouped, 'w', encoding='utf-8') as f:
        json.dump(merged_grouped, f, ensure_ascii=False, indent=2)
        
    with open(output_report, 'w', encoding='utf-8') as f:
        json.dump(merged_report, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully merged {len(merged_grouped)} groups and {len(merged_report)} report pages.")

if __name__ == "__main__":
    parts_info_json = sys.argv[1]
    output_grouped = sys.argv[2]
    output_report = sys.argv[3]
    merge_jsons(parts_info_json, output_grouped, output_report)
