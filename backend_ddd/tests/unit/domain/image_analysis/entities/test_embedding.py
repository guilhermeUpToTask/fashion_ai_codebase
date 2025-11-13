import pytest
from datetime import datetime, timezone, timedelta
from src.domain.image_analysis.entities.embedding import Embedding
from src.domain.image_analysis.value_objects.embedding_vos import (
    EmbeddingId,
    EmbeddingData,
)


@pytest.fixture
def sample_embedding_data() -> EmbeddingData:
    return EmbeddingData(vector=[0.1, 0.2, 0.3, 0.4], model_name="clip-vit-base")


@pytest.fixture
def another_embedding_data() -> EmbeddingData:
    return EmbeddingData(vector=[0.9, 0.8, 0.7], model_name="clip-vit-large")


@pytest.fixture
def embedding(sample_embedding_data) -> Embedding:
    return Embedding(id=EmbeddingId.next_id(), embedding=sample_embedding_data)


# creation
def test_create_embedding_entity(embedding, sample_embedding_data):
    assert isinstance(embedding.id, EmbeddingId)
    assert embedding.embedding == sample_embedding_data
    assert isinstance(embedding.created_at, datetime)
    assert embedding.created_at.tzinfo == timezone.utc


def test_created_at_default_is_close_to_now(sample_embedding_data):
    before = datetime.now(timezone.utc)
    entity = Embedding(id=EmbeddingId.next_id(), embedding=sample_embedding_data)
    after = datetime.now(timezone.utc)

    assert before <= entity.created_at <= after


# equality
def test_entity_equality_based_on_id(sample_embedding_data):
    same_id = EmbeddingId.next_id()
    e1 = Embedding(id=same_id, embedding=sample_embedding_data)
    e2 = Embedding(id=same_id, embedding=sample_embedding_data)

    assert e1 == e2


def test_entity_inequality_based_on_id(sample_embedding_data):
    e1 = Embedding(id=EmbeddingId.next_id(), embedding=sample_embedding_data)
    e2 = Embedding(id=EmbeddingId.next_id(), embedding=sample_embedding_data)
    assert e1 != e2

def test_vector_return_same_vector(embedding, sample_embedding_data):
    assert embedding.vector() == sample_embedding_data.vector

#update
def test_embedding_data_can_be_updated_reference(embedding, another_embedding_data):
    """You can replace the embedding data reference directly if domain allows."""
    old_data = embedding.embedding
    embedding.embedding = another_embedding_data

    assert embedding.embedding != old_data
    assert embedding.embedding == another_embedding_data