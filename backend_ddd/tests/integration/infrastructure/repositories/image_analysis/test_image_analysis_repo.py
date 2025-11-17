"""
Tests for SQLModelImageAnalysisRepository.

Tests cover:
- Adding aggregates with various configurations
- Retrieving by ID
- Listing all aggregates
- Finding by specification
- Updating aggregates (status, adding/removing items, appending steps)
- Deleting aggregates
- Edge cases and error conditions
"""

from datetime import datetime, timezone, timedelta
from typing import List
import pytest
from sqlmodel import select

from src.domain.image_analysis.aggregates.image_analysis_aggregate import (
    ImageAnalysisAggregate,
)
from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.image_analysis.value_objects.image_analysis_vos import (
    ImageAnalysisID,
    ProcessingStep,
    StatusEnum,
)
from src.domain.image_analysis.value_objects.clothing_item_vos import (
    BoundingBox,
    ClothingItemId,
    Label,
)
from src.domain.shared.value_objects import (
    DescriptiveString,
    ImageArtifactID,
    EmbeddingId,
)
from src.domain.shared.specifications import (
    FieldSpecification,
    AndSpecification,
    OrSpecification,
)
from src.infrastructure.repositories.image_analysis.orms import (
    ImageAnalysisORM,
    ClothingItemORM,
    ProcessingStepORM,
)
from src.domain.image_analysis.factories.image_analysis_factory import (
    ImageAnalysisFactory,
)


# ==================== Fixtures ====================


@pytest.fixture
def factory() -> ImageAnalysisFactory:
    """Factory for creating aggregates."""
    return ImageAnalysisFactory()


@pytest.fixture
def sample_aggregate(factory) -> ImageAnalysisAggregate:
    """Create a basic aggregate in CREATED status."""
    source_image_id = ImageArtifactID.next_id()
    return factory.create(source_image_id)


@pytest.fixture
def aggregate_with_items(factory) -> ImageAnalysisAggregate:
    """Create an aggregate with clothing items."""
    source_image_id = ImageArtifactID.next_id()
    aggregate = factory.create(source_image_id)

    # Add a clothing item
    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=aggregate.id,
        bbox=BoundingBox(x_min=10, y_min=20, x_max=100, y_max=200),
        label=Label(
            category=DescriptiveString("shirt"),
            pattern=DescriptiveString("striped"),
            style=DescriptiveString("casual"),
            color=DescriptiveString("blue"),
        ),
        cropped_image_id=None,
        embedding_id=None,
    )
    aggregate.add_clothing_item(item)

    return aggregate


@pytest.fixture
def preprocessing_aggregate(factory) -> ImageAnalysisAggregate:
    """Create an aggregate in PREPROCESSING status."""
    source_image_id = ImageArtifactID.next_id()
    aggregate = factory.create(source_image_id)
    aggregate.start()
    aggregate.start_preprocessing()
    return aggregate


@pytest.fixture
def completed_aggregate(factory) -> ImageAnalysisAggregate:
    """Create a completed aggregate with multiple items and steps."""
    source_image_id = ImageArtifactID.next_id()
    preprocessed_id = ImageArtifactID.next_id()

    aggregate = factory.create(source_image_id)

    # Simulate processing
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.finish_preprocessing(preprocessed_id)

    aggregate.start_detection()
    # Add multiple clothing items
    items: List[ClothingItem] = []
    for i in range(3):
        item = ClothingItem(
            id=ClothingItemId.next_id(),
            image_aggregate_id=aggregate.id,
            bbox=BoundingBox(
                x_min=i * 10, y_min=i * 20, x_max=i * 10 + 100, y_max=i * 20 + 200
            ),
            label=Label(
                category=DescriptiveString(f"item_category_{i}"),
                pattern=DescriptiveString(f"item_pattern_{i}"),
                style=DescriptiveString(f"item_style_{i}"),
                color=DescriptiveString(f"item_{i}"),
            ),
            cropped_image_id=None,
            embedding_id=None,
        )
        items.append(item)

    aggregate.finish_detection(detected_items=items)

    return aggregate


@pytest.fixture
def failed_aggregate(factory) -> ImageAnalysisAggregate:
    """Create a failed aggregate."""
    source_image_id = ImageArtifactID.next_id()
    aggregate = factory.create(source_image_id)
    aggregate.start()
    aggregate.start_preprocessing()
    aggregate.fail("Processing error", "detection_service")
    return aggregate


