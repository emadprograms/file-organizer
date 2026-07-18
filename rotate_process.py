import os
from itertools import cycle

def load_api_keys(env_file_path: str = ".env") -> list[str]:
    """Loads API keys from a .env file.
    
    Supports both KEY=VALUE format and raw keys on each line.
    
    Args:
        env_file_path (str): The path to the .env file. Defaults to ".env".
        
    Returns:
        list[str]: A list of extracted API keys.
    """
    keys = []
    if not os.path.exists(env_file_path):
        print(f"Error: {env_file_path} not found.")
        return keys
        
    with open(env_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ignore empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Extract the value part after '='
            if '=' in line:
                key_value = line.split('=', 1)[1].strip()
                key_value = key_value.strip("'\"")
                if key_value:
                    keys.append(key_value)
            # If it's just a raw key (like a Google API key starting with AIza)
            elif line.startswith('AIza'):
                keys.append(line)
    return keys

def main() -> None:
    """Main execution function to rotate API keys and process directories.
    
    Iterates through paired categorized PDFs and report JSONs, groups them into subdirectories,
    and runs the main categorization script while rotating through available API keys.
    """
    target_dir = r"D:\\Safra D"
    env_path = ".env" # Change this if your .env is located elsewhere
    
    # 1. Load the API keys
    api_keys = load_api_keys(env_path)
    if not api_keys:
        print("No API keys found. Exiting.")
        return
        
    print(f"Loaded {len(api_keys)} API keys.")
    
    # Create an infinite iterator that cycles through the list of keys
    key_cycle = cycle(api_keys)
    
    # 2. Verify the target directory exists
    if not os.path.exists(target_dir):
        print(f"Error: Directory not found -> {target_dir}")
        return
        
    # 3. Group files by base ID and move each pair into its own folder
    # Find all categorized PDFs and corresponding report JSONs
    pdf_files = [f for f in os.listdir(target_dir) if f.endswith('_categorized.pdf')]
    json_files = [f for f in os.listdir(target_dir) if f.endswith('_report.json')]

    # Build a mapping from base ID to its files
    pairs = {}
    for pdf in pdf_files:
        base = pdf.replace('_categorized.pdf', '')
        pairs.setdefault(base, {})['pdf'] = pdf
    for js in json_files:
        base = js.replace('_report.json', '')
        pairs.setdefault(base, {})['json'] = js

    # Create subfolders and move files
    for base, files in pairs.items():
        folder_path = os.path.join(target_dir, base)
        os.makedirs(folder_path, exist_ok=True)
        if 'pdf' in files:
            os.replace(os.path.join(target_dir, files['pdf']), os.path.join(folder_path, files['pdf']))
        if 'json' in files:
            os.replace(os.path.join(target_dir, files['json']), os.path.join(folder_path, files['json']))

    print(f"Created {len(pairs)} subfolders and moved paired files.")

    import subprocess

    # Iterate over each subfolder and run src/main.py with the next API key
    subfolders = [os.path.join(target_dir, d) for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]
    for folder in subfolders:
        # Skip the folder if it does not contain a PDF (e.g., stray directories)
        if not any(f.endswith('_categorized.pdf') for f in os.listdir(folder)):
            continue
        current_api_key = next(key_cycle)
        masked_key = f"{current_api_key[:4]}...{current_api_key[-4:]}" if len(current_api_key) > 8 else "***"
        print(f"Processing folder '{os.path.basename(folder)}' with key {masked_key}")
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = current_api_key
        command = ["python", "src/main.py", folder]
        try:
            subprocess.run(command, env=env, check=True)
            print(f"Successfully processed folder {os.path.basename(folder)}")
        except subprocess.CalledProcessError as e:
            print(f"Error processing folder {os.path.basename(folder)}: {e}")


if __name__ == "__main__":
    main()
