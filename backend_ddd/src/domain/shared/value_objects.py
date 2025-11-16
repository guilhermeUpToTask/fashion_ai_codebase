from decimal import Decimal
import uuid
from dataclasses import dataclass
from typing import Any, List, Type
from pydantic import GetCoreSchemaHandler
from src.domain.shared.errors import InvalidImageDimension, InvalidImageType, InvalidURI, InvalidValue


class GenericUUID(uuid.UUID):
    
    # generates id
    @classmethod
    def next_id(cls):
        return cls(int=int(uuid.uuid4()))

    # makes this class be seen by pydantic as uuid
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ):
        return handler.generate_schema(uuid.UUID)


class ValueObject:
    """
    Base class for value objects
    """


@dataclass(frozen=True)
class Money(ValueObject):
    # atributes
    amount: Decimal
    currency: str = "USD"

    # after init
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Price cannot be negative")


@dataclass(frozen=True)
class DescriptiveString:
    value: str
    
    # Class-level constants (no type annotations!)
    MAX_LENGTH = 255
    EXCEPTION_CLASS = InvalidValue
    FIELD_NAME = "Value"  # used in error messages

    def __post_init__(self):
        normalized = self.value.strip()
        if not normalized:
            raise self.EXCEPTION_CLASS(f"{self.FIELD_NAME} cannot be empty")
        if len(normalized) > self.MAX_LENGTH:
            raise self.EXCEPTION_CLASS(
                f"{self.FIELD_NAME} Cannot exceed {self.MAX_LENGTH} characters"
            )
        object.__setattr__(self, "value", normalized)
    


#Embedding VOs
class EmbeddingId(GenericUUID):
    pass

@dataclass(frozen=True)
class EmbeddingData(ValueObject):
    vector: List[float]
    model_name: str
    
    @property
    def dimension(self) -> int:
        return len(self.vector)
    
#Image Artifact VOs

class ImageArtifactID(GenericUUID):
    pass


@dataclass(frozen=True)
class ImageDimension(ValueObject):
    value: int

    TYPE = ""
    MAX_SIZE = 2500
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

    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

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