# ==================== ADD Tests ====================


def test_add_basic_aggregate(sqlmodel_image_analysis_repo, session, sample_aggregate):
    """Test adding a basic aggregate in CREATED status."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    session.commit()

    # Verify in database
    orm = session.get(ImageAnalysisORM, str(sample_aggregate.id))
    assert orm is not None
    assert orm.status == StatusEnum.CREATED.value
    assert orm.source_image_id == str(sample_aggregate.source_image_id)
    assert orm.created_at is not None
    assert orm.started_at is None
    assert orm.completed_at is None
    assert orm.error_message is None
    assert orm.error_origin is None


def test_add_aggregate_with_clothing_items(
    sqlmodel_image_analysis_repo, session, aggregate_with_items
):
    """Test adding an aggregate with clothing items."""
    sqlmodel_image_analysis_repo.add(aggregate_with_items)
    session.commit()

    # Verify aggregate
    orm = session.get(ImageAnalysisORM, str(aggregate_with_items.id))
    assert orm is not None

    # Verify clothing items
    items = session.exec(
        select(ClothingItemORM).where(
            ClothingItemORM.image_aggregate_id == str(aggregate_with_items.id)
        )
    ).all()

    assert len(items) == 1
    item = items[0]
    assert item.bbox_x_min == 10
    assert item.bbox_y_min == 20
    assert item.bbox_x_max == 100
    assert item.bbox_y_max == 200
    assert item.label_category == "shirt"
    assert item.label_pattern == "striped"
    assert item.label_style == "casual"
    assert item.label_color == "blue"


def test_add_preprocessing_aggregate(
    sqlmodel_image_analysis_repo, session, preprocessing_aggregate
):
    """Test adding an aggregate in PROCESSING status."""
    sqlmodel_image_analysis_repo.add(preprocessing_aggregate)
    session.commit()

    orm = session.get(ImageAnalysisORM, str(preprocessing_aggregate.id))
    assert orm is not None
    assert orm.status == StatusEnum.PREPROCESSING.value
    assert orm.started_at is not None
    assert orm.completed_at is None

    # Verify processing steps
    steps = session.exec(
        select(ProcessingStepORM).where(
            ProcessingStepORM.image_aggregate_id == str(preprocessing_aggregate.id)
        )
    ).all()

    # Should have STARTED and PROCESSING steps
    assert len(steps) >= 2
    statuses = [step.status for step in steps]
    assert StatusEnum.STARTED.value in statuses
    assert StatusEnum.PREPROCESSING.value in statuses


def test_add_completed_aggregate(
    sqlmodel_image_analysis_repo, session, completed_aggregate
):
    """Test adding a completed detection aggregate with multiple items."""
    sqlmodel_image_analysis_repo.add(completed_aggregate)
    session.commit()

    orm = session.get(ImageAnalysisORM, str(completed_aggregate.id))
    assert orm is not None
    assert orm.status == StatusEnum.DETECTED.value
    assert orm.started_at is not None
    assert orm.preprocessed_image_id is not None

    # Verify clothing items
    items = session.exec(
        select(ClothingItemORM).where(
            ClothingItemORM.image_aggregate_id == str(completed_aggregate.id)
        )
    ).all()
    assert len(items) == 3


def test_add_failed_aggregate(sqlmodel_image_analysis_repo, session, failed_aggregate):
    """Test adding a failed aggregate with error details."""
    sqlmodel_image_analysis_repo.add(failed_aggregate)
    session.commit()

    orm = session.get(ImageAnalysisORM, str(failed_aggregate.id))
    assert orm is not None
    assert orm.status == StatusEnum.FAILED.value
    assert orm.error_message == "Processing error"
    assert orm.error_origin == "detection_service"
    assert orm.started_at is not None


# ==================== GET BY ID Tests ====================


def test_get_by_id_existing(sqlmodel_image_analysis_repo, session, sample_aggregate):
    """Test retrieving an existing aggregate by ID."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    session.commit()

    retrieved = sqlmodel_image_analysis_repo.get_by_id(sample_aggregate.id)

    assert retrieved is not None
    assert retrieved.id == sample_aggregate.id
    assert retrieved.source_image_id == sample_aggregate.source_image_id
    assert retrieved.status.value == sample_aggregate.status.value


