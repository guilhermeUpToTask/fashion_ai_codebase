from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, ClassVar, Generic, List, Type, TypeVar, cast
from src.domain.shared.value_objects import EmbeddingData, EmbeddingId, GenericUUID, ImageArtifactID, ImageMetadata, ImageURI

EntityId = TypeVar("EntityId", bound=GenericUUID)


@dataclass
class Entity(Generic[EntityId]):
    id: EntityId = field(compare=False)
    ID_CLASS: ClassVar[Type[GenericUUID]]

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    @classmethod
    def next_id(cls) -> EntityId:
        return cast(EntityId, cls.ID_CLASS.next_id())


#Uselful entities across domains
@dataclass(eq=False)
class Embedding(Entity):
    id: EmbeddingId
    embedding: EmbeddingData
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def vector(self) -> List[float]:
        return self.embedding.vector
@dataclass(eq=False)
class ImageArtifact(Entity):
    id:ImageArtifactID
    blob_ref:ImageURI
    metadata:ImageMetadata
    
    def update_metadata(self, new_metadata: ImageMetadata):
        self.metadata = new_metadata