from dataclasses import dataclass
from src.domain.image_analysis.errors import InvalidLabel
from src.domain.image_analysis.value_objects.image_artifact_value_objects import (
    ImageArtifactID,
)
from src.domain.image_analysis.value_objects.image_analysis_value_objects import (
    ImageAnalysisID,
)
from src.domain.shared.entities import Entity
from src.domain.image_analysis.value_objects.clothing_item_value_objects import (
    ClothingItemId,
    Label,
    BoundingBox,
)
from backend_ddd.src.domain.image_analysis.entities.embedding import EmbeddingId


@dataclass(eq=False)
class ClothingItem(Entity):
    id: ClothingItemId
    image_aggregate_id: ImageAnalysisID
    cropped_image_id: ImageArtifactID | None
    embedding_id: EmbeddingId | None
    label: Label | None
    bbox: BoundingBox

    def attach_label(self, label: Label):
        if len(str(label).strip()) == 0:
            raise InvalidLabel("label cannot be empty")
        self.label = label

    def attach_cropped_image(self, artifact_id: ImageArtifactID):
        self.cropped_image_id = artifact_id

    def attach_embedding(self, embedding_id: EmbeddingId):
        self.embedding_id = embedding_id
