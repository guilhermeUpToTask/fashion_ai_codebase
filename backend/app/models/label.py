from typing import List
from pydantic import BaseModel

#this structured label we will pass to the vector db as metadata
class StructuredLabel(BaseModel):
    category: str
    color: str
    style: str
    pattern: str
    
class LabelingResponse(BaseModel):
    label_data: StructuredLabel
    # The final vector to be stored in ChromaDB.
    # The ml_service is responsible for merging the image and text vectors.
    storage_vector: List[float]