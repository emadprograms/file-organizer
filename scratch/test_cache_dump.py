import os
import json
from src.core.cache import SimpleCache
from pydantic import create_model, Field

cache = SimpleCache("scratch/test_pipeline_cache.json")

model_fields = {
    "residents": (list[str], Field(description="foo")),
    "category": (str, Field(description="bar"))
}
DynamicSchema = create_model('DynamicClassification', **model_fields)

res = DynamicSchema(residents=["Emad"], category="Contract")
print(res.model_dump())

try:
    cache.set("1", res.model_dump())
    print("Cache set successful.")
except Exception as e:
    print("Cache set failed:", e)

with open("scratch/test_pipeline_cache.json", "r") as f:
    print("Disk contents:", f.read())
