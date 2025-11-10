from dataclasses import dataclass
from typing import List
from src.domain.shared.value_objects import GenericUUID, ValueObject

class EmbeddingId(GenericUUID):
    pass

@dataclass(frozen=True)
class EmbeddingData(ValueObject):
    vector: List[float]
    model_name: str
    
    @property
    def dimension(self) -> int:
        return len(self.vector)