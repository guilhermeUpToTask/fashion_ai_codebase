from src.domain.image_analysis.value_objects.embedding_vos import (
    EmbeddingId,
    EmbeddingData,
)


def test_embedding_id_is_correct_instance():
    id = EmbeddingId.next_id()
    assert isinstance(id, EmbeddingId)


def test_embedding_data_dimension_property():
    data = EmbeddingData(vector=[0.1, 0.2, 0.3, 0.4], model_name="test-model")

    assert data.dimension == 4
    assert isinstance(data.dimension, int)


def test_embedding_data_equality():
    d1 = EmbeddingData(vector=[1.0, 2.0, 3.0], model_name="model-A")
    d2 = EmbeddingData(vector=[1.0, 2.0, 3.0], model_name="model-A")
    d3 = EmbeddingData(vector=[1.0, 2.1, 3.0], model_name="model-A")

    assert d1 == d2
    assert d1 != d3


def test_embedding_data_empty_vector():
    data = EmbeddingData(vector=[], model_name="model-empty")
    assert data.dimension == 0