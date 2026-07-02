import sys
import os
import time

# Create a dummy PDF to process
from src.pipeline import Pipeline

pdf_path = "scratch/test_resume.pdf"
pipeline = Pipeline(api_key="dummy")
# Override the client to simulate a delay and then "crash"
from src.llm import LLMClient
class DummyClient(LLMClient):
    def classify_page_direct(self, img, footer, prompt, fields):
        time.sleep(1)
        from pydantic import create_model, Field
        from typing import Any
        type_mapping = {"str": str, "list[str]": list[str], "int": int, "bool": bool}
        model_fields = {}
        for f in fields:
            t = type_mapping.get(f.type, Any)
            model_fields[f.name] = (t, Field(description=f.description))
        DynamicSchema = create_model('DynamicClassification', **model_fields)
        return DynamicSchema(residents=["Test"], category="Basic Details Form", date="2024-01-01", summary="Test")

pipeline.client = DummyClient(api_key="dummy")

# Run pipeline
try:
    print("Running process_pdf first time...")
    pipeline.process_pdf(pdf_path)
except Exception as e:
    print("Pipeline crashed as expected:", e)

print(f"Cache file exists? {os.path.exists(f'{pdf_path}.cache.json')}")
print("Running process_pdf second time...")
pipeline.process_pdf(pdf_path)
print("Finished!")
