import json
import glob

def main():
    files = glob.glob("tests/golden_data/*.fine_cache.json")
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        keys_to_delete = []
        for key, val in data.items():
            fine_cat = val.get('fine_category', '')
            if fine_cat in ('07-استقطاع إيجار', '08-وقف استقطاع بدل'):
                keys_to_delete.append(key)
                
        if keys_to_delete:
            for key in keys_to_delete:
                del data[key]
            
            with open(f, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            print(f"Removed {len(keys_to_delete)} entries from {f}")
        else:
            print(f"No changes needed for {f}")

if __name__ == "__main__":
    main()
