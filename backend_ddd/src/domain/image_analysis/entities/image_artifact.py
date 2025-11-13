from dataclasses import dataclass

from src.domain.shared.entities import Entity
from src.domain.image_analysis.value_objects.image_artifact_vos import ImageArtifactID, ImageMetadata, ImageURI
@dataclass(eq=False)
class ImageArtifact(Entity):
    id:ImageArtifactID
    blob_ref:ImageURI
    metadata:ImageMetadata
    
    def update_metadata(self, new_metadata: ImageMetadata):
        self.metadata = new_metadata
        