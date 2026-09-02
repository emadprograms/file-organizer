from pydantic import BaseModel

class TreeItemResponse(BaseModel):
    id: str
    name: str
    type: str
    children: list["TreeItemResponse"] | None = None

print("OK")
