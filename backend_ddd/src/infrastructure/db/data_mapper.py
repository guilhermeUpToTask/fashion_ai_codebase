from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from src.domain.shared.entities import Entity

MapperEntity = TypeVar("MapperEntity", bound=Entity)
MapperModel = TypeVar("MapperModel", bound=Any)


class DataMapper(Generic[MapperEntity, MapperModel], ABC):
    entity_class: type[MapperEntity]
    model_class: type[MapperModel]

    @abstractmethod
    def model_to_entity(self, instance: MapperModel) -> MapperEntity:
        raise NotImplementedError()

    @abstractmethod
    def entity_to_model(self, entity: MapperEntity) -> MapperModel:
        raise NotImplementedError()