def test_get_by_id_nonexistent(sqlmodel_image_analysis_repo):
    """Test retrieving a non-existent aggregate returns None."""
    fake_id = ImageAnalysisID.next_id()
    retrieved = sqlmodel_image_analysis_repo.get_by_id(fake_id)
    assert retrieved is None


def test_get_by_id_with_items(
    sqlmodel_image_analysis_repo, session, aggregate_with_items
):
    """Test that retrieved aggregate includes clothing items."""
    sqlmodel_image_analysis_repo.add(aggregate_with_items)
    session.commit()

    retrieved = sqlmodel_image_analysis_repo.get_by_id(aggregate_with_items.id)

    assert retrieved is not None
    assert len(retrieved.clothing_items) == 1

    item = list(retrieved.clothing_items.values())[0]
    assert item.bbox.x_min == 10
    assert item.label.category.value == "shirt"


def test_get_by_id_with_steps(
    sqlmodel_image_analysis_repo, session, preprocessing_aggregate
):
    """Test that retrieved aggregate includes processing steps."""
    sqlmodel_image_analysis_repo.add(preprocessing_aggregate)
    session.commit()

    retrieved = sqlmodel_image_analysis_repo.get_by_id(preprocessing_aggregate.id)

    assert retrieved is not None
    assert len(retrieved.p_history.steps) >= 2


def test_get_by_id_preserves_all_data(
    sqlmodel_image_analysis_repo, session, completed_aggregate
):
    """Test that all aggregate data is correctly reconstituted."""
    sqlmodel_image_analysis_repo.add(completed_aggregate)
    session.commit()

    retrieved = sqlmodel_image_analysis_repo.get_by_id(completed_aggregate.id)

    assert retrieved is not None
    assert retrieved.id == completed_aggregate.id
    assert retrieved.source_image_id == completed_aggregate.source_image_id
    assert retrieved.preprocessed_image_id == completed_aggregate.preprocessed_image_id
    assert retrieved.status.value == completed_aggregate.status.value
    assert len(retrieved.clothing_items) == len(completed_aggregate.clothing_items)
    assert len(retrieved.p_history.steps) == len(
        completed_aggregate.p_history.steps
    )
    assert retrieved.timestamps.created_at == completed_aggregate.timestamps.created_at


# ==================== LIST ALL Tests ====================


def test_list_all_empty(sqlmodel_image_analysis_repo):
    """Test listing when repository is empty."""
    aggregates = sqlmodel_image_analysis_repo.list_all()
    assert aggregates == []


def test_list_all_single(sqlmodel_image_analysis_repo, session, sample_aggregate):
    """Test listing with a single aggregate."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    session.commit()

    aggregates = sqlmodel_image_analysis_repo.list_all()
    assert len(aggregates) == 1
    assert aggregates[0].id == sample_aggregate.id


def test_list_all_multiple(sqlmodel_image_analysis_repo, session, factory):
    """Test listing multiple aggregates."""
    aggregates_to_add = []
    for _ in range(5):
        source_id = ImageArtifactID.next_id()
        agg = factory.create(source_id)
        aggregates_to_add.append(agg)
        sqlmodel_image_analysis_repo.add(agg)

    session.commit()

    retrieved = sqlmodel_image_analysis_repo.list_all()
    assert len(retrieved) == 5

    retrieved_ids = {agg.id for agg in retrieved}
    expected_ids = {agg.id for agg in aggregates_to_add}
    assert retrieved_ids == expected_ids


def test_list_all_includes_related_data(
    sqlmodel_image_analysis_repo, session, completed_aggregate
):
    """Test that list_all includes clothing items and steps."""
    sqlmodel_image_analysis_repo.add(completed_aggregate)
    session.commit()

    aggregates = sqlmodel_image_analysis_repo.list_all()
    assert len(aggregates) == 1

    retrieved = aggregates[0]
    assert len(retrieved.clothing_items) == 3
    assert len(retrieved.p_history.steps) > 0


# ==================== FIND BY SPECIFICATION Tests ====================


def test_find_by_specification_none(
    sqlmodel_image_analysis_repo, session, sample_aggregate
):
    """Test finding without specification returns all."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    session.commit()

    results = sqlmodel_image_analysis_repo.find_by_specification(None)
    assert len(results) == 1


