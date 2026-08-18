import subprocess, time, os, glob

print('Waiting for the massive 900-block batch to finish before starting House 711...')

# Poll every 5 minutes to see if the main batch script is still running
while True:
    try:
        output = subprocess.check_output('wmic process where "name=\'python.exe\'" get commandline', shell=True, text=True)
        if '962' in output and 'key_numbers' in output:
            time.sleep(300)
            continue
    except Exception as e:
        pass
    break

print('\nPrevious batch detected as finished! Waiting 5 minutes for OS flush...')
time.sleep(300)

# Extract Key 13 from .env
key_13_val = None
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('GEMINI_API_KEY_13='):
            key_13_val = line.strip().split('=')[1]
            break

if key_13_val:
    print('Swapping to API Key 13...')
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    with open('.env', 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('GEMINI_API_KEY=') and not line.startswith('GEMINI_API_KEY_'):
                f.write(f'GEMINI_API_KEY={key_13_val}\n')
            else:
                f.write(line)
                
    paths = glob.glob(r'D:\areas\Safra D\711*')
    if paths:
        house_path = paths[0]
        
        print('\nStarting CREATE for House 711...')
        subprocess.run(['python', 'src/main.py', 'create', house_path, '--model', 'gemma-4-31b-it', '--categorization-model', 'gemini-3.5-flash-lite'])
        
        print('\nStarting VERIFY for House 711...')
        subprocess.run(['python', 'src/main.py', 'verify', house_path])
    else:
        print('House 711 not found!')
else:
    print('Could not find Key 13 in .env')
