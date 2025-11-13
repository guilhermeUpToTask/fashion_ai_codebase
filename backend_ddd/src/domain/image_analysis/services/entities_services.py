from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.image_analysis.entities.image_artifact import ImageArtifact


class ClothingItemService:
    def get_source_image(self, item: ClothingItem) -> ImageArtifact:
        raise NotImplemented