import pytest
from datetime import datetime, timezone
from src.domain.shared.value_objects import DescriptiveString
from src.domain.image_analysis.factories.image_analysis_factory import (
    ImageAnalysisFactory,
)
from src.domain.image_analysis.aggregates.image_analysis_aggregate import (
    ImageAnalysisAggregate,
)
from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.image_analysis.value_objects.clothing_item_vos import (
    BoundingBox,
    ClothingItemId,
    Label,
)
from src.domain.image_analysis.value_objects.image_analysis_vos import (
    AnalysisError,
    AnalysisStatus,
    AnalysisTimestamps,
    ImageAnalysisID,
    ProcessingStep,
    StatusEnum,
)
from src.domain.shared.value_objects import ImageArtifactID, EmbeddingId
from src.domain.image_analysis.errors import CorruptedAggregateError


@pytest.fixture
def factory():
    return ImageAnalysisFactory()


@pytest.fixture
def sample_image_id():
    return ImageArtifactID.next_id()


@pytest.fixture
def sample_timestamps():
    return AnalysisTimestamps(
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        started_at=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
        completed_at=None,
    )


def create_sample_clothing_item_for_agg(img_agg_id: ImageAnalysisID):
    return ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=img_agg_id,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
        label=Label(
            color=DescriptiveString("blue"),
            style=DescriptiveString("casual"),
            pattern=DescriptiveString("solid"),
            category=DescriptiveString("t-shirt"),
        ),
        cropped_image_id=ImageArtifactID.next_id(),
        embedding_id=EmbeddingId.next_id(),
    )


# Creation
def test_create_returns_aggregate_with_created_status(factory, sample_image_id):
    aggregate = factory.create(sample_image_id)

    assert isinstance(aggregate, ImageAnalysisAggregate)
    assert aggregate.status.value == StatusEnum.CREATED


def test_create_sets_source_image_id(factory, sample_image_id):
    aggregate = factory.create(sample_image_id)

    assert aggregate.source_image_id == sample_image_id


def test_create_initializes_timestamps(factory, sample_image_id):
    before = datetime.now(timezone.utc)
    aggregate = factory.create(sample_image_id)
    after = datetime.now(timezone.utc)

    assert before <= aggregate.timestamps.created_at <= after
    assert aggregate.timestamps.started_at is None
    assert aggregate.timestamps.completed_at is None


def test_create_initializes_empty_processing_history(factory, sample_image_id):
    aggregate = factory.create(sample_image_id)

    assert len(aggregate.p_history.steps) == 0


def test_create_initializes_empty_clothing_items(factory, sample_image_id):
    aggregate = factory.create(sample_image_id)

    assert len(aggregate.clothing_items) == 0


def test_create_generates_unique_ids(factory, sample_image_id):
    aggregate1 = factory.create(sample_image_id)
    aggregate2 = factory.create(sample_image_id)

    assert aggregate1.id != aggregate2.id


# Reconstitute
def test_reconstitute_with_created_status(factory, sample_image_id, sample_timestamps):
    analysis_id = ImageAnalysisID.next_id()
    status = AnalysisStatus(StatusEnum.CREATED)
    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=None,
        completed_at=None,
        source_img_id=sample_image_id,
        preprocessed_img_id=None,
        clothing_items=[],
        status=status,
        steps=[],
        error=None,
    )

    assert aggregate.id == analysis_id
    assert aggregate.status.value == StatusEnum.CREATED
    assert aggregate.source_image_id == sample_image_id
    assert aggregate.timestamps.created_at == sample_timestamps.created_at
    assert len(aggregate.clothing_items) == 0


def test_reconstitute_with_preprocessed_status(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    preprocessed_id = ImageArtifactID.next_id()
    status = AnalysisStatus(StatusEnum.PREPROCESSED)

    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=None,
        source_img_id=sample_image_id,
        preprocessed_img_id=preprocessed_id,
        clothing_items=[],
        status=status,
        steps=[],
        error=None,
    )

    assert aggregate.status.value == StatusEnum.PREPROCESSED
    assert aggregate.preprocessed_image_id == preprocessed_id
    assert aggregate.timestamps.started_at == sample_timestamps.started_at


def test_reconstitute_with_detected_status_and_items(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    preprocessed_id = ImageArtifactID.next_id()
    status = AnalysisStatus(StatusEnum.DETECTED)

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=analysis_id,
        label=None,
        cropped_image_id=None,
        embedding_id=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )

    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=None,
        source_img_id=sample_image_id,
        preprocessed_img_id=preprocessed_id,
        clothing_items=[item],
        status=status,
        steps=[],
        error=None,
    )

    assert aggregate.status.value == StatusEnum.DETECTED
    assert len(aggregate.clothing_items) == 1


