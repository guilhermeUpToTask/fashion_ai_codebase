from dataclasses import dataclass
from src.domain.image_analysis.errors import InvariantViolationException
from src.domain.shared.value_objects import (
    ImageArtifactID,
)
from src.domain.image_analysis.value_objects.image_analysis_vos import (
    ImageAnalysisID,
)
from src.domain.shared.entities import Entity
from src.domain.image_analysis.value_objects.clothing_item_vos import (
    ClothingItemId,
    Label,
    BoundingBox,
)
from src.domain.shared.entities import EmbeddingId


@dataclass(eq=False)
class ClothingItem(Entity):
    id: ClothingItemId
    image_aggregate_id: ImageAnalysisID
    cropped_image_id: ImageArtifactID | None
    embedding_id: EmbeddingId | None
    label: Label | None
    bbox: BoundingBox

    def attach_label(self, label: Label):
        if self.label is not None:
            raise InvariantViolationException(
                f"Label already attached to item {self.id}."
            )
        self.label = label

    def attach_cropped_image(self, artifact_id: ImageArtifactID):
        if self.cropped_image_id is not None:
            raise InvariantViolationException(
                f"Item {self.id} already has an cropped image artifact."
            )
        self.cropped_image_id = artifact_id

    def attach_embedding(self, embedding_id: EmbeddingId):
        if self.embedding_id is not None:
            raise InvariantViolationException(
                f"Item {self.id} already has an embedding."
            )
        self.embedding_id = embedding_id
