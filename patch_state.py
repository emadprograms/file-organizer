import json
import os
import tempfile
import shutil

filepath = r"D:\areas\Safra D\568 - محمد عمران محمد أسلم\.source_files\568_state.json"

try:
    with open(filepath, 'r', encoding='utf-8') as f:
        state = json.load(f)

    changed = False
    if 'data' in state:
        if 'grouped_documents' in state['data']:
            del state['data']['grouped_documents']
            changed = True
            print("Removed 'grouped_documents'")
        if 'routed_documents' in state['data']:
            del state['data']['routed_documents']
            changed = True
            print("Removed 'routed_documents'")
            
    if changed:
        # Save safely
        dir_name = os.path.dirname(filepath)
        fd, temp_path = tempfile.mkstemp(dir=dir_name)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
        shutil.move(temp_path, filepath)
        print("Successfully patched state file.")
    else:
        print("No keys found to delete, file left unchanged.")
except Exception as e:
    print(f"Error: {e}")