def test_find_by_status(sqlmodel_image_analysis_repo, session, factory):
    """Test finding aggregates by status."""
    # Add aggregates with different statuses
    created_agg = factory.create(ImageArtifactID.next_id())
    processing_agg = factory.create(ImageArtifactID.next_id())
    processing_agg.start()
    processing_agg.start_preprocessing()
    completed_agg = factory.create(ImageArtifactID.next_id())
    completed_agg.start()
    completed_agg.start_preprocessing()
    completed_agg.finish_preprocessing(ImageArtifactID.next_id())

    sqlmodel_image_analysis_repo.add(created_agg)
    sqlmodel_image_analysis_repo.add(processing_agg)
    sqlmodel_image_analysis_repo.add(completed_agg)
    session.commit()

    # Find only PROCESSING
    spec = FieldSpecification("status", "eq", StatusEnum.PREPROCESSING.value)
    results = sqlmodel_image_analysis_repo.find_by_specification(spec)

    assert len(results) == 1
    assert results[0].status.value.value == StatusEnum.PREPROCESSING.value


def test_find_by_source_image_id(sqlmodel_image_analysis_repo, session, factory):
    """Test finding aggregates by source image ID."""
    source_id = ImageArtifactID.next_id()
    agg1 = factory.create(source_id)
    agg2 = factory.create(ImageArtifactID.next_id())

    sqlmodel_image_analysis_repo.add(agg1)
    sqlmodel_image_analysis_repo.add(agg2)
    session.commit()

    spec = FieldSpecification("source_image_id", "eq", str(source_id))
    results = sqlmodel_image_analysis_repo.find_by_specification(spec)

    assert len(results) == 1
    assert results[0].source_image_id == source_id


def test_find_with_and_specification(sqlmodel_image_analysis_repo, session, factory):
    """Test finding with combined specifications."""
    source_id = ImageArtifactID.next_id()
    agg = factory.create(source_id)
    agg.start()
    agg.start_preprocessing()

    sqlmodel_image_analysis_repo.add(agg)
    session.commit()

    spec1 = FieldSpecification("source_image_id", "eq", str(source_id))
    spec2 = FieldSpecification("status", "eq", StatusEnum.PREPROCESSING.value)
    combined_spec = AndSpecification(spec1, spec2)

    results = sqlmodel_image_analysis_repo.find_by_specification(combined_spec)

    assert len(results) == 1
    assert results[0].source_image_id == source_id
    assert results[0].status.value.value == StatusEnum.PREPROCESSING.value


def test_find_no_matches(sqlmodel_image_analysis_repo, session, sample_aggregate):
    """Test finding with specification that matches nothing."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    session.commit()

    spec = FieldSpecification("status", "eq", StatusEnum.COMPLETED.value)
    results = sqlmodel_image_analysis_repo.find_by_specification(spec)

    assert len(results) == 0


# ==================== UPDATE Tests ====================


def test_update_status(sqlmodel_image_analysis_repo, session, sample_aggregate):
    """Test updating aggregate status."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    session.commit()

    # Update status
    sample_aggregate.start()
    sample_aggregate.start_preprocessing()
    sqlmodel_image_analysis_repo.update(sample_aggregate)
    session.commit()

    # Verify in database
    orm = session.get(ImageAnalysisORM, str(sample_aggregate.id))
    assert orm.status == StatusEnum.PREPROCESSING.value
    assert orm.started_at is not None


