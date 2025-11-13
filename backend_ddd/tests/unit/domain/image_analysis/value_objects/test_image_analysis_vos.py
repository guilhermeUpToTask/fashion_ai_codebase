import pytest
from datetime import datetime, timezone, timedelta

from src.domain.image_analysis.value_objects.image_analysis_vos import (
    ImageAnalysisID,
    AnalysisStatus,
    AnalysisTimestamps,
    AnalysisError,
    ProcessingStep,
    ProcessingHistory,
    StatusEnum,
)
from src.domain.image_analysis.errors import InvalidImageAnalysisStatusType


# ImageAnalysisID
def test_image_analysis_id_is_correct_instance():
    id = ImageAnalysisID.next_id()
    assert isinstance(id, ImageAnalysisID)


# AnalysisStatus
def test_analysis_status_valid_and_terminal_flags():
    created = AnalysisStatus(StatusEnum.CREATED)
    completed = AnalysisStatus(StatusEnum.COMPLETED)
    failed = AnalysisStatus(StatusEnum.FAILED)
    cancelled = AnalysisStatus(StatusEnum.CANCELLED)

    assert not created.is_terminal
    assert completed.is_terminal
    assert failed.is_terminal
    assert cancelled.is_terminal


def test_analysis_status_invalid_type_raises():
    with pytest.raises(InvalidImageAnalysisStatusType):
        AnalysisStatus("invalid")  # type: ignore[arg-type]


# AnalysisTimestamps
def test_analysis_timestamps_creation_and_transitions():
    created = datetime(2025, 1, 1, tzinfo=timezone.utc)
    timestamps = AnalysisTimestamps(created_at=created)
    assert timestamps.started_at is None
    assert timestamps.completed_at is None

    start_time = created + timedelta(seconds=5)
    completed_time = start_time + timedelta(seconds=10)

    started = timestamps.mark_started(start_time)
    completed = started.mark_completed(completed_time)

    assert started is not timestamps
    assert completed is not started

    assert started.started_at == start_time
    assert completed.completed_at == completed_time


# AnalysisError
def test_analysis_error_message_and_origin():
    err = AnalysisError(message="processing failed")
    assert err.message == "processing failed"
    assert err.origin is None

    err2 = AnalysisError(message="db timeout", origin="database")
    assert err2.origin == "database"


# ProcessingStep
def test_processing_step_new_sets_expected_fields():
    status = AnalysisStatus(StatusEnum.STARTED)
    step = ProcessingStep.new(status=status, attempt=2, message="retrying")

    assert step.status == status
    assert step.attempt == 2
    assert step.message == "retrying"
    assert isinstance(step.timestamp, datetime)
    assert step.timestamp.tzinfo == timezone.utc


def make_step(status_enum: StatusEnum, attempt: int = 1, message: str | None = None):
    return ProcessingStep(
        status=AnalysisStatus(status_enum),
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        message=message,
        attempt=attempt,
    )

#ProcessingHistory
def test_processing_history_add_and_retries_and_flags():
    failed1 = make_step(StatusEnum.FAILED, attempt=1)
    failed2 = make_step(StatusEnum.FAILED, attempt=2)
    completed = make_step(StatusEnum.COMPLETED)
    
    history = ProcessingHistory(steps=())
    assert len(history) == 0
    assert history.last_step is None
    assert not history.has_failed
    assert not history.is_completed
    
    history1 = history.add_step(failed1)
    assert len(history1) == 1
    assert history1.has_failed
    assert history1.retries_for_status(failed1.status) == 1
    
    history2 = history1.add_step(failed2)
    assert len(history2) == 2
    assert history2.retries_for_status(failed1.status) == 2
    assert history2.last_step == failed2
    
    history3 = history2.add_step(completed)
    assert len(history3) == 3
    assert history3.is_completed
    assert history3.has_failed

def test_processing_history_len_and_iteration_behavior():
    s1 = make_step(StatusEnum.CREATED)
    s2 = make_step(StatusEnum.STARTED)
    history = ProcessingHistory(steps=(s1, s2))
    
    assert len(history) == 2
    assert history.steps == (s1, s2)
    assert history.last_step == s2