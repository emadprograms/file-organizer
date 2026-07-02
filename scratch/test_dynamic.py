import json
from pydantic import create_model, Field

type_mapping = {
    "str": str,
    "list[str]": list[str]
}

model_fields = {
    "residents": (list[str], Field(description="foo")),
    "category": (str, Field(description="bar"))
}

DynamicSchema = create_model('DynamicClassification', **model_fields)

res = DynamicSchema(residents=["Emad"], category="Contract")
print("model_dump:", res.model_dump())
try:
    json.dumps(res.model_dump())
    print("JSON serialize succeeded.")
except Exception as e:
    print("JSON serialize failed:", e)