def test_reconstitute_with_described_status_requires_labels(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    preprocessed_id = ImageAnalysisID.next_id()
    status = AnalysisStatus(StatusEnum.DESCRIBED)

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=analysis_id,
        label=Label(
            color=DescriptiveString("blue"),
            style=DescriptiveString("casual"),
            pattern=DescriptiveString("solid"),
            category=DescriptiveString("t-shirt"),
        ),
        cropped_image_id=None,
        embedding_id=None,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
    )

    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=None,
        source_img_id=sample_image_id,
        preprocessed_img_id=preprocessed_id,
        clothing_items=[item],
        status=status,
        steps=[],
        error=None,
    )

    assert aggregate.status.value == StatusEnum.DESCRIBED
    assert aggregate.clothing_items[item.id].label.category.value == "t-shirt"
    assert aggregate.clothing_items[item.id].label.pattern.value == "solid"
    assert aggregate.clothing_items[item.id].label.style.value == "casual"
    assert aggregate.clothing_items[item.id].label.color.value == "blue"


def test_reconstitute_with_embedded_status_requires_all_fields(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    preprocessed_id = ImageArtifactID.next_id()
    status = AnalysisStatus(StatusEnum.EMBEDDED)
    item = create_sample_clothing_item_for_agg(analysis_id)

    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=None,
        source_img_id=sample_image_id,
        preprocessed_img_id=preprocessed_id,
        clothing_items=[item],
        status=status,
        steps=[],
        error=None,
    )

    assert aggregate.status.value == StatusEnum.EMBEDDED
    assert aggregate.clothing_items[item.id].label is not None
    assert aggregate.clothing_items[item.id].embedding_id is not None


def test_reconstitute_with_no_cloths_status(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    preprocessed_id = ImageArtifactID.next_id()
    status = AnalysisStatus(StatusEnum.NO_CLOTHS)

    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=None,
        source_img_id=sample_image_id,
        preprocessed_img_id=preprocessed_id,
        clothing_items=[],
        status=status,
        steps=[],
        error=None,
    )

    assert aggregate.status.value == StatusEnum.NO_CLOTHS
    assert len(aggregate.clothing_items) == 0


def test_reconstitute_with_failed_status(factory, sample_image_id, sample_timestamps):
    analysis_id = ImageAnalysisID.next_id()
    preprocessed_id = ImageArtifactID.next_id()
    status = AnalysisStatus(StatusEnum.FAILED)
    error = AnalysisError(message="Processing failed", origin="detector")

    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=None,
        source_img_id=sample_image_id,
        preprocessed_img_id=preprocessed_id,
        clothing_items=[],
        status=status,
        steps=[],
        error=error,
    )

    assert aggregate.status.value == StatusEnum.FAILED
    assert aggregate.error.message == "Processing failed"


def test_reconstitute_with_processing_steps(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    status = AnalysisStatus(StatusEnum.STARTED)

    step1 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.CREATED), attempt=1, message="Created"
    )
    step2 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.STARTED), attempt=1, message="Started"
    )

    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=None,
        source_img_id=sample_image_id,
        preprocessed_img_id=None,
        clothing_items=[],
        status=status,
        steps=[step1, step2],
        error=None,
    )

    assert len(aggregate.p_history.steps) == 2
    assert aggregate.p_history.steps[0].status.value == StatusEnum.CREATED


def test_reconstitute_completed_from_embedded(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    status = AnalysisStatus(StatusEnum.COMPLETED)
    preprocessed_id = ImageArtifactID.next_id()

    step1 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.EMBEDDED), attempt=1, message="Embedded"
    )
    step2 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.COMPLETED),
        attempt=1,
        message="Completed from EMBEDDED",
    )

    item = create_sample_clothing_item_for_agg(analysis_id)

    aggregate = factory.reconstitute(
        id=analysis_id,
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=datetime.now(timezone.utc),
        source_img_id=sample_image_id,
        preprocessed_img_id=preprocessed_id,
        clothing_items=[item],
        status=status,
        steps=[step1, step2],
        error=None,
    )

    assert aggregate.status.value == StatusEnum.COMPLETED
    assert len(aggregate.clothing_items) == 1


