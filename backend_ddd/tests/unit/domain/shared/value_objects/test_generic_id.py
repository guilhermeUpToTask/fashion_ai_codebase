import uuid
import pytest
from pydantic import BaseModel
from src.domain.shared.value_objects import GenericUUID


def test_next_id_generates_uuid():
    new_id = GenericUUID.next_id()
    assert isinstance(new_id, GenericUUID)
    # underlying int is in UUID range
    assert 0 <= int(new_id) < 2**128


def test_next_id_is_unique():
    id1 = GenericUUID.next_id()
    id2 = GenericUUID.next_id()
    assert id1 != id2


def test_pydantic_model_accepts_genericuuid():
    class Model(BaseModel):
        id: GenericUUID

    u = GenericUUID.next_id()
    m = Model(id=u)
    assert m.id == u
    assert isinstance(m.id, GenericUUID)


def test_pydantic_model_parses_uuid_string():
    class Model(BaseModel):
        id: GenericUUID

    u = str(uuid.uuid4())
    m = Model(id=u)  # type: ignore[arg-type]

    assert str(m.id) == u
    assert isinstance(m.id, uuid.UUID)


def test_equality_with_uuid():
    u = uuid.uuid4()
    g = GenericUUID(u.hex)
    # Should compare equal to normal UUID
    assert g == u
    assert u == g


def test_equality_between_genericuuids():
    g1 = GenericUUID.next_id()
    g2 = GenericUUID(str(g1))
    assert g1 == g2
    # Changing value produces inequality
    g3 = GenericUUID.next_id()
    assert g1 != g3


def test_hashing_genericuuid():
    g1 = GenericUUID.next_id()
    g2 = GenericUUID(str(g1))
    s = {g1}
    # The set recognizes g2 as same element
    assert g2 in s

    d = {g1: "value"}
    assert d[g2] == "value"
