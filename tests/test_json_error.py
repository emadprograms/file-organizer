import os
import json
from dotenv import load_dotenv

load_dotenv()

from src.llm import GemmaClient
from src.schemas import EntityResolutionMapping

def main():
    client = GemmaClient(delay_between_pages=0)
    
    # Create a massive dummy log mimicking 1250 pages
    raw_pages_log = ""
    for i in range(1250):
        raw_pages_log += f"Page {i} | basic_details | ['Mohammed Salem Al-Dosari'] | 2010-05-{i%28+1:02d}\n"
        
    print(f"Calling resolve_entities with {len(raw_pages_log)} bytes of log...")
    
    try:
        res = client.resolve_entities(raw_pages_log)
        print("Success:", len(res))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed with {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