def test_update_add_clothing_item(
    sqlmodel_image_analysis_repo, session, sample_aggregate
):
    """Test adding a clothing item to existing aggregate."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    session.commit()

    # Add item
    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=sample_aggregate.id,
        bbox=BoundingBox(x_min=10, y_min=20, x_max=100, y_max=200),
        label=Label(
            category=DescriptiveString("shirt"),
            pattern=DescriptiveString("striped"),
            style=DescriptiveString("casual"),
            color=DescriptiveString("blue"),
        ),
        cropped_image_id=None,
        embedding_id=None,
    )
    sample_aggregate.add_clothing_item(item)

    sqlmodel_image_analysis_repo.update(sample_aggregate)
    session.commit()

    # Verify
    items = session.exec(
        select(ClothingItemORM).where(
            ClothingItemORM.image_aggregate_id == str(sample_aggregate.id)
        )
    ).all()

    assert len(items) == 1
    assert items[0].label_category == "shirt"


def test_update_remove_clothing_item(
    sqlmodel_image_analysis_repo, session, aggregate_with_items
):
    """Test removing a clothing item from aggregate."""
    sqlmodel_image_analysis_repo.add(aggregate_with_items)
    session.commit()

    # Remove item
    items = list(aggregate_with_items.clothing_items.values())
    aggregate_with_items.remove_clothing_item(items[0])

    sqlmodel_image_analysis_repo.update(aggregate_with_items)
    session.commit()

    # Verify deleted
    items = session.exec(
        select(ClothingItemORM).where(
            ClothingItemORM.image_aggregate_id == str(aggregate_with_items.id)
        )
    ).all()

    assert len(items) == 0


def test_update_modify_clothing_item(
    sqlmodel_image_analysis_repo, session, aggregate_with_items
):
    """Test modifying an existing clothing item."""
    sqlmodel_image_analysis_repo.add(aggregate_with_items)
    session.commit()

    # Modify item
    item_id = list(aggregate_with_items.clothing_items.keys())[0]
    item = aggregate_with_items.clothing_items[item_id]

    # Set embedding and cropped image
    embedding_id = EmbeddingId.next_id()
    cropped_id = ImageArtifactID.next_id()
    item.attach_embedding(embedding_id)
    item.attach_cropped_image(cropped_id)

    sqlmodel_image_analysis_repo.update(aggregate_with_items)
    session.commit()

    # Verify
    item_orm = session.get(ClothingItemORM, str(item_id))
    assert item_orm.embedding_id == str(embedding_id)
    assert item_orm.cropped_image_id == str(cropped_id)


def test_update_append_processing_steps(
    sqlmodel_image_analysis_repo, session, preprocessing_aggregate
):
    """Test that update appends new processing steps without duplicating."""
    sqlmodel_image_analysis_repo.add(preprocessing_aggregate)
    session.commit()

    initial_steps_count = len(preprocessing_aggregate.p_history.steps)

    # Complete processing (adds COMPLETED step)
    preprocessing_aggregate.finish_preprocessing(
        preprocessed_image_id=ImageArtifactID.next_id()
    )

    sqlmodel_image_analysis_repo.update(preprocessing_aggregate)
    session.commit()

    # Verify steps in database
    steps = session.exec(
        select(ProcessingStepORM).where(
            ProcessingStepORM.image_aggregate_id == str(preprocessing_aggregate.id)
        )
    ).all()

    # Should have one more step
    assert len(steps) == initial_steps_count + 1

    # Verify COMPLETED step exists
    statuses = [step.status for step in steps]
    assert StatusEnum.PREPROCESSED.value in statuses


def test_update_idempotent_steps(
    sqlmodel_image_analysis_repo, session, preprocessing_aggregate
):
    """Test that updating twice doesn't duplicate steps."""
    sqlmodel_image_analysis_repo.add(preprocessing_aggregate)
    session.commit()

    # First update
    sqlmodel_image_analysis_repo.update(preprocessing_aggregate)
    session.commit()

    steps_after_first = session.exec(
        select(ProcessingStepORM).where(
            ProcessingStepORM.image_aggregate_id == str(preprocessing_aggregate.id)
        )
    ).all()

    first_count = len(steps_after_first)

    # Second update without changes
    sqlmodel_image_analysis_repo.update(preprocessing_aggregate)
    session.commit()

    steps_after_second = session.exec(
        select(ProcessingStepORM).where(
            ProcessingStepORM.image_aggregate_id == str(preprocessing_aggregate.id)
        )
    ).all()

    # Count should be the same
    assert len(steps_after_second) == first_count


def test_update_set_error(
    sqlmodel_image_analysis_repo, session, preprocessing_aggregate
):
    """Test updating aggregate to failed status with error."""
    sqlmodel_image_analysis_repo.add(preprocessing_aggregate)
    session.commit()

    preprocessing_aggregate.fail("Test error", "test_service")

    sqlmodel_image_analysis_repo.update(preprocessing_aggregate)
    session.commit()

    orm = session.get(ImageAnalysisORM, str(preprocessing_aggregate.id))
    assert orm.status == StatusEnum.FAILED.value
    assert orm.error_message == "Test error"
    assert orm.error_origin == "test_service"


def test_update_nonexistent_aggregate_raises(sqlmodel_image_analysis_repo, factory):
    """Test that updating a non-existent aggregate raises error."""
    agg = factory.create(ImageArtifactID.next_id())

    with pytest.raises(ValueError, match="ImageAnalysisAggregate not found"):
        sqlmodel_image_analysis_repo.update(agg)


