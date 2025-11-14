from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum

from src.domain.shared.value_objects import GenericUUID, ValueObject
from src.domain.image_analysis.errors import InvalidImageAnalysisStatusType


class ImageAnalysisID(GenericUUID):
    pass


class StatusEnum(Enum):
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


# TODO: avaliate the need of having a class analysis status or just have the status enum
@dataclass(frozen=True)
class AnalysisStatus:
    value: StatusEnum

    def __post_init__(self):
        if not isinstance(self.value, StatusEnum):
            raise InvalidImageAnalysisStatusType("Invalid status: {self.value}")

    @property
    def is_terminal(self) -> bool:
        return self.value in (
            StatusEnum.COMPLETED,
            StatusEnum.FAILED,
            StatusEnum.CANCELLED,
        )


@dataclass(frozen=True)
class AnalysisTimestamps(ValueObject):
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def mark_started(self, timestamp: datetime) -> "AnalysisTimestamps":
        return replace(self, started_at=timestamp)

    def mark_completed(self, timestamp: datetime) -> "AnalysisTimestamps":
        return replace(self, completed_at=timestamp)


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
class ProcessingHistory(ValueObject):
    steps: tuple[ProcessingStep, ...]

    def add_step(self, step: ProcessingStep) -> "ProcessingHistory":
        return ProcessingHistory(steps=self.steps + (step,))

    def retries_for_status(self, status: AnalysisStatus) -> int:
        return sum(1 for s in self.steps if s.status.value == status.value)

    @property
    def last_step(self) -> ProcessingStep | None:
        return self.steps[-1] if self.steps else None

    @property
    def previuos_non_failed_status(self) -> StatusEnum | None:
        for step in reversed(self.steps[:-1]):
            if step.status.value != StatusEnum.FAILED:
                return step.status.value
        return None

    @property
    def has_failed(self) -> bool:
        return any(s.status.value == StatusEnum.FAILED for s in self.steps)

    @property
    def is_completed(self) -> bool:
        return any(s.status.value == StatusEnum.COMPLETED for s in self.steps)

    def __len__(self) -> int:
        return len(self.steps)
