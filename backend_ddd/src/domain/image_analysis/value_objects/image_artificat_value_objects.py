from dataclasses import dataclass
from typing import Literal

from src.domain.shared.errors import InvalidValue
from src.domain.shared.value_objects import DescriptiveString, ValueObject
from src.domain.image_analysis.errors import (
    InvalidImageDimension,
    InvalidImageType,
    InvalidImageBlobSize,
)


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
        if self.value not in self.ALLOWED_TYPES:
            raise InvalidImageType(
                f"Unsupported image type: {self.value}. Allowed types: {', '.join(self.ALLOWED_TYPES)}"

            )
            
        object.__setattr__(self, "value", value_lower)


@dataclass(frozen=True)
class ImageMetadata(ValueObject):
    mime_type: ImageMimeType
    width: ImageWidth
    height: ImageHeight




@dataclass(frozen=True)
class ImageBlob(ValueObject):
    data: bytes

    MAX_SIZE_BYTES = 10 * 1024 * 1024  # e.g., 10 MB limit

    def __post_init__(self):
        if not isinstance(self.data, bytes) or not self.data:
            raise InvalidImageBlobSize("ImageBlob must contain non-empty bytes")
        if len(self.data) > self.MAX_SIZE_BYTES:
            raise InvalidImageBlobSize(f"ImageBlob exceeds maximum allowed size: {self.MAX_SIZE_BYTES}")



    




#TODO: after infrasctructure layer of storage system is consolidate, analysis way of validatig a correct imageURI
@dataclass(frozen=True)
class ImageURI(ValueObject):
    value: DescriptiveString
