from dataclasses import dataclass
from typing import List
from src.domain.image_analysis.errors import InvalidBoundingBox
from src.domain.shared.value_objects import ValueObject, DescriptiveString


@dataclass(frozen=True)
class Label:
    category: DescriptiveString
    color: DescriptiveString
    pattern: DescriptiveString
    style: DescriptiveString


@dataclass(frozen=True)
class BoundingBox(ValueObject):
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    def __post__init(self):
        if not all(v >= 0 for v in (self.x_min, self.x_max, self.y_min, self.y_max)):
            raise InvalidBoundingBox(
                f"BoundingBox coordinates must be non-negative integers: {self}"
            )
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise InvalidBoundingBox(
                f"BoundingBox max values mulst be greater than min values: {self}"
            )
