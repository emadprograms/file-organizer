import os
import json
from src.cache import SimpleCache
from src.schemas import PageClassification, Category

cache = SimpleCache("test_cache.json")
cache.set("1", {
    "residents": ["John Doe"],
    "category": "Basic Details Form",
    "date": "2024-01-01",
    "summary": "This is a test summary."
})

print("Cache contents:", cache.data)
cache2 = SimpleCache("test_cache.json")
print("Cache loaded from disk:", cache2.data)

cache_data = cache2["1"]
try:
    result = PageClassification(**cache_data)
    print("PageClassification:", result)
except Exception as e:
    print("Exception:", e)
