
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from src.domain.shared.entities import Entity
from backend_ddd.src.domain.image_analysis.value_objects.embedding_value_objects import EmbeddingData, EmbeddingId
from src.domain.image_analysis.value_objects.clothing_item_value_objects import ClothingItemId

@dataclass(eq=False)
class Embedding(Entity):
    id: EmbeddingId
    embedding: EmbeddingData
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def vector(self) -> List[float]:
        return self.embedding.vector