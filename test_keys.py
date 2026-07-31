import os
from google import genai
from google.genai.errors import APIError

with open('.env', 'r') as f:
    lines = f.read().splitlines()

keys = []
for line in lines:
    line = line.strip()
    if line.startswith('GEMINI_API_KEY='):
        keys.append(line.split('=', 1)[1])
    elif line.startswith('AIza'):
        keys.append(line)

for key in keys:
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Hi'
        )
        print(f"Key {key[:10]}... WORKED!")
        break
    except APIError as e:
        print(f"Key {key[:10]}... failed: {e.code}")
    except Exception as e:
        if "429" in str(e):
             print(f"Key {key[:10]}... failed: 429")
        elif "403" in str(e):
             print(f"Key {key[:10]}... failed: 403")
        else:
             print(f"Key {key[:10]}... failed with generic error: {type(e)}")

