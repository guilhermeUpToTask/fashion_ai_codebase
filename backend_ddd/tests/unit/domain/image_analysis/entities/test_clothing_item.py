import pytest
from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.image_analysis.errors import InvalidLabel, InvariantViolationException
from src.domain.image_analysis.value_objects.clothing_item_vos import (
    ClothingItemId,
    Label,
    BoundingBox,
)
from src.domain.image_analysis.value_objects.image_analysis_vos import ImageAnalysisID
from src.domain.image_analysis.value_objects.image_artifact_vos import ImageArtifactID
from src.domain.image_analysis.entities.embedding import EmbeddingId
from src.domain.shared.value_objects import DescriptiveString


@pytest.fixture
def valid_label() -> Label:
    return Label(
        category=DescriptiveString("shirt"),
        color=DescriptiveString("blue"),
        pattern=DescriptiveString("stripped"),
        style=DescriptiveString("casual"),
    )


@pytest.fixture
def valid_bbox() -> BoundingBox:
    return BoundingBox(x_min=10, x_max=100, y_min=20, y_max=200)


@pytest.fixture
def clothing_item(valid_bbox) -> ClothingItem:
    return ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=ImageAnalysisID.next_id(),
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=valid_bbox,
    )


# creation
def test_create_clothing_item(clothing_item, valid_bbox):
    assert isinstance(clothing_item.id, ClothingItemId)
    assert isinstance(clothing_item.image_aggregate_id, ImageAnalysisID)
    assert clothing_item.label is None
    assert clothing_item.embedding_id is None
    assert clothing_item.cropped_image_id is None
    assert clothing_item.bbox == valid_bbox


# atachs and invariants
def test_attach_label_sucessfully(clothing_item, valid_label):
    clothing_item.attach_label(valid_label)
    assert clothing_item.label == valid_label


def test_attach_label_twice_raises(clothing_item, valid_label):
    clothing_item.attach_label(valid_label)
    with pytest.raises(InvariantViolationException):
        clothing_item.attach_label(valid_label)


def test_attach_cropped_image_sets_reference(clothing_item):
    artifact_id = ImageArtifactID.next_id()
    clothing_item.attach_cropped_image(artifact_id)
    assert clothing_item.cropped_image_id == artifact_id


def test_attach_cropped_image_twice_raises(clothing_item):
    artifact_id = ImageArtifactID.next_id()
    clothing_item.attach_cropped_image(artifact_id)
    with pytest.raises(InvariantViolationException):
        clothing_item.attach_cropped_image(artifact_id)


def test_attach_embedding_sets_reference(clothing_item):
    embbeding_id = EmbeddingId.next_id()
    clothing_item.attach_embedding(embbeding_id)
    assert clothing_item.embedding_id == embbeding_id


def test_attach_embedding_twice_raises(clothing_item):
    embbedding_id = EmbeddingId.next_id()
    clothing_item.attach_embedding(embbedding_id)
    with pytest.raises(InvariantViolationException):
        clothing_item.attach_embedding(embbedding_id)


# equality
def test_entity_equality_based_on_id(valid_bbox):
    """Entities with same ID should be equal."""
    same_id = ClothingItemId.next_id()
    item1 = ClothingItem(
        id=same_id,
        image_aggregate_id=ImageAnalysisID.next_id(),
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=valid_bbox,
    )
    item2 = ClothingItem(
        id=same_id,
        image_aggregate_id=ImageAnalysisID.next_id(),
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=valid_bbox,
    )
    assert item1 == item2


def test_entity_inequality_based_on_id(valid_bbox):
    """Entities with different IDs should not be equal."""
    item1 = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=ImageAnalysisID.next_id(),
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=valid_bbox,
    )
    item2 = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=ImageAnalysisID.next_id(),
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=valid_bbox,
    )
    assert item1 != item2
