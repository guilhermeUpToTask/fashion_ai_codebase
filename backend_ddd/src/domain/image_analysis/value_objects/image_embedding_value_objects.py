from dataclasses import dataclass
from typing import List
from src.domain.shared.value_objects import ValueObject

@dataclass(frozen=True)
class Embedding(ValueObject):
    vector: List[float]
    model_name: str
    dimension: int