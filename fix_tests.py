import os

replacements = {
    "client.providers = [mock_provider]": "client.provider = mock_provider",
    "client.providers[0]": "client.provider",
    "llm_client.providers[0]": "llm_client.provider",
    "llm_client.providers = [mock_provider]": "llm_client.provider = mock_provider",
    "self.providers[0]": "self.provider",
}

for root, _, files in os.walk('tests'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
                
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
