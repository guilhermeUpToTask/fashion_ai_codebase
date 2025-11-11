from dataclasses import dataclass

from src.domain.shared.value_objects import DescriptiveString, ValueObject, GenericUUID
from src.domain.image_analysis.errors import (
    InvalidImageDimension,
    InvalidImageType,
    InvalidURI
)


class ImageArtifactID(GenericUUID):
    pass


@dataclass(frozen=True)
class ImageDimension(ValueObject):
    value: int

    TYPE = ""
    MAX_SIZE = 1500
    MIN_SIZE = 100

    def __post_init__(self):
        if self.value > self.MAX_SIZE:
            raise InvalidImageDimension(
                f"Image {self.TYPE} {self.value} exceeds max size of: {self.MAX_SIZE}"
            )
        if self.value < self.MIN_SIZE:
            raise InvalidImageDimension(
                f"Image {self.TYPE}  {self.value} is below the minimum size of {self.MIN_SIZE}"
            )


@dataclass(frozen=True)
class ImageWidth(ImageDimension):
    TYPE = "width"


@dataclass(frozen=True)
class ImageHeight(ImageDimension):
    TYPE = "heigth"


@dataclass(frozen=True)
class ImageMimeType(DescriptiveString):
    """
    Currently supported image
    """

    ALLOWED_TYPES = {"image/jpeg", "image/png"}

    def __post_init__(self):
        super().__post_init__()

        value_lower = self.value.lower()
        if value_lower not in self.ALLOWED_TYPES:
            raise InvalidImageType(
                f"Unsupported image type: {self.value}. Allowed types: {', '.join(self.ALLOWED_TYPES)}"
            )

        object.__setattr__(self, "value", value_lower)


# TODO: after infrasctructure layer of storage system is consolidate, analysis way of validatig a correct imageURI

@dataclass(frozen=True)
class ImageURI(DescriptiveString):
    MAX_LENGTH = 1024
    EXCEPTION_CLASS = InvalidURI
    FIELD_NAME = "Image URI"



@dataclass(frozen=True)
class ImageMetadata(ValueObject):
    mime_type: ImageMimeType
    width: ImageWidth
    height: ImageHeight
    uri: ImageURI
