from sqlmodel import Session, select

from src.domain.shared.entities import Embedding, ImageArtifact
from src.domain.shared.value_objects import EmbeddingId, ImageArtifactID
from src.domain.shared.specifications import Specification
from src.infrastructure.repositories.shared.data_mappers import (
    EmbeddingMapper,
    ImageArtifactMapper,
)
from src.infrastructure.repositories.shared.orms import EmbeddingORM, ImageArtifactORM
from src.infrastructure.db.specification_visitor import SQLModelSpecificationVisitor


class SQLModelEmbeddingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.mapper = EmbeddingMapper()
        self.visitor = SQLModelSpecificationVisitor(
            field_map={
                "model_name": EmbeddingORM.model_name,
                "created_at": EmbeddingORM.created_at,
            }
        )

    def add(self, embedding: Embedding) -> None:
        orm = self.mapper.entity_to_model(embedding)
        self.session.add(orm)

    def get_by_id(self, embedding_id: EmbeddingId) -> Embedding | None:
        orm = self.session.get(EmbeddingORM, str(embedding_id))
        if orm:
            return self.mapper.model_to_entity(orm)
        return None

    def list_all(self) -> list[Embedding]:
        rows = self.session.exec(select(EmbeddingORM)).all()
        return [self.mapper.model_to_entity(row) for row in rows]

    def find_by_specification(self, spec: Specification | None) -> list[Embedding]:
        stmt = select(EmbeddingORM)

        if spec:
            predicate = spec.accept(self.visitor)
            stmt = stmt.where(predicate)

        rows = self.session.exec(stmt).all()
        return [self.mapper.model_to_entity(row) for row in rows]

    def update(self, embedding: Embedding) -> Embedding:
        orm = self.session.get(EmbeddingORM, str(embedding.id))
        if not orm:
            raise ValueError("Embedding not found")

        updated = self.mapper.entity_to_model(embedding)

        orm.sqlmodel_update(updated)
        self.session.add(orm)

        return self.mapper.model_to_entity(orm)

    def delete(self, embedding_id: EmbeddingId) -> None:
        orm = self.session.get(EmbeddingORM, str(embedding_id))
        if orm:
            self.session.delete(orm)

    def flush(self) -> None:
        self.session.flush()


class SQLModelImageArtifactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.mapper = ImageArtifactMapper()
        self.visitor = SQLModelSpecificationVisitor(
            field_map={
                "mime_type": ImageArtifactORM.mime_type,
            }
        )

    def add(self, image_artifact: ImageArtifact) -> None:
        orm = self.mapper.entity_to_model(image_artifact)
        self.session.add(orm)

    def get_by_id(self, image_artifact_id: ImageArtifactID) -> ImageArtifact | None:
        orm = self.session.get(ImageArtifactORM, str(image_artifact_id))
        if orm:
            return self.mapper.model_to_entity(orm)
        return None

    def list_all(self) -> list[ImageArtifact]:
        rows = self.session.exec(select(ImageArtifactORM)).all()
        return [self.mapper.model_to_entity(row) for row in rows]

    def find_by_specification(self, spec: Specification | None) -> list[ImageArtifact]:
        stmt = select(ImageArtifactORM)

        if spec:
            predicate = spec.accept(self.visitor)
            stmt = stmt.where(predicate)

        rows = self.session.exec(stmt).all()
        return [self.mapper.model_to_entity(row) for row in rows]

    def update(self, image_artifact: ImageArtifact) -> ImageArtifact:
        orm = self.session.get(ImageArtifactORM, str(image_artifact.id))
        if not orm:
            raise ValueError("ImageArtifact not found")

        updated = self.mapper.entity_to_model(image_artifact)

        orm.sqlmodel_update(updated)
        self.session.add(orm)

        return self.mapper.model_to_entity(orm)

    def delete(self, image_artifact_id: ImageArtifactID) -> None:
        orm = self.session.get(ImageArtifactORM, str(image_artifact_id))
        if orm:
            self.session.delete(orm)

    def flush(self) -> None:
        self.session.flush()
