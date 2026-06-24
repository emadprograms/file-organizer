import os
import requests
import json
from dotenv import load_dotenv

def test_deepseek():
    load_dotenv(dotenv_path=".env")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("No DEEPSEEK_API_KEY found in .env")
        return
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Output a valid JSON object with a single key 'status' and value 'OK'."}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0
    }
    
    print("Pinging DeepSeek API...")
    try:
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            print("[SUCCESS] DeepSeek API works!")
            data = response.json()
            print("Response:", data["choices"][0]["message"]["content"])
        else:
            print(f"[FAILED] HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[FAILED] Exception occurred: {e}")

if __name__ == "__main__":
    test_deepseek()
