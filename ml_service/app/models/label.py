from pydantic import BaseModel
from typing import List, Dict

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
    
class  BestMatching(BaseModel):
    index: int
    text: str
    score: float
    
class MatchingRequestBody(BaseModel):
    candidates: List[str]
    target: str
