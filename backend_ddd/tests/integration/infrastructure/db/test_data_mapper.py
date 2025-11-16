import pytest
from dataclasses import dataclass
from pydantic import BaseModel

from src.infrastructure.db.data_mapper import DataMapper
from src.domain.shared.entities import Entity
from src.domain.shared.value_objects import GenericUUID

@dataclass
class SampleEntity(Entity):
    id: GenericUUID
    name: str
    value: float


class SampleModel(BaseModel):
    id: str
    name: str
    value: float


class SampleMapper(DataMapper[SampleEntity, SampleModel]):
    entity_class = SampleEntity
    model_class = SampleModel

    def model_to_entity(self, instance: SampleModel) -> SampleEntity:
        return SampleEntity(
            id=GenericUUID(instance.id), name=instance.name, value=instance.value
        )

    def entity_to_model(self, entity: SampleEntity) -> SampleModel:
        return SampleModel(id=str(entity.id), name=entity.name, value=entity.value)


@pytest.fixture
def entity():
    return SampleEntity(id=GenericUUID.next_id(), name="Test", value=42.0)


@pytest.fixture
def model(entity):
    return SampleModel(id=str(entity.id), name=entity.name, value=entity.value)


@pytest.fixture
def mapper():
    return SampleMapper()



def test_model_to_entity(mapper, model):
    entity = mapper.model_to_entity(model)
    assert isinstance(entity, SampleEntity)
    assert entity.id.int == GenericUUID(model.id).int
    assert entity.name == model.name
    assert entity.value == model.value


def test_entity_to_model(mapper, entity):
    model = mapper.entity_to_model(entity)
    assert isinstance(model, SampleModel)
    assert model.id == str(entity.id)
    assert model.name == entity.name
    assert model.value == entity.value


def test_round_trip(mapper, entity):
    model = mapper.entity_to_model(entity)
    new_entity = mapper.model_to_entity(model)
    assert new_entity == entity  # compares dataclass fields
