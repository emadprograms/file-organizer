import re

def refactor():
    with open("src/llm.py", "r", encoding="utf-8") as f:
        content = f.read()

    new_classify_page = '''    def classify_page(self, image_bytes: bytes) -> PageClassification:
        system_prompt = self._build_system_prompt()
        user_prompt = "Classify this scanned document page."
        
        contents = [
            system_prompt,
            user_prompt,
            types.Part.from_bytes(data=image_bytes, mime_type='image/png')
        ]
        
        result = self._route_llm_call(
            model='gemma-4-26b-a4b-it',
            contents=contents,
            response_schema=PageClassification,
            log_prefix="Retry"
        )
        
        if ((not result.residents or result.residents == ["NONE"])
                and result.category.value not in self.NONE_EXPECTED_CATEGORIES):
            retry_prompt = (
                "Classify this scanned document page.\\n\\n"
                "WARNING: You previously returned NONE for the resident name, "
                "but this document category usually has a named person. "
                "Look VERY carefully at every part of the page — headers, "
                "footers, address blocks, body text, stamps, and signatures — "
                "for any Arabic or English name. Extract the FULL name with "
                "all 4-5 parts if possible."
            )
            retry_contents = [
                system_prompt,
                retry_prompt,
                types.Part.from_bytes(data=image_bytes, mime_type='image/png')
            ]
            
            retry_result = self._route_llm_call(
                model='gemma-4-26b-a4b-it',
                contents=retry_contents,
                response_schema=PageClassification,
                log_prefix="'Look Harder' Retry",
                max_attempts=3
            )
            
            if retry_result.residents and retry_result.residents != ["NONE"]:
                result = retry_result

        ANCHOR_CATEGORIES = ["basic_details", "key_handover_form", "contract", "amar_takhsees"]
        if result.category.value in ANCHOR_CATEGORIES:
            verify_prompt = (
                "Classify this scanned document page.\\n\\n"
                f"WARNING: You previously classified this as '{result.category.value}'. "
                "This is an 'Anchor Document' that creates a new resident folder. "
                "Are you absolutely certain? House inspection checklists and photos MUST be 'pictures'. "
                "General letters MUST be 'other_letters'. "
                "Re-evaluate the image carefully. Return the true category and ensure the resident name is perfect."
            )
            v_contents = [
                system_prompt,
                verify_prompt,
                types.Part.from_bytes(data=image_bytes, mime_type='image/png')
            ]
            
            v_result = self._route_llm_call(
                model='gemma-4-31b-it',
                contents=v_contents,
                response_schema=PageClassification,
                log_prefix="Anchor Verification Retry",
                max_attempts=3
            )
            
            result = v_result

        return result
'''

    # Extract original classify_page
    classify_match = re.search(r'    def classify_page\(self, image_bytes: bytes\) -> PageClassification:.*?(?=    def resolve_entities)', content, re.DOTALL)
    if not classify_match:
        print("Could not find classify_page")
        return
        
    content = content.replace(classify_match.group(0), new_classify_page + "\n")

    new_resolve = '''    def resolve_entities(self, raw_pages_log: str) -> dict[str, str]:
        system_prompt = (
            "You are an Arabic document classification expert analyzing a chronological log of documents "
            "[Category, Name, Date] for a single house.\\n\\n"
            "Your task is to resolve ALL unique tenant/resident names mentioned across the files into canonical 'Primary Resident' names.\\n"
            "There may be multiple generations (father, then son inherits) or multiple separate rentals over time.\\n\\n"
            "CRITICAL RULES:\\n"
            "1. Identify the 'Primary Tenants' who signed the contracts or handover forms.\\n"
            "2. Group all variations of a name (e.g., 'محمد علي' and 'المرحوم محمد علي') under the most complete canonical name.\\n"
            "3. Spouses and children (e.g., 'آمنة (زوجة)') MUST be mapped to the Primary Tenant of their era! Do NOT make them their own separate entity.\\n"
            "4. Return a JSON object mapping EVERY EXACT RAW NAME to its canonical Primary Tenant name.\\n\\n"
            "Example Output:\\n"
            "{\\n"
            "  \\"محمد علي أحمد\\": \\"محمد علي أحمد\\",\\n"
            "  \\"محمد علي\\": \\"محمد علي أحمد\\",\\n"
            "  \\"آمنة (زوجة)\\": \\"محمد علي أحمد\\",\\n"
            "  \\"أحمد محمد علي\\": \\"أحمد محمد علي\\"\\n"
            "}"
        )
        user_prompt = f"Resolve the following document log:\\n\\n{raw_pages_log}"
        
        contents = [system_prompt, user_prompt]
        
        result = self._route_llm_call(
            model='gemma-4-26b-a4b-it',
            contents=contents,
            response_schema=EntityResolutionMapping,
            log_prefix="Entity Resolution Retry"
        )
        
        return result.mapping
'''

    resolve_match = re.search(r'    def resolve_entities\(self, raw_pages_log: str\) -> dict\[str, str\]:.*?(?=\s*$)', content, re.DOTALL)
    if not resolve_match:
        print("Could not find resolve_entities")
        return
        
    content = content.replace(resolve_match.group(0), new_resolve)

    with open("src/llm.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    refactor()
