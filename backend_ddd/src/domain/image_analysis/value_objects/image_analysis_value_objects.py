from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Iterator

from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.image_analysis.value_objects.clothing_item_value_objects import (
    ClothingItemId,
)
from src.domain.shared.value_objects import GenericUUID, ValueObject
from src.domain.image_analysis.errors import InvalidImageAnalysisStatusType


class ImageAnalysisID(GenericUUID):
    pass


class AnalysisStatusEnum(Enum):
    """Status of the image analysis workflow"""

    CREATED = "created"
    STARTED = "started"
    PREPROCESSING = "preprocessing"
    PREPROCESSED = "preprocessed"
    DETECTING = "detecting"
    DETECTED = "detected"
    NO_CLOTHS = "no_cloths"
    DESCRIBING = "describing"
    DESCRIBED = "described"
    EMBEDDING = "embedding"
    EMBEDDED = "embedded"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class AnalysisStatus:
    value: AnalysisStatusEnum

    def __post_init__(self):
        if not isinstance(self.value, AnalysisStatusEnum):
            raise InvalidImageAnalysisStatusType("Invalid status: {self.value}")

    @property
    def is_terminal(self) -> bool:
        return self.value in (
            AnalysisStatusEnum.COMPLETED,
            AnalysisStatusEnum.FAILED,
            AnalysisStatusEnum.CANCELLED,
        )


@dataclass(frozen=True)
class AnalysisTimestamps(ValueObject):
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def mark_started(self) -> "AnalysisTimestamps":
        return replace(self, started_at=datetime.now(timezone.utc))

    def mark_completed(self) -> "AnalysisTimestamps":
        return replace(self, completed_at=datetime.now(timezone.utc))


@dataclass(frozen=True)
class AnalysisError(ValueObject):
    message: str
    origin: str | None = None


@dataclass(frozen=True)
class ProcessingStep(ValueObject):
    status: AnalysisStatus
    timestamp: datetime
    message: str | None = None
    attempt: int = 1

    @classmethod
    def new(
        cls, status: AnalysisStatus, attempt: int, message: str | None
    ) -> "ProcessingStep":
        return cls(
            status=status,
            timestamp=datetime.now(timezone.utc),
            message=message,
            attempt=attempt,
        )


@dataclass(frozen=True)
class ProcessingHistory:
    steps: tuple[ProcessingStep, ...]

    def add_step(self, step: ProcessingStep) -> "ProcessingHistory":
        return ProcessingHistory(steps=self.steps + (step,))

    def retries_for_status(self, status: AnalysisStatus) -> int:
        return sum(1 for s in self.steps if s.status.value == status.value)

    @property
    def last_step(self) -> ProcessingStep | None:
        return self.steps[-1] if self.steps else None

    @property
    def has_failed(self) -> bool:
        return any(s.status.value == AnalysisStatusEnum.FAILED for s in self.steps)

    @property
    def is_completed(self) -> bool:
        return any(s.status.value == AnalysisStatusEnum.COMPLETED for s in self.steps)

    def __len__(self) -> int:
        return len(self.steps)


class ClothingItemsMap:
    def __init__(self):
        self._items: Dict[ClothingItemId, ClothingItem] = {}

    def add(self, item: ClothingItem) -> None:
        """Add or replace a clothing item by ID."""
        self._items[item.id] = item

    def get(self, item_id: ClothingItemId) -> ClothingItem | None:
        """Retrieve an item by its ID."""
        return self._items.get(item_id)

    def remove(self, item_id: ClothingItemId) -> None:
        """Remove an item if it exists."""
        self._items.pop(item_id, None)

    def all(self) -> list[ClothingItem]:
        """Return all items."""
        return list(self._items.values())

    def __iter__(self) -> Iterator[ClothingItem]:
        return iter(self._items.values())

    def __contains__(self, item_id: ClothingItemId) -> bool:
        return item_id in self._items

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self):
        return f"ClothingItemsMap({list(self._items.keys())})"
