import pytest
from datetime import datetime, timezone
from src.domain.shared.value_objects import DescriptiveString
from src.domain.image_analysis.aggregates.image_analysis_aggregate import (
    ImageAnalysisAggregate,
)
from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.image_analysis.value_objects.clothing_item_vos import (
    ClothingItemId,
    Label,
    BoundingBox,
)
from src.domain.image_analysis.value_objects.embedding_vos import EmbeddingId
from src.domain.image_analysis.value_objects.image_artifact_vos import ImageArtifactID
from src.domain.image_analysis.value_objects.image_analysis_vos import (
    AnalysisStatus,
    ImageAnalysisID,
    StatusEnum,
)
from src.domain.image_analysis.errors import (
    InvalidTransitionException,
    MissingItemException,
    InvariantViolationException,
)
from src.domain.image_analysis.factories.image_analysis_factory import (
    ImageAnalysisFactory,
)


@pytest.fixture
def factory():
    return ImageAnalysisFactory()


@pytest.fixture
def source_image_id():
    return ImageArtifactID.next_id()


@pytest.fixture
def aggregate(factory, source_image_id):
    return factory.create(source_image_id)


@pytest.fixture
def sample_clothing_item():
    return ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=ImageAnalysisID.next_id(),
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )


@pytest.fixture
def sample_label():
    return Label(
        color=DescriptiveString("blue"),
        style=DescriptiveString("casual"),
        pattern=DescriptiveString("solid"),
        category=DescriptiveString("t-shirt"),
    )


# Aggregate Creation Tests
def test_create_new_aggregate(factory, source_image_id):
    aggregate = factory.create(source_image_id)

    assert aggregate.id is not None
    assert aggregate.source_image_id == source_image_id
    assert aggregate.status.value == StatusEnum.CREATED
    assert aggregate.preprocessed_image_id is None
    assert len(aggregate.clothing_items) == 0
    assert len(aggregate.p_history) == 0
    assert aggregate.error is None
    assert aggregate.timestamps.created_at is not None
    assert aggregate.timestamps.started_at is None
    assert aggregate.timestamps.completed_at is None


# Start Transition Tests
def test_start_from_created(aggregate):
    aggregate.start()
    assert aggregate.status.value == StatusEnum.STARTED
    assert aggregate.timestamps.started_at is not None
    assert len(aggregate.p_history) == 1
    assert aggregate.p_history.last_step.status.value == StatusEnum.STARTED

    assert aggregate.p_history.last_step.attempt == 1


def test_start_fails_with_existing_items(aggregate, sample_clothing_item):
    sample_clothing_item.image_aggregate_id = aggregate.id
    aggregate.add_clothing_item(sample_clothing_item)

    with pytest.raises(InvariantViolationException, match="Expected no clothing items"):
        aggregate.start()


def test_start_fails_with_existing_history(aggregate):
    aggregate.start()

    with pytest.raises(
        InvariantViolationException, match="should not have any processing history"
    ):
        aggregate.start()


# Preprocessing Transition Tests
def test_start_preprocessing_from_started(aggregate):
    aggregate.start()
    aggregate.start_preprocessing("Starting preprocessing")

    assert aggregate.status.value == StatusEnum.PREPROCESSING
    assert len(aggregate.p_history) == 2
    assert aggregate.p_history.last_step.message == "Starting preprocessing"


def test_start_preprocessing_from_wrong_state(aggregate):
    with pytest.raises(InvalidTransitionException):
        aggregate.start_preprocessing()


def test_finish_preprocessing(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    preprocessed_id = ImageArtifactID.next_id()

    aggregate.finish_preprocessing(preprocessed_id, "Preprocessing complete")

    assert aggregate.status.value == StatusEnum.PREPROCESSED
    assert aggregate.preprocessed_image_id == preprocessed_id
    assert aggregate.p_history.last_step.message == "Preprocessing complete"


# Detection Transition Tests
def test_start_detection_from_preprocessed(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())

    aggregate.start_detection("Starting detection")

    assert aggregate.status.value == StatusEnum.DETECTING
    assert len(aggregate.clothing_items) == 0


def test_start_detection_fails_with_existing_items(aggregate, sample_clothing_item):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())

    sample_clothing_item.image_aggregate_id = aggregate.id
    aggregate.add_clothing_item(sample_clothing_item)

    with pytest.raises(InvariantViolationException):
        aggregate.start_detection()