def test_completed_from_no_cloths_successfully(
    factory, sample_image_id, sample_timestamps
):
    status = AnalysisStatus(StatusEnum.COMPLETED)
    preprocessed_id = ImageArtifactID.next_id()

    step1 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.NO_CLOTHS), attempt=1, message="no cloths"
    )
    step2 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.COMPLETED),
        attempt=1,
        message="Completed from no cloths",
    )

    aggregate = factory.reconstitute(
        id=ImageAnalysisID.next_id(),
        created_at=sample_timestamps.created_at,
        started_at=sample_timestamps.started_at,
        completed_at=datetime.now(timezone.utc),
        source_img_id=sample_image_id,
        preprocessed_img_id=preprocessed_id,
        clothing_items=[],
        status=status,
        steps=[step1, step2],
        error=None,
    )

    assert aggregate.status.value == StatusEnum.COMPLETED
    assert len(aggregate.clothing_items) == 0


# Validation Errors
def test_preprocessed_without_preprocessed_image_id_raises_error(
    factory, sample_image_id, sample_timestamps
):
    status = AnalysisStatus(StatusEnum.PREPROCESSED)

    with pytest.raises(CorruptedAggregateError, match="missing preprocessed_image_id"):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            created_at=sample_timestamps.created_at,
            started_at=None,
            completed_at=None,
            source_img_id=sample_image_id,
            preprocessed_img_id=None,  # Missing!
            clothing_items=[],
            status=status,
            steps=[],
            error=None,
        )


def test_detected_without_items_raises_error(
    factory, sample_image_id, sample_timestamps
):
    status = AnalysisStatus(StatusEnum.DETECTED)
    preprocessed_id = ImageArtifactID.next_id()

    with pytest.raises(CorruptedAggregateError, match="missing clothing items"):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=None,
            source_img_id=sample_image_id,
            preprocessed_img_id=preprocessed_id,
            clothing_items=[],  # Empty!
            status=status,
            steps=[],
            error=None,
        )


def test_described_without_labels_raises_error(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    status = AnalysisStatus(StatusEnum.DESCRIBED)
    preprocessed_id = ImageArtifactID.next_id()

    item_without_label = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=analysis_id,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
        label=None,  # Missing label!
        cropped_image_id=None,
        embedding_id=None,
    )

    with pytest.raises(CorruptedAggregateError, match="missing label"):
        factory.reconstitute(
            id=analysis_id,
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=None,
            source_img_id=sample_image_id,
            preprocessed_img_id=preprocessed_id,
            clothing_items=[item_without_label],
            status=status,
            steps=[],
            error=None,
        )


def test_embedded_without_embedding_id_raises_error(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    status = AnalysisStatus(StatusEnum.EMBEDDED)
    preprocessed_id = ImageArtifactID.next_id()

    item_without_embedding = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=analysis_id,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
        label=Label(
            color=DescriptiveString("blue"),
            style=DescriptiveString("casual"),
            pattern=DescriptiveString("solid"),
            category=DescriptiveString("t-shirt"),
        ),
        cropped_image_id=None,
        embedding_id=None,  # Missing embedding!
    )
    with pytest.raises(CorruptedAggregateError, match="missing embedding_id"):
        factory.reconstitute(
            id=analysis_id,
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=None,
            source_img_id=sample_image_id,
            preprocessed_img_id=preprocessed_id,
            clothing_items=[item_without_embedding],
            status=status,
            steps=[],
            error=None,
        )


def test_completed_without_preprocessed_image_id_raises_error(
    factory, sample_image_id, sample_timestamps
):
    status = AnalysisStatus(StatusEnum.COMPLETED)

    with pytest.raises(CorruptedAggregateError, match="requires preprocessed_image_id"):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
            source_img_id=sample_image_id,
            preprocessed_img_id=None,  # Missing preprocessed img id!
            clothing_items=[],
            status=status,
            steps=[],
            error=None,
        )


def test_completed_from_no_cloths_with_items_raises_error(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    status = AnalysisStatus(StatusEnum.COMPLETED)
    preprocessed_id = ImageArtifactID.next_id()

    # Setup previous step as NO_CLOTHS
    step1 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.NO_CLOTHS),
        attempt=1,
        message="No clothes detected",
    )
    step2 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.COMPLETED),
        attempt=1,
        message="Completed from NO_CLOTHS",
    )
    item = create_sample_clothing_item_for_agg(analysis_id)

    with pytest.raises(
        CorruptedAggregateError, match="NO_CLOTHS must have zero clothing_items"
    ):
        factory.reconstitute(
            id=analysis_id,
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=datetime.now(timezone.utc),
            source_img_id=sample_image_id,
            preprocessed_img_id=preprocessed_id,
            clothing_items=[item],  # Should be empty!
            status=status,
            steps=[step1, step2],
            error=None,
        )


