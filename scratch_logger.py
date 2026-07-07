import re
with open('src/logger.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''def log_llm_api_call(request: dict, response: dict, run_id: str):
    """
    Append an LLM API request and response to traces.jsonl.
    """
    payload = {
        "request": request,
        "response": response
    }
    _write_jsonl_trace(run_id, "llm_api", payload)
'''
content = content.replace(target, '')

with open('src/logger.py', 'w', encoding='utf-8') as f:
    f.write(content)