# ==================== DELETE Tests ====================


def test_delete_existing_aggregate(
    sqlmodel_image_analysis_repo, session, sample_aggregate
):
    """Test deleting an existing aggregate."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    session.commit()

    sqlmodel_image_analysis_repo.delete(sample_aggregate.id)
    session.commit()

    # Verify deleted
    orm = session.get(ImageAnalysisORM, str(sample_aggregate.id))
    assert orm is None


def test_delete_cascade_clothing_items(
    sqlmodel_image_analysis_repo, session, aggregate_with_items
):
    """Test that deleting aggregate cascades to clothing items."""
    sqlmodel_image_analysis_repo.add(aggregate_with_items)
    session.commit()

    aggregate_id = aggregate_with_items.id

    sqlmodel_image_analysis_repo.delete(aggregate_id)
    session.commit()

    # Verify items deleted
    items = session.exec(
        select(ClothingItemORM).where(
            ClothingItemORM.image_aggregate_id == str(aggregate_id)
        )
    ).all()

    assert len(items) == 0


def test_delete_cascade_processing_steps(
    sqlmodel_image_analysis_repo, session, preprocessing_aggregate
):
    """Test that deleting aggregate cascades to processing steps."""
    sqlmodel_image_analysis_repo.add(preprocessing_aggregate)
    session.commit()

    aggregate_id = preprocessing_aggregate.id

    sqlmodel_image_analysis_repo.delete(aggregate_id)
    session.commit()

    # Verify steps deleted
    steps = session.exec(
        select(ProcessingStepORM).where(
            ProcessingStepORM.image_aggregate_id == str(aggregate_id)
        )
    ).all()

    assert len(steps) == 0


def test_delete_nonexistent_aggregate_silent(sqlmodel_image_analysis_repo, session):
    """Test that deleting non-existent aggregate doesn't raise error."""
    fake_id = ImageAnalysisID.next_id()

    # Should not raise
    sqlmodel_image_analysis_repo.delete(fake_id)
    session.commit()


# ==================== FLUSH Tests ====================


def test_flush_persists_changes(
    sqlmodel_image_analysis_repo, session, sample_aggregate
):
    """Test that flush persists changes within transaction."""
    sqlmodel_image_analysis_repo.add(sample_aggregate)
    sqlmodel_image_analysis_repo.flush()

    # Should be queryable within same transaction
    orm = session.get(ImageAnalysisORM, str(sample_aggregate.id))
    assert orm is not None

    # Rollback to verify it was only flushed
    session.rollback()

    orm = session.get(ImageAnalysisORM, str(sample_aggregate.id))
    assert orm is None


# ==================== Edge Cases ====================


def test_multiple_aggregates_same_source_image(
    sqlmodel_image_analysis_repo, session, factory
):
    """Test that multiple aggregates can reference the same source image."""
    source_id = ImageArtifactID.next_id()

    agg1 = factory.create(source_id)
    agg2 = factory.create(source_id)

    sqlmodel_image_analysis_repo.add(agg1)
    sqlmodel_image_analysis_repo.add(agg2)
    session.commit()

    spec = FieldSpecification("source_image_id", "eq", str(source_id))
    results = sqlmodel_image_analysis_repo.find_by_specification(spec)

    assert len(results) == 2


def test_timestamp_preservation(
    sqlmodel_image_analysis_repo, session, completed_aggregate
):
    """Test that timestamps are preserved through persistence and reconstitution."""
    original_created = completed_aggregate.timestamps.created_at
    original_started = completed_aggregate.timestamps.started_at


    sqlmodel_image_analysis_repo.add(completed_aggregate)
    session.commit()

    retrieved = sqlmodel_image_analysis_repo.get_by_id(completed_aggregate.id)

    assert retrieved is not None
    assert retrieved.timestamps.created_at == original_created
    assert retrieved.timestamps.started_at == original_started


def test_processing_steps_order_preserved(
    sqlmodel_image_analysis_repo, session, completed_aggregate
):
    """Test that processing steps maintain chronological order."""
    sqlmodel_image_analysis_repo.add(completed_aggregate)
    session.commit()

    retrieved = sqlmodel_image_analysis_repo.get_by_id(completed_aggregate.id)

    assert retrieved is not None
    steps = retrieved.p_history.steps

    # Verify chronological order
    for i in range(len(steps) - 1):
        assert steps[i].timestamp <= steps[i + 1].timestamp
