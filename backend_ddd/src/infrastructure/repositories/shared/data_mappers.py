from datetime import datetime
from src.infrastructure.db.data_mapper import DataMapper
from src.domain.shared.entities import Embedding, ImageArtifact
from src.domain.shared.value_objects import (
    EmbeddingId,
    EmbeddingData,
    ImageArtifactID,
    ImageHeight,
    ImageMetadata,
    ImageMimeType,
    ImageURI,
    ImageWidth,
)

from src.infrastructure.repositories.shared.orms import EmbeddingORM, ImageArtifactORM


# TODO:compare pure sqlalchmestry and sqlmodel version if its worth the conversion
class EmbeddingMapper(DataMapper[Embedding, EmbeddingORM]):
    """
    Converts between EmbeddingORM <-> Embedding domain entity.
    """

    def model_to_entity(self, instance: EmbeddingORM) -> Embedding:
        """
        ORM → Domain
        SQLAlchemy JSON column already returns a list of floats.
        """

        return Embedding(
            id=EmbeddingId(str(instance.id)),
            embedding=EmbeddingData(
                vector=instance.vector,
                model_name=instance.model_name,
            ),
            created_at=instance.created_at,
        )

    def entity_to_model(self, entity: Embedding) -> EmbeddingORM:
        """
        Domain → ORM
        We simply assign Python list → JSON column (SQLAlchemy handles it).
        """

        return EmbeddingORM(
            id=str(entity.id),
            model_name=entity.embedding.model_name,
            vector=entity.embedding.vector,
            created_at=entity.created_at,
        )


class ImageArtifactMapper(DataMapper[ImageArtifact, ImageArtifactORM]):
    """
    Converts between ImageArtifactORM <-> ImageArtifact domain entity.
    """

    def model_to_entity(self, instance: ImageArtifactORM) -> ImageArtifact:
        """
        ORM → Domain
        """

        return ImageArtifact(
            id=ImageArtifactID(str(instance.id)),
            blob_ref=ImageURI(instance.blob_ref),
            metadata=ImageMetadata(
                mime_type=ImageMimeType(instance.mime_type),
                width=ImageWidth(instance.width),
                height=ImageHeight(instance.height),
            ),
        )

    def entity_to_model(self, entity: ImageArtifact) -> ImageArtifactORM:
        """
        Domain → ORM
        """

        return ImageArtifactORM(
            id=str(entity.id),
            blob_ref=entity.blob_ref.value,
            mime_type=entity.metadata.mime_type.value,
            width=entity.metadata.width.value,
            height=entity.metadata.height.value,
        )
