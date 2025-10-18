from decimal import Decimal
import uuid
from dataclasses import dataclass
from typing import Any, Type
from pydantic import GetCoreSchemaHandler
from src.domain.shared.errors import InvalidValue


class GenericUUID(uuid.UUID):
    # generates id
    @classmethod
    def next_id(cls):
        return cls(int=uuid.uuid4().int)

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


@dataclass(frozen=True)
class TimeEvent:
    value: str
    
    