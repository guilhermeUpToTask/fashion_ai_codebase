from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.domain.shared.value_objects import ValueObject
from src.domain.image_analysis.errors import InvalidImageAnalysisStatusType


class AnalysisStatusEnum(Enum):
    """Status of the image analysis workflow"""

    CREATED = "created"
    STARTED = "started"
    PREPROCESSING = "preprocessing"
    PREPROCESSED = "preprocessed"
    DETECTING = "detecting"
    DETECTED = "detected"
    DESCRIBING = "describing"
    DESCRIBED = "described"
    EMBEDDING = "embedding"
    EMBEDDED = "embedded"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class AnalysisStatus:
    value: AnalysisStatusEnum

    def __post__init__(self):
        if not isinstance(self.value, AnalysisStatusEnum):
            raise InvalidImageAnalysisStatusType("Invalid status: {self.value}")

@dataclass(frozen=True)
class AnalysisTimestamps(ValueObject):
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True)
class AnalysisError(ValueObject):
    message: str


@dataclass
class ProcessingStep(ValueObject):
    status: AnalysisStatus
    timestamp: datetime
    message: str | None = None
    attempt: int = 1


@dataclass
class ProcessingHistory:
    steps: tuple[ProcessingStep, ...]

    def add_step(self, step: ProcessingStep) -> "ProcessingHistory":
        return self
    
    @property
    def last_step(self) -> ProcessingStep | None:
        ...
    
    def retries_for_status(self, status: AnalysisStatus) -> int:
        return 0
    

    
    


