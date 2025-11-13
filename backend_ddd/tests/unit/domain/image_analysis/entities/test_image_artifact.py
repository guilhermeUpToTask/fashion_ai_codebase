import pytest
from src.domain.image_analysis.entities.image_artifact import ImageArtifact
from src.domain.image_analysis.value_objects.image_artifact_vos import (
    ImageArtifactID,
    ImageMetadata,
    ImageMimeType,
    ImageWidth,
    ImageHeight,
    ImageURI,
)


@pytest.fixture
def sample_metadata() -> ImageMetadata:
    return ImageMetadata(
        mime_type=ImageMimeType("image/png"),
        width=ImageWidth(500),
        height=ImageHeight(500),
    )


@pytest.fixture
def another_metadata() -> ImageMetadata:
    return ImageMetadata(
        mime_type=ImageMimeType("image/jpeg"),
        width=ImageWidth(600),
        height=ImageHeight(450),
    )


@pytest.fixture
def image_artifact(sample_metadata) -> ImageArtifact:
    return ImageArtifact(
        id=ImageArtifactID.next_id(),
        metadata=sample_metadata,
        blob_ref=ImageURI("https://storage.example.com/blob/test.png"),
    )

#create and update
def test_create_image_artifact(image_artifact, sample_metadata):
    assert isinstance(image_artifact.id, ImageArtifactID)
    assert image_artifact.metadata == sample_metadata
    assert image_artifact.blob_ref.value == "https://storage.example.com/blob/test.png"

def test_update_metadata(image_artifact, another_metadata):
    old_metadata = image_artifact.metadata
    image_artifact.update_metadata(another_metadata)
    
    assert image_artifact.metadata == another_metadata
    assert image_artifact.metadata != old_metadata

#Equality 
def test_entity_equality_based_on_id(sample_metadata):
    same_id = ImageArtifactID.next_id()
    entity1 = ImageArtifact(
        id=same_id,
        metadata=sample_metadata,
        blob_ref=ImageURI("https://blob1.png")
    )
    entity2 = ImageArtifact(
        id=same_id,
        metadata=sample_metadata,
        blob_ref=ImageURI("https://blob2.png")
    )
    
    assert entity1 == entity2

def test_entity_inequality_based_on_id(sample_metadata):
    """Entities with different IDs should not be equal."""
    entity1 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        metadata=sample_metadata,
        blob_ref=ImageURI("https://blob1.png"),
    )
    entity2 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        metadata=sample_metadata,
        blob_ref=ImageURI("https://blob2.png"),
    )

    assert entity1 != entity2