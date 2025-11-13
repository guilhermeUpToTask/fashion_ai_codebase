import pytest
from src.domain.image_analysis.value_objects.image_artifact_vos import (
    ImageArtifactID,
    ImageWidth,
    ImageHeight,
    ImageMimeType,
    ImageMetadata,
    ImageURI,
)
from src.domain.image_analysis.errors import (
    InvalidImageDimension,
    InvalidImageType,
    InvalidURI,
)


# ID
def test_image_artifact_id_is_correct_instance():
    id = ImageArtifactID.next_id()   
    assert isinstance(id, ImageArtifactID)


# ImageWidth and ImageHeigth
@pytest.mark.parametrize("cls", [ImageWidth, ImageHeight])
def test_image_dimension_valid_range(cls):
    obj = cls(500)
    assert obj.value == 500


@pytest.mark.parametrize("cls", [ImageWidth, ImageHeight])
def test_image_dimension_too_small_raises(cls):
    with pytest.raises(InvalidImageDimension) as e:
        cls(50)
    assert "below the minimum size" in str(e.value)


@pytest.mark.parametrize("cls", [ImageWidth, ImageHeight])
def test_image_dimension_too_large_raises(cls):
    with pytest.raises(InvalidImageDimension) as e:
        cls(1600)
    assert "exceeds max size" in str(e.value)


def test_image_width_and_heigth_type_labels():
    assert ImageWidth.TYPE == "width"
    assert ImageHeight.TYPE == "heigth"


# ImageMimeType
def test_image_mime_type_accepts_valid_types():
    mime = ImageMimeType("image/jpeg")
    assert mime.value == "image/jpeg"

    mime = ImageMimeType("image/png")
    assert mime.value == "image/png"


def test_image_mime_type_rejects_invalid_type():
    with pytest.raises(InvalidImageType) as e:
        ImageMimeType("image/gif")
    assert "Unsupported image type" in str(e.value)


def test_image_mime_type_is_lowercased():
    mime = ImageMimeType("IMAGE/JPEG")
    assert mime.value == "image/jpeg"


# ImageURI
def test_valid_image_uri():
    uri = ImageURI("https://example.com/image.jpg")
    assert uri.value == "https://example.com/image.jpg"


def test_empty_image_uri():
    with pytest.raises(InvalidURI) as e:
        uri = ImageURI("")
    assert "Image URI cannot be empty" in str(e.value)


# ImageMetadata


def test_image_metadata_valid_instance():
    metadata = ImageMetadata(
        mime_type=ImageMimeType("image/png"),
        width=ImageWidth(200),
        height=ImageHeight(300),
    )
    assert metadata.mime_type.value == "image/png"
    assert metadata.width.value == 200
    assert metadata.height.value == 300