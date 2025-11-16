from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from src.domain.shared.specifications import Specification
from src.domain.shared.value_objects import GenericUUID
from src.domain.shared.entities import Entity as DomainEntity, Embedding, EmbeddingId

Entity = TypeVar("Entity", bound=DomainEntity)
EntityId = TypeVar("EntityId", bound=GenericUUID)


class GenericRepository(Generic[EntityId, Entity], ABC):
    """An interface for a generic repository"""

    @abstractmethod
    def add(self, entity: Entity):
        raise NotImplementedError()

    @abstractmethod
    def remove(self, entity: Entity):
        raise NotImplementedError()

    @abstractmethod
    def get_by_id(self, id: EntityId) -> Entity:
        raise NotImplementedError()

    @abstractmethod
    def find_by_specification(self, spec: Specification | None) -> List[Entity]: ...

    @abstractmethod
    def update(self, entity: Entity) -> Entity:
        raise NotImplementedError()


class EmbeddingRepository(GenericRepository[EmbeddingId, Embedding]):
    pass


class ImageArtifactRepository(GenericRepository[EmbeddingId, Embedding]):
    pass
