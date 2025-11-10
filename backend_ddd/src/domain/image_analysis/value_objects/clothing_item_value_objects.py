from dataclasses import dataclass
from src.domain.image_analysis.errors import InvalidBoundingBox
from src.domain.shared.value_objects import GenericUUID, ValueObject, DescriptiveString


class ClothingItemId(GenericUUID):
    pass


@dataclass(frozen=True)
class Label:
    category: DescriptiveString
    color: DescriptiveString
    pattern: DescriptiveString
    style: DescriptiveString

    def __str__(self) -> str:
        return f"{self.style.value} {self.color.value} {self.pattern.value} {self.category.value}"


@dataclass(frozen=True)
class BoundingBox(ValueObject):
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    def __post_init__(self):
        if not all(v >= 0 for v in (self.x_min, self.x_max, self.y_min, self.y_max)):
            raise InvalidBoundingBox(
                f"BoundingBox coordinates must be non-negative integers: {self}"
            )
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise InvalidBoundingBox(
                f"BoundingBox max values must be greater than min values: {self}"
            )

    @property
    def width(self) -> int:
        return self.x_max - self.x_min

    @property
    def height(self) -> int:
        return self.y_max - self.y_min

    @property
    def area(self) -> int:
        return self.width * self.height

    def as_tuple(self) -> tuple[int, int, int, int]:
        return self.x_min, self.y_min, self.x_max, self.y_max

    def as_dict(self) -> dict[str, int]:
        return {
            "x_min": self.x_min,
            "y_min": self.y_min,
            "x_max": self.x_max,
            "y_max": self.y_max,
        }