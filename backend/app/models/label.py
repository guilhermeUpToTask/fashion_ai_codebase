from pydantic import BaseModel

#this structured label we will pass to the vector db as metadata
class StructuredLabel(BaseModel):
    category: str
    color: str
    style: str
    pattern: str