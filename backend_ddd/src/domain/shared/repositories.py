import abc
from typing import Generic, List, TypeVar

from src.domain.shared.specifications import Specification
from src.domain.shared.value_objects import GenericUUID
from src.domain.shared.entities import Entity as DomainEntity

Entity = TypeVar("Entity", bound=DomainEntity)
EntityId = TypeVar("EntityId", bound=GenericUUID)


class GenericRepository(Generic[EntityId, Entity], metaclass=abc):
    """An interface for a generic repository"""

    @abc.abstractmethod
    def add(self, entity: Entity):
        raise NotImplementedError()

    @abc.abstractmethod
    def remove(self, entity: Entity):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_by_id(self, id: EntityId) -> Entity:
        raise NotImplementedError()

    @abc.abstractmethod
    def find_by_specification(self, spec: Specification | None) -> List[Entity]: ...

    @abc.abstractmethod
    def update(self, entity: Entity) -> Entity:
        raise NotImplementedError()
