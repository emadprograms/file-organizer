import re

def refactor():
    with open("src/llm.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Add import
    if "import concurrent.futures" not in content:
        content = "import concurrent.futures\n" + content

    # Find the target block
    target = '''            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0
                    )
                )'''

    replacement = '''            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        client.models.generate_content,
                        model=model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=response_schema,
                            temperature=0
                        )
                    )
                    try:
                        response = future.result(timeout=90)
                    except concurrent.futures.TimeoutError:
                        raise TimeoutError("LLM API call hung and timed out after 90 seconds.")'''

    if target in content:
        content = content.replace(target, replacement)
    else:
        print("Could not find the target block in llm.py!")
        return

    with open("src/llm.py", "w", encoding="utf-8") as f:
        f.write(content)
        print("Successfully added timeout to _route_llm_call!")

if __name__ == "__main__":
    refactor()