def test_finish_detection_with_items(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )

    aggregate.finish_detection([item], "Detection complete")

    assert aggregate.status.value == StatusEnum.DETECTED
    assert len(aggregate.clothing_items) == 1
    assert item.id in aggregate.clothing_items


def test_finish_detection_with_no_items(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    aggregate.finish_detection([], "No items found")

    assert aggregate.status.value == StatusEnum.NO_CLOTHS
    assert len(aggregate.clothing_items) == 0
    assert "No Clothing items" in aggregate.p_history.last_step.message


def test_finish_detection_fails_without_preprocessed_image(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    # Don't finish preprocessing - no preprocessed_image_id
    aggregate.status = AnalysisStatus(StatusEnum.DETECTING)

    with pytest.raises(MissingItemException, match="pre processed image is missing"):
        aggregate.finish_detection([])


# Helper fixtures for describing/embedding tests
@pytest.fixture
def detected_aggregate(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    return aggregate, item


@pytest.fixture
def described_aggregate(detected_aggregate):
    aggregate, item = detected_aggregate
    aggregate.start_describing()
    aggregate.finish_describing(
        {
            item.id: Label(
                color=DescriptiveString("blue"),
                style=DescriptiveString("casual"),
                pattern=DescriptiveString("solid"),
                category=DescriptiveString("t-shirt"),
            ),
        }
    )
    return aggregate, item


# Describing Transition Tests
def test_start_describing(detected_aggregate):
    aggregate, item = detected_aggregate

    aggregate.start_describing("Starting description")

    assert aggregate.status.value == StatusEnum.DESCRIBING


def test_start_describing_fails_without_items(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    aggregate.finish_detection([])

    # Status is NO_CLOTHS, trying to describe should fail
    with pytest.raises(InvariantViolationException):
        aggregate.status = AnalysisStatus(StatusEnum.DETECTED)
        aggregate.start_describing()


def test_finish_describing(detected_aggregate):
    aggregate, item = detected_aggregate
    aggregate.start_describing()

    labels = {
        item.id: Label(
            color=DescriptiveString("blue"),
            style=DescriptiveString("casual"),
            pattern=DescriptiveString("solid"),
            category=DescriptiveString("t-shirt"),
        ),
    }
    aggregate.finish_describing(labels, "Description complete")

    assert aggregate.status.value == StatusEnum.DESCRIBED
    assert aggregate.clothing_items[item.id].label == labels[item.id]


def test_finish_describing_fails_with_mismatched_count(detected_aggregate, sample_label):
    aggregate, item = detected_aggregate
    aggregate.start_describing()

    # Provide wrong number of labels
    labels = {
        item.id: sample_label,
        ClothingItemId.next_id(): sample_label,
    }

    with pytest.raises(
        InvariantViolationException, match="cloth labels size is different"
    ):
        aggregate.finish_describing(labels)


def test_finish_describing_fails_with_wrong_item_id(detected_aggregate, sample_label):
    aggregate, item = detected_aggregate
    aggregate.start_describing()

    wrong_id = ClothingItemId.next_id()
    labels = {wrong_id: sample_label}

    with pytest.raises(MissingItemException, match=f"Item {wrong_id} not found"):
        aggregate.finish_describing(labels)


# Embedding Transition Tests
def test_start_embedding(described_aggregate):
    aggregate, item = described_aggregate

    aggregate.start_embedding("Starting embedding")

    assert aggregate.status.value == StatusEnum.EMBEDDING


def test_finish_embedding(described_aggregate):
    aggregate, item = described_aggregate
    aggregate.start_embedding()

    embedding_id = EmbeddingId.next_id()
    embeddings = {item.id: embedding_id}

    aggregate.finish_embedding(embeddings, "Embedding complete")

    assert aggregate.status.value == StatusEnum.EMBEDDED
    assert aggregate.clothing_items[item.id].embedding_id == embedding_id


def test_finish_embedding_fails_with_mismatched_count(described_aggregate):
    aggregate, item = described_aggregate
    aggregate.start_embedding()

    embeddings = {
        item.id: EmbeddingId.next_id(),
        ClothingItemId.next_id(): EmbeddingId.next_id(),
    }

    with pytest.raises(
        InvariantViolationException, match="cloth embeddings size is different"
    ):
        aggregate.finish_embedding(embeddings)


# Completion Transition Tests
def test_complete_without_items(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    aggregate.finish_detection([])

    aggregate.complete_without_items("No items detected")

    assert aggregate.status.value == StatusEnum.COMPLETED
    assert aggregate.timestamps.completed_at is not None
    assert len(aggregate.clothing_items) == 0


def test_complete_without_items_fails_with_items(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=ImageArtifactID.next_id(),
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])

    with pytest.raises(InvariantViolationException):
        aggregate.complete_without_items()


def test_complete_with_items(aggregate , sample_label):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    aggregate.start_describing()
    aggregate.finish_describing({item.id: sample_label})
    aggregate.start_embedding()
    aggregate.finish_embedding({item.id: EmbeddingId.next_id()})

    # Attach cropped image
    aggregate.attach_cropped_artifact_to_item(item.id, ImageArtifactID.next_id())

    aggregate.complete_with_items("Processing complete")

    assert aggregate.status.value == StatusEnum.COMPLETED
    assert aggregate.timestamps.completed_at is not None


def test_complete_with_items_fails_without_items(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.status = AnalysisStatus(StatusEnum.EMBEDDED)

    with pytest.raises(InvariantViolationException):
        aggregate.complete_with_items()


def test_complete_with_items_fails_with_missing_label(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=ImageArtifactID.next_id(),
        embedding_id=EmbeddingId.next_id(),
        label=None,  # Missing label
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    aggregate.status = AnalysisStatus(StatusEnum.EMBEDDED)

    with pytest.raises(MissingItemException, match="missing critical properties"):
        aggregate.complete_with_items()


def test_complete_with_items_fails_with_missing_embedding(aggregate, sample_label):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=ImageArtifactID.next_id(),
        embedding_id=None,  # Missing embedding
        label=sample_label,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    aggregate.status = AnalysisStatus(StatusEnum.EMBEDDED)

    with pytest.raises(MissingItemException, match="missing critical properties"):
        aggregate.complete_with_items()


def test_complete_with_items_fails_with_missing_cropped_image(aggregate, sample_label):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,  # Missing cropped image
        embedding_id=EmbeddingId.next_id(),
        label=sample_label,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    aggregate.status = AnalysisStatus(StatusEnum.EMBEDDED)

    with pytest.raises(MissingItemException, match="missing critical properties"):
        aggregate.complete_with_items()


# Failure Transition Tests
def test_fail_from_any_non_terminal_state(aggregate):
    aggregate.start()

    aggregate.fail("Something went wrong", "detection_service")

    assert aggregate.status.value == StatusEnum.FAILED
    assert aggregate.error is not None
    assert aggregate.error.message == "Something went wrong"
    assert aggregate.error.origin == "detection_service"


def test_fail_from_terminal_state_raises_error(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    aggregate.finish_detection([])
    aggregate.complete_without_items()

    with pytest.raises(InvalidTransitionException, match="Cannot fail terminal state"):
        aggregate.fail("Error", None)


def test_fail_without_origin(aggregate):
    aggregate.start()

    aggregate.fail("Error without origin", None)

    assert aggregate.error.origin is None


# Cancel Transition Tests
def test_cancel_from_any_non_terminal_state(aggregate):
    aggregate.start()

    aggregate.cancel("User cancelled")

    assert aggregate.status.value == StatusEnum.CANCELLED
    assert aggregate.p_history.last_step.message == "User cancelled"


def test_cancel_from_terminal_state_raises_error(aggregate):
    aggregate.start()
    aggregate.fail("Error", None)

    with pytest.raises(
        InvalidTransitionException, match="Cannot cancel a terminal state"
    ):
        aggregate.cancel("Trying to cancel")


# Item Attachment Tests
def test_attach_cropped_artifact(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])

    artifact_id = ImageArtifactID.next_id()
    aggregate.attach_cropped_artifact_to_item(item.id, artifact_id)

    assert aggregate.clothing_items[item.id].cropped_image_id == artifact_id


def test_attach_cropped_artifact_to_missing_item(aggregate):
    wrong_id = ClothingItemId.next_id()
    artifact_id = ImageArtifactID.next_id()

    with pytest.raises(MissingItemException, match=f"Could not find ClothingItem"):
        aggregate.attach_cropped_artifact_to_item(wrong_id, artifact_id)


def test_attach_embedding_to_item(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])

    embedding_id = EmbeddingId.next_id()
    aggregate.attach_embedding_to_item(item.id, embedding_id)

    assert aggregate.clothing_items[item.id].embedding_id == embedding_id


def test_attach_embedding_to_missing_item(aggregate):
    wrong_id = ClothingItemId.next_id()
    embedding_id = EmbeddingId.next_id()

    with pytest.raises(MissingItemException, match=f"Could not find ClothingItem"):
        aggregate.attach_embedding_to_item(wrong_id, embedding_id)


# Query Helper Tests
def test_last_processing_step(aggregate):
    assert aggregate.last_processing_step() is None

    aggregate.start()

    last_step = aggregate.last_processing_step()
    assert last_step is not None
    assert last_step.status.value == StatusEnum.STARTED


def test_retries_for_status(aggregate):
    assert aggregate.retries_for(StatusEnum.STARTED) == 0

    aggregate.start()
    assert aggregate.retries_for(StatusEnum.STARTED) == 1

    # Simulate a retry
    aggregate.fail("Error", None)
    aggregate.status = AnalysisStatus(StatusEnum.CREATED)
    aggregate.start()
    assert aggregate.retries_for(StatusEnum.STARTED) == 2


def test_is_empty_result(aggregate):
    assert not aggregate.is_empty_result()

    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    aggregate.finish_detection([])

    assert aggregate.is_empty_result()


# Idempotency Tests
def test_same_transition_twice_is_idempotent(aggregate):
    aggregate.start()
    initial_history_len = len(aggregate.p_history)

    # Try to transition to the same state again
    aggregate._mark_transition_and_add_step(None, StatusEnum.STARTED)

    # Should not add another step
    assert len(aggregate.p_history) == initial_history_len


# Multiple Items Tests
def test_workflow_with_multiple_items(aggregate, sample_label):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    # Create multiple items
    items = [
        ClothingItem(
            id=ClothingItemId.next_id(),
            image_aggregate_id=aggregate.id,
            cropped_image_id=None,
            embedding_id=None,
            label=None,
            bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
        )
        for i in range(3)
    ]

    aggregate.finish_detection(items)
    assert len(aggregate.clothing_items) == 3

    # Describe all items
    aggregate.start_describing()
    labels = {item.id: sample_label for item in items}
    aggregate.finish_describing(labels)

    # Embed all items
    aggregate.start_embedding()
    embeddings = {item.id: EmbeddingId.next_id() for item in items}
    aggregate.finish_embedding(embeddings)

    # Attach cropped images
    for item in items:
        aggregate.attach_cropped_artifact_to_item(item.id, ImageArtifactID.next_id())

    # Complete
    aggregate.complete_with_items()

    assert aggregate.status.value == StatusEnum.COMPLETED
    assert len(aggregate.clothing_items) == 3

    # Verify all items have required fields
    for item in aggregate.clothing_items.values():
        assert item.label is not None
        assert item.embedding_id is not None
        assert item.cropped_image_id is not None


# Retry Logic Tests
def test_retry_after_failure(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()

    # First attempt fails
    aggregate.fail("First attempt failed", "preprocessing_service")
    assert aggregate.status.value == StatusEnum.FAILED
    assert aggregate.retries_for(StatusEnum.PREPROCESSING) == 1

    # Reset to retry
    aggregate.status = AnalysisStatus(StatusEnum.STARTED)
    aggregate.start_preprocessing("Retry preprocessing")

    # Should track as second attempt
    assert aggregate.retries_for(StatusEnum.PREPROCESSING) == 2
    assert aggregate.p_history.last_step.attempt == 2


def test_multiple_retries_different_stages(aggregate):
    aggregate.start()

    # Fail at preprocessing
    aggregate.start_preprocessing()
    aggregate.fail("Preprocessing error", None)

    # Retry preprocessing
    aggregate.status = AnalysisStatus(StatusEnum.STARTED)
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())

    # Fail at detection
    aggregate.start_detection()
    aggregate.fail("Detection error", None)

    # Retry detection
    aggregate.status = AnalysisStatus(StatusEnum.PREPROCESSED)
    aggregate.start_detection()

    assert aggregate.retries_for(StatusEnum.PREPROCESSING) == 2
    assert aggregate.retries_for(StatusEnum.DETECTING) == 2


# Edge Case Tests
def test_add_clothing_item_directly(aggregate):
    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )

    aggregate.add_clothing_item(item)

    assert item.id in aggregate.clothing_items
    assert aggregate.clothing_items[item.id] == item


def test_timestamp_consistency(aggregate):
    start_time = datetime.now(timezone.utc)

    aggregate.start()

    assert aggregate.timestamps.started_at is not None
    assert aggregate.timestamps.started_at >= start_time
    assert aggregate.timestamps.completed_at is None


def test_processing_history_accumulates(aggregate):
    aggregate.start()
    assert len(aggregate.p_history) == 1

    aggregate.start_preprocessing()
    assert len(aggregate.p_history) == 2

    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    assert len(aggregate.p_history) == 3

    aggregate.start_detection()
    assert len(aggregate.p_history) == 4


def test_no_cloths_path_complete_workflow(aggregate):
    """Test the complete workflow when no clothing items are detected"""
    aggregate.start()
    assert aggregate.status.value == StatusEnum.STARTED

    aggregate.start_preprocessing()
    assert aggregate.status.value == StatusEnum.PREPROCESSING

    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    assert aggregate.status.value == StatusEnum.PREPROCESSED
    assert aggregate.preprocessed_image_id is not None

    aggregate.start_detection()
    assert aggregate.status.value == StatusEnum.DETECTING

    aggregate.finish_detection([])
    assert aggregate.status.value == StatusEnum.NO_CLOTHS
    assert len(aggregate.clothing_items) == 0

    aggregate.complete_without_items()
    assert aggregate.status.value == StatusEnum.COMPLETED
    assert aggregate.timestamps.completed_at is not None


def test_happy_path_complete_workflow(aggregate, sample_label):
    """Test the complete happy path workflow with items"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    assert aggregate.status.value == StatusEnum.DETECTED

    aggregate.start_describing()
    aggregate.finish_describing({item.id: sample_label})
    assert aggregate.status.value == StatusEnum.DESCRIBED
    assert aggregate.clothing_items[item.id].label is not None

    aggregate.start_embedding()
    aggregate.finish_embedding({item.id: EmbeddingId.next_id()})
    assert aggregate.status.value == StatusEnum.EMBEDDED
    assert aggregate.clothing_items[item.id].embedding_id is not None

    # Attach cropped image
    aggregate.attach_cropped_artifact_to_item(item.id, ImageArtifactID.next_id())
    assert aggregate.clothing_items[item.id].cropped_image_id is not None

    aggregate.complete_with_items()
    assert aggregate.status.value == StatusEnum.COMPLETED
    assert aggregate.timestamps.completed_at is not None


def test_terminal_states_cannot_transition(aggregate):
    """Test that terminal states prevent further transitions"""
    aggregate.start()
    aggregate.cancel("Cancelled by user")

    # Try various transitions from CANCELLED
    with pytest.raises(InvalidTransitionException):
        aggregate.start_preprocessing()

    with pytest.raises(InvalidTransitionException):
        aggregate.fail("Should not work", None)


def test_preprocessing_message_propagation(aggregate):
    aggregate.start()

    custom_message = "Custom preprocessing message"
    aggregate.start_preprocessing(custom_message)

    assert aggregate.p_history.last_step.message == custom_message


def test_detection_message_with_no_items(aggregate):
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection("Starting detection")

    custom_message = "Detection completed"
    aggregate.finish_detection([], custom_message)

    # Should append "No Clothing items..." to the message
    assert "No Clothing items" in aggregate.p_history.last_step.message
    assert custom_message in aggregate.p_history.last_step.message

# Failed State Recovery Tests
def test_recover_from_failed_preprocessing(aggregate):
    """Test recovery from failed preprocessing by retrying"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.fail("Preprocessing failed", "preprocessing_service")
    
    assert aggregate.status.value == StatusEnum.FAILED
    first_failure_step = aggregate.p_history.last_step
    
    # Recover by transitioning back to STARTED
    aggregate.status = AnalysisStatus(StatusEnum.STARTED)
    aggregate.start_preprocessing("Retry after failure")
    
    assert aggregate.status.value == StatusEnum.PREPROCESSING
    assert aggregate.p_history.last_step.attempt == 2
    assert aggregate.retries_for(StatusEnum.PREPROCESSING) == 2


def test_recover_from_failed_detection(aggregate):
    """Test recovery from failed detection"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    aggregate.fail("Detection model timeout", "detection_service")
    
    assert aggregate.status.value == StatusEnum.FAILED
    assert aggregate.error is not None
    
    # Retry detection
    aggregate.status = AnalysisStatus(StatusEnum.PREPROCESSED)
    aggregate.start_detection("Retry detection")
    
    assert aggregate.status.value == StatusEnum.DETECTING
    # Error should still be there (aggregate doesn't clear it)
    assert aggregate.error is not None


def test_multiple_failures_at_same_stage(aggregate):
    """Test multiple consecutive failures at the same stage"""
    aggregate.start()
    aggregate.start_preprocessing()
    
    # First failure
    aggregate.fail("Timeout", "service")
    assert aggregate.retries_for(StatusEnum.PREPROCESSING) == 1
    
    # Retry and fail again
    aggregate.status = AnalysisStatus(StatusEnum.STARTED)
    aggregate.start_preprocessing()
    aggregate.fail("Still timing out", "service")
    assert aggregate.retries_for(StatusEnum.PREPROCESSING) == 2
    
    # Third attempt
    aggregate.status = AnalysisStatus(StatusEnum.STARTED)
    aggregate.start_preprocessing()
    aggregate.fail("Give up", "service")
    assert aggregate.retries_for(StatusEnum.PREPROCESSING) == 3
    
    # Verify all failures are in history
    failed_steps = [s for s in aggregate.p_history.steps if s.status.value == StatusEnum.FAILED]
    assert len(failed_steps) == 3


def test_fail_preserves_aggregate_state(aggregate):
    """Test that failing preserves items and other aggregate state"""
    aggregate.start()
    aggregate.start_preprocessing()
    preprocessed_id = ImageArtifactID.next_id()
    aggregate.finish_preprocessing(preprocessed_id)
    aggregate.start_detection()
    
    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    
    # Fail during describing
    aggregate.start_describing()
    aggregate.fail("Description service down", "description_service")
    
    # Verify state is preserved
    assert aggregate.preprocessed_image_id == preprocessed_id
    assert len(aggregate.clothing_items) == 1
    assert item.id in aggregate.clothing_items
    assert aggregate.status.value == StatusEnum.FAILED


# Duplicate and Concurrent Operation Tests
def test_add_duplicate_item_id_overwrites(aggregate):
    """Test that adding item with duplicate ID overwrites the previous one"""
    item1 = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    
    item2 = ClothingItem(
        id=item1.id,  # Same ID
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=20, x_max=100, y_min=10, y_max=100),  # Different bbox
    )
    
    aggregate.add_clothing_item(item1)
    aggregate.add_clothing_item(item2)
    
    assert len(aggregate.clothing_items) == 1
    assert aggregate.clothing_items[item1.id].bbox.x_min == 20  # Should be item2's bbox


def test_attach_cropped_artifact_twice_raises_error(aggregate):
    """Test that attaching cropped artifact twice raises error from entity"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    
    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    
    # Attach first time
    aggregate.attach_cropped_artifact_to_item(item.id, ImageArtifactID.next_id())
    
    # Try to attach again - should raise from entity
    with pytest.raises(InvariantViolationException, match="already has an cropped image artifact"):
        aggregate.attach_cropped_artifact_to_item(item.id, ImageArtifactID.next_id())


def test_attach_embedding_twice_raises_error(aggregate):
    """Test that attaching embedding twice raises error from entity"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    
    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    
    # Attach first time
    aggregate.attach_embedding_to_item(item.id, EmbeddingId.next_id())
    
    # Try to attach again - should raise from entity
    with pytest.raises(InvariantViolationException, match="already has an embedding"):
        aggregate.attach_embedding_to_item(item.id, EmbeddingId.next_id())


def test_finish_describing_with_already_labeled_items(detected_aggregate, sample_label):
    """Test describing items that already have labels"""
    aggregate, item = detected_aggregate
    
    # Manually attach label
    item.attach_label(sample_label)
    
    aggregate.start_describing()
    
    # Try to describe with different labels
    labels = {item.id: sample_label}
    
    # Should raise from entity when trying to attach second label
    with pytest.raises(InvariantViolationException, match="Label already attached"):
        aggregate.finish_describing(labels)


# Invalid State Combination Tests
def test_detect_without_preprocessed_image_manual_state(aggregate):
    """Test detection phase requires preprocessed image even if status is set manually"""
    aggregate.start()
    aggregate.start_preprocessing()
    # Don't finish preprocessing, just manually set status
    aggregate.status = AnalysisStatus(StatusEnum.DETECTING)
    
    with pytest.raises(MissingItemException, match="pre processed image is missing"):
        aggregate.finish_detection([])


def test_complete_with_items_in_wrong_state(aggregate, sample_label):
    """Test that completing with items validates previous state"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    
    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        cropped_image_id=ImageArtifactID.next_id(),
        embedding_id=EmbeddingId.next_id(),
        label=sample_label,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    aggregate.finish_detection([item])
    
    # Manually set wrong state
    aggregate.status = AnalysisStatus(StatusEnum.DESCRIBED)  # Skipped embedding
    
    # Should fail validation due to expected status
    with pytest.raises(InvalidTransitionException):
        aggregate.complete_with_items()


# Processing History Validation Tests
def test_processing_history_tracks_all_attempts(aggregate):
    """Test that processing history accurately tracks all attempts including failures"""
    aggregate.start()
    
    # Multiple preprocessing attempts
    aggregate.start_preprocessing("Attempt 1")
    aggregate.fail("Failed", None)
    
    aggregate.status = AnalysisStatus(StatusEnum.STARTED)
    aggregate.start_preprocessing("Attempt 2")
    aggregate.fail("Failed again", None)
    
    aggregate.status = AnalysisStatus(StatusEnum.STARTED)
    aggregate.start_preprocessing("Attempt 3")
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    
    # Check history
    preprocessing_steps = [
        s for s in aggregate.p_history.steps 
        if s.status.value == StatusEnum.PREPROCESSING
    ]
    
    assert len(preprocessing_steps) == 3
    assert preprocessing_steps[0].attempt == 1
    assert preprocessing_steps[1].attempt == 2
    assert preprocessing_steps[2].attempt == 3


def test_previous_non_failed_status(aggregate):
    """Test retrieval of previous non-failed status from history"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.fail("Error", None)
    
    # Should return PREPROCESSING as previous non-failed status
    assert aggregate.p_history.previuos_non_failed_status == StatusEnum.PREPROCESSING


def test_previous_non_failed_status_with_multiple_failures(aggregate):
    """Test previous non-failed status with multiple consecutive failures"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    aggregate.fail("First fail", None)
    aggregate.start_detection()
    aggregate.fail("Second fail", None)
    
    # Should skip both FAILED states and return DETECTING
    assert aggregate.p_history.previuos_non_failed_status == StatusEnum.DETECTING

def test_cannot_fail_from_failed_state(aggregate):
    """Test that you cannot call fail() when already in FAILED state"""
    aggregate.start()
    aggregate.fail("First failure", "service_a")
    
    # Attempting to fail again should raise
    with pytest.raises(InvalidTransitionException, match="Cannot fail terminal state"):
        aggregate.fail("Second failure", "service_b")


# Timestamp Validation Tests
def test_started_timestamp_set_correctly(aggregate):
    """Test that started_at timestamp is set when starting"""
    before = datetime.now(timezone.utc)
    aggregate.start()
    after = datetime.now(timezone.utc)
    
    assert aggregate.timestamps.started_at is not None
    assert before <= aggregate.timestamps.started_at <= after


def test_completed_timestamp_set_correctly(aggregate):
    """Test that completed_at timestamp is set when completing"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    aggregate.finish_detection([])
    
    before = datetime.now(timezone.utc)
    aggregate.complete_without_items()
    after = datetime.now(timezone.utc)
    
    assert aggregate.timestamps.completed_at is not None
    assert before <= aggregate.timestamps.completed_at <= after


def test_timestamps_are_ordered(aggregate):
    """Test that timestamps follow chronological order"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    aggregate.finish_detection([])
    aggregate.complete_without_items()
    
    assert aggregate.timestamps.created_at <= aggregate.timestamps.started_at
    assert aggregate.timestamps.started_at <= aggregate.timestamps.completed_at


# Empty and Null Value Tests
def test_finish_detection_with_empty_list_explicit(aggregate):
    """Explicitly test finishing detection with empty list"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    
    empty_list = []
    aggregate.finish_detection(empty_list)
    
    assert aggregate.status.value == StatusEnum.NO_CLOTHS
    assert len(aggregate.clothing_items) == 0


def test_fail_with_none_origin(aggregate):
    """Test that failing with None origin is acceptable"""
    aggregate.start()
    
    aggregate.fail("Error message", None)
    
    assert aggregate.error is not None
    assert aggregate.error.message == "Error message"
    assert aggregate.error.origin is None


def test_cancel_with_none_message(aggregate):
    """Test cancelling with None message"""
    aggregate.start()
    
    aggregate.cancel(None)
    
    assert aggregate.status.value == StatusEnum.CANCELLED
    assert aggregate.p_history.last_step.message is None


# Complete Edge Cases
def test_cannot_start_from_non_created_state(aggregate):
    """Test that start only works from CREATED state"""
    aggregate.start()
    
    # Try to start again
    with pytest.raises(InvariantViolationException):
        aggregate.start()


def test_finish_preprocessing_from_wrong_state_raises_error(aggregate):
    """Test that finish_preprocessing validates current state"""
    aggregate.start()
    # Skip start_preprocessing
    
    with pytest.raises(InvalidTransitionException):
        aggregate.finish_preprocessing(ImageArtifactID.next_id())


def test_complete_without_items_from_wrong_state_raises_error(aggregate):
    """Test that complete_without_items requires NO_CLOTHS state"""
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    # Don't finish detection
    
    with pytest.raises(InvalidTransitionException):
        aggregate.complete_without_items()


def test_items_belong_to_correct_aggregate(aggregate):
    """Test that items must belong to the correct aggregate"""
    other_aggregate_id = ImageAnalysisID.next_id()
    
    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=other_aggregate_id,  # Wrong aggregate
        cropped_image_id=None,
        embedding_id=None,
        label=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )
    
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(ImageArtifactID.next_id())
    aggregate.start_detection()
    
    # Finish detection adds the item without validation in the method
    # The validation would come from the factory reconstitute method
    aggregate.finish_detection([item])
    
    # Item is added despite wrong aggregate_id (aggregate doesn't validate this)
    assert len(aggregate.clothing_items) == 1