def test_completed_from_embedded_without_items_raises_error(
    factory, sample_image_id, sample_timestamps
):
    status = AnalysisStatus(StatusEnum.COMPLETED)
    preprocessed_id = ImageArtifactID.next_id()

    step1 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.EMBEDDED), attempt=1, message="Embedded"
    )
    step2 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.COMPLETED),
        attempt=1,
        message="Completed from EMBEDDED",
    )

    with pytest.raises(
        CorruptedAggregateError, match="EMBEDDED requires clothing_items"
    ):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=datetime.now(timezone.utc),
            source_img_id=sample_image_id,
            preprocessed_img_id=preprocessed_id,
            clothing_items=[],  # Should have items!
            status=status,
            steps=[step1, step2],
            error=None,
        )


def test_completed_from_embedded_without_labels_raises_error(
    factory, sample_image_id, sample_timestamps
):
    analysis_id = ImageAnalysisID.next_id()
    status = AnalysisStatus(StatusEnum.COMPLETED)
    preprocessed_id = ImageArtifactID.next_id()

    step1 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.EMBEDDED), attempt=1, message="Embedded"
    )
    step2 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.COMPLETED),
        attempt=1,
        message="Completed from EMBEDDED",
    )

    item = ClothingItem(
        id=ClothingItemId.next_id(),
        image_aggregate_id=analysis_id,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
        label=None,  # Missing label!
        cropped_image_id=ImageArtifactID.next_id(),
        embedding_id=EmbeddingId.next_id(),
    )

    with pytest.raises(CorruptedAggregateError, match="all items to have label"):
        factory.reconstitute(
            id=analysis_id,
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=datetime.now(timezone.utc),
            source_img_id=sample_image_id,
            preprocessed_img_id=preprocessed_id,
            clothing_items=[item],
            status=status,
            steps=[step1, step2],
            error=None,
        )


def test_completed_with_invalid_previous_status_raises_error(
    factory, sample_image_id, sample_timestamps
):
    status = AnalysisStatus(StatusEnum.COMPLETED)
    preprocessed_id = ImageArtifactID.next_id()

    step1 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.STARTED), attempt=1, message="Started"
    )
    step2 = ProcessingStep.new(
        status=AnalysisStatus(StatusEnum.COMPLETED),
        attempt=1,
        message="Completed from wrong status",
    )
    with pytest.raises(
        CorruptedAggregateError, match="inconsistent with previous non-failed status"
    ):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=datetime.now(timezone.utc),
            source_img_id=sample_image_id,
            preprocessed_img_id=preprocessed_id,
            clothing_items=[],
            status=status,
            steps=[step1, step2],
            error=None,
        )

    # Items Fields


def test_all_items_have_field_returns_true_when_all_have_field(factory):
    analysis_id = ImageAnalysisID.next_id()
    items = {
        ClothingItemId.next_id(): ClothingItem(
            id=ClothingItemId.next_id(),
            image_aggregate_id=analysis_id,
            bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
            label=Label(
                color=DescriptiveString("blue"),
                style=DescriptiveString("casual"),
                pattern=DescriptiveString("solid"),
                category=DescriptiveString("t-shirt"),
            ),
            cropped_image_id=None,
            embedding_id=None,
        ),
        ClothingItemId.next_id(): ClothingItem(
            id=ClothingItemId.next_id(),
            image_aggregate_id=analysis_id,
            bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
            label=Label(
                color=DescriptiveString("red"),
                style=DescriptiveString("formal"),
                pattern=DescriptiveString("solid"),
                category=DescriptiveString("t-shirt"),
            ),
            cropped_image_id=None,
            embedding_id=None,
        ),
    }

    result = factory.rules.all_items_have_field(items, "label")

    assert result is True


def test_all_items_have_field_returns_false_when_field_is_none(factory):
    items = {
        ClothingItemId.next_id(): ClothingItem(
            id=ClothingItemId.next_id(),
            image_aggregate_id=ImageAnalysisID.next_id(),
            bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
            label=None,
            cropped_image_id=None,
            embedding_id=None,
        ),
    }

    result = factory.rules.all_items_have_field(items, "label")

    assert result is False


