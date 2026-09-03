import os
import sys
import glob
import subprocess
import io

# Force UTF-8 for Windows stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

AREA_DIR = r"D:\Areas\Safra C"
ENV_PATH = r"C:\Users\Emad\Documents\GitHub\file-organizer\.env"

def load_keys():
    keys = []
    current_key = None
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines:
        if line.startswith("GEMINI_API_KEY="):
            current_key = line.strip().split("=", 1)[1]
        elif line.startswith("GEMINI_API_KEY_"):
            keys.append(line.strip().split("=", 1)[1])
            
    return keys, current_key

def set_key(new_key):
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("GEMINI_API_KEY="):
                f.write(f"GEMINI_API_KEY={new_key}\n")
            else:
                f.write(line)

def get_raw_houses():
    houses = []
    for entry in os.listdir(AREA_DIR):
        full_path = os.path.join(AREA_DIR, entry)
        if os.path.isdir(full_path):
            # If it doesn't have " - " it's a raw house directory
            if " - " not in entry:
                houses.append(entry)
    # Sort alphabetically
    houses.sort()
    return houses

def run_pipeline():
    keys, current_key = load_keys()
    if not keys:
        print("No numbered keys found in .env!")
        return

    try:
        current_idx = keys.index(current_key)
    except ValueError:
        current_idx = 0
        
    houses = get_raw_houses()
    print(f"Found {len(houses)} raw houses to process.")
    
    for house in houses:
        print(f"\n{'='*50}\nStarting house: {house}\n{'='*50}")
        
        current_idx = (current_idx + 1) % len(keys)
        next_key = keys[current_idx]
        set_key(next_key)
        print(f"Rotated to next key (Index {current_idx}) before starting {house}.")
        
        raw_house_path = os.path.join(AREA_DIR, house)
        
        while True:
            print(f"Running ingest for {house}...")
            # Use utf-8 encoding for subprocess environment
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run([sys.executable, "src/main.py", "ingest", raw_house_path], cwd=r"C:\Users\Emad\Documents\GitHub\file-organizer", env=env)
            
            if result.returncode == 0:
                break
            else:
                print(f"Ingest failed for {house}. Possibly mid-house quota limit. Rotating key and retrying...")
                current_idx = (current_idx + 1) % len(keys)
                next_key = keys[current_idx]
                set_key(next_key)
        
        print(f"Ingest complete. Finding renamed folder for {house}...")
        renamed_dirs = glob.glob(os.path.join(AREA_DIR, f"{house} - *"))
        if not renamed_dirs:
            print(f"ERROR: Could not find renamed directory for {house}. Skipping reconcile.")
            continue
            
        renamed_house_path = renamed_dirs[0]
        print(f"Running reconcile for {renamed_house_path}...")
        
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run([sys.executable, "src/main.py", "reconcile", renamed_house_path], cwd=r"C:\Users\Emad\Documents\GitHub\file-organizer", env=env)
        if result.returncode != 0:
            print(f"ERROR: Reconcile failed for {renamed_house_path}")
            
    print("\nAll houses processed!")

if __name__ == '__main__':
    run_pipeline()
