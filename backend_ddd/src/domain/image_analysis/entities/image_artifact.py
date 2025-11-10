from dataclasses import dataclass

from src.domain.shared.entities import Entity
from src.domain.image_analysis.value_objects.image_artifact_value_objects import ImageArtifactID, ImageBlob, ImageMetadata, ImageURI
@dataclass(eq=False)
class ImageArtifact(Entity):
    id:ImageArtifactID
    metadata:ImageMetadata
    blob_ref:ImageURI
    
    def update_metadata(self, new_metadata: ImageMetadata):
        self.metadata = new_metadata
        