def test_all_items_have_field_returns_false_when_field_missing(factory):
    items = {
        ClothingItemId.next_id(): ClothingItem(
            id=ClothingItemId.next_id(),
            image_aggregate_id=ImageAnalysisID.next_id(),
            bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
            label=None,
            cropped_image_id=None,
            embedding_id=None,
        ),
    }

    result = factory.rules.all_items_have_field(items, "nonexistent_field")

    assert result is False


def test_all_items_have_field_returns_true_for_empty_dict(factory):
    items = {}

    result = factory.rules.all_items_have_field(items, "label")

    assert result is True


# TODO: test timestamps and duplicates items or worng ids.

# timestamps


def test_timestamp_missing_fields_raises(factory, sample_timestamps):

    with pytest.raises(
        CorruptedAggregateError,
        match="Image Analysis timestamp missing created_at in status",
    ):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            source_img_id=ImageArtifactID.next_id(),
            preprocessed_img_id=None,
            created_at=None,  # Missing created_at
            started_at=sample_timestamps.started_at,
            completed_at=None,
            status=AnalysisStatus(StatusEnum.STARTED),
            clothing_items=[],
            steps=(),
            error=None
        )
    with pytest.raises(
        CorruptedAggregateError,
        match="Image Analysis timestamp missing started_at in status",
    ):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            source_img_id=ImageArtifactID.next_id(),
            preprocessed_img_id=None,
            created_at=sample_timestamps.created_at,
            started_at=None,  # Missing started at
            completed_at=None,
            status=AnalysisStatus(StatusEnum.STARTED),
            clothing_items=[],
            steps=(),
            error=None
        )

    step1 = ProcessingStep(
        status=AnalysisStatus(StatusEnum.NO_CLOTHS),
        timestamp=sample_timestamps.started_at,
    )
    step2 = ProcessingStep(
        status=AnalysisStatus(StatusEnum.COMPLETED),
        timestamp=sample_timestamps.started_at,
    )
    with pytest.raises(
        CorruptedAggregateError,
        match="Image Analysis timestamp missing completed_at in status",
    ):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            source_img_id=ImageArtifactID.next_id(),
            preprocessed_img_id=None,
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=None,  # Missing completed_at
            status=AnalysisStatus(StatusEnum.COMPLETED),
            clothing_items=[],
            steps=(step1, step2),
            error=None
        )


def test_list_items_duplicates_raises(factory, sample_timestamps):
    analysis_id = ImageAnalysisID.next_id()
    item_same_id = ClothingItemId.next_id()

    item1 = ClothingItem(
        id=item_same_id,
        image_aggregate_id=analysis_id,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
        label=Label(
            color=DescriptiveString("blue"),
            style=DescriptiveString("casual"),
            pattern=DescriptiveString("solid"),
            category=DescriptiveString("t-shirt"),
        ),
        cropped_image_id=ImageArtifactID.next_id(),
        embedding_id=EmbeddingId.next_id(),
    )
    item2 = ClothingItem(
        id=item_same_id,
        image_aggregate_id=analysis_id,
        bbox=BoundingBox(x_min=10, x_max=100, y_min=10, y_max=100),
        label=Label(
            color=DescriptiveString("blue"),
            style=DescriptiveString("casual"),
            pattern=DescriptiveString("solid"),
            category=DescriptiveString("t-shirt"),
        ),
        cropped_image_id=ImageArtifactID.next_id(),
        embedding_id=EmbeddingId.next_id(),
    )

    with pytest.raises(
        CorruptedAggregateError,
        match="Duplicate item ID found:",
    ):
        factory.reconstitute(
            id=analysis_id,
            source_img_id=ImageArtifactID.next_id(),
            preprocessed_img_id=None,
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=None,
            status=AnalysisStatus(StatusEnum.DETECTED),
            clothing_items=[item1, item2],
            steps=(),
            error=None
        )
        
def test_list_items_wrong_origin_raises(factory, sample_timestamps):
    analysis_id = ImageAnalysisID.next_id()

    item1 = create_sample_clothing_item_for_agg(analysis_id)
    item2 = create_sample_clothing_item_for_agg(analysis_id)
    
    with pytest.raises(
        CorruptedAggregateError,
        match="Origin id mismatch",
    ):
        factory.reconstitute(
            id=ImageAnalysisID.next_id(),
            source_img_id=ImageArtifactID.next_id(),
            preprocessed_img_id=None,
            created_at=sample_timestamps.created_at,
            started_at=sample_timestamps.started_at,
            completed_at=None,
            status=AnalysisStatus(StatusEnum.DETECTED),
            clothing_items=[item1, item2],
            steps=(),
            error=None
        )