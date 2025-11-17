from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, NamedTuple, Type, TypeVar
from src.domain.shared.value_objects import (
    DescriptiveString,
    EmbeddingId,
    ImageArtifactID,
)
from src.domain.image_analysis.value_objects.clothing_item_vos import (
    BoundingBox,
    ClothingItemId,
    Label,
)
from src.domain.image_analysis.aggregates.image_analysis_aggregate import (
    ImageAnalysisAggregate,
)
from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.image_analysis.value_objects.image_analysis_vos import (
    AnalysisError,
    AnalysisStatus,
    ImageAnalysisID,
    ProcessingStep,
    StatusEnum,
)
from src.domain.image_analysis.factories.image_analysis_factory import (
    ImageAnalysisFactory,
)
from src.infrastructure.repositories.image_analysis.orms import (
    ImageAnalysisORM,
    ClothingItemORM,
    ProcessingStepORM,
)


@dataclass(frozen=True)
class Models:
    analysis: ImageAnalysisORM
    clothing_items: List[ClothingItemORM]
    steps: list[ProcessingStepORM]


@dataclass(frozen=True)
class LabelFields:
    category: str | None = None
    color: str | None = None
    pattern: str | None = None
    style: str | None = None


class ImageAnalysisMapper:
    """
    Converts between ImageArtifactORM <-> ImageArtifact domain entity.
    """

    factory: ImageAnalysisFactory

    def __init__(self) -> None:
        self.factory = ImageAnalysisFactory()

    def _make_datetime_aware(self, dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _label_from_fields(self, fields: LabelFields) -> Label | None:

        if (
            fields.category is not None
            and fields.color is not None
            and fields.pattern is not None
            and fields.style is not None
        ):
            return Label(
                category=DescriptiveString(fields.category),
                color=DescriptiveString(fields.color),
                pattern=DescriptiveString(fields.pattern),
                style=DescriptiveString(fields.style),
            )
        return None

    def _fields_from_label(self, label: Label | None) -> LabelFields:
        if not label:
            return LabelFields()
        return LabelFields(
            category=label.category.value,
            color=label.color.value,
            pattern=label.pattern.value,
            style=label.style.value,
        )

    def _create_error(
        self, error_message: str | None, origin: str | None
    ) -> AnalysisError | None:
        if not error_message:
            return None
        return AnalysisError(message=error_message, origin=origin)

    def _to_domain_clothing_item(self, item: ClothingItemORM) -> ClothingItem:
        label = self._label_from_fields(
            LabelFields(
                category=item.label_category,
                color=item.label_color,
                pattern=item.label_pattern,
                style=item.label_style,
            )
        )

        return ClothingItem(
            id=ClothingItemId(item.id),
            image_aggregate_id=ImageAnalysisID(item.image_aggregate_id),
            cropped_image_id=(
                ImageArtifactID(item.cropped_image_id)
                if item.cropped_image_id
                else None
            ),
            embedding_id=EmbeddingId(item.embedding_id) if item.embedding_id else None,
            label=label,
            bbox=BoundingBox(
                x_min=item.bbox_x_min,
                x_max=item.bbox_x_max,
                y_min=item.bbox_y_min,  # <- corrigido
                y_max=item.bbox_y_max,
            ),
        )

    def _to_orm_clothing_item(self, item: ClothingItem) -> ClothingItemORM:
        fields = self._fields_from_label(item.label)

        return ClothingItemORM(
            id=str(item.id),
            image_aggregate_id=str(item.image_aggregate_id),
            cropped_image_id=(
                str(item.cropped_image_id) if item.cropped_image_id else None
            ),
            embedding_id=str(item.embedding_id) if item.embedding_id else None,
            label_category=fields.category,
            label_color=fields.color,
            label_pattern=fields.pattern,
            label_style=fields.style,
            bbox_x_max=item.bbox.x_max,
            bbox_x_min=item.bbox.x_min,
            bbox_y_max=item.bbox.y_max,
            bbox_y_min=item.bbox.y_min,
        )

    def models_to_aggregate(self, models: Models) -> ImageAnalysisAggregate:
        """
        ORM → Domain
        """
        clothing_items = [
            self._to_domain_clothing_item(item) for item in models.clothing_items
        ]

        processing_step: List[ProcessingStep] = [
            ProcessingStep(
                status=AnalysisStatus(StatusEnum(step.status)),
                timestamp=step.timestamp,
                message=step.message,
                attempt=step.attempt,
            )
            for step in models.steps
        ]

        error = self._create_error(
            error_message=models.analysis.error_message,
            origin=models.analysis.error_origin,
        )

        created_timestamp = models.analysis.created_at.replace(tzinfo=timezone.utc) if models.analysis.created_at.tzinfo is None else models.analysis.created_at
        started_timestamp = self._make_datetime_aware(models.analysis.started_at)
        completed_timestamp = self._make_datetime_aware(models.analysis.started_at)
        
        return self.factory.reconstitute(
            id=ImageAnalysisID(models.analysis.id),
            source_img_id=ImageArtifactID(models.analysis.source_image_id),
            preprocessed_img_id=(
                ImageArtifactID(models.analysis.preprocessed_image_id)
                if models.analysis.preprocessed_image_id
                else None
            ),
            status=AnalysisStatus(StatusEnum(models.analysis.status)),
            created_at=created_timestamp ,
            started_at=started_timestamp,
            completed_at=completed_timestamp,
            error=error,
            clothing_items=clothing_items,
            steps=processing_step,
        )

    def aggregate_to_models(self, aggregate: ImageAnalysisAggregate) -> Models:
        """
        Domain → ORM
        """
        step_orms: List[ProcessingStepORM] = [
            ProcessingStepORM(
                image_aggregate_id=str(aggregate.id),
                status=str(
                    step.status.value.value
                ),  # <- Needs to check if is saving the key or the value of the enum
                timestamp=step.timestamp,
                message=step.message,
                attempt=step.attempt,
            )
            for step in aggregate.p_history.steps
        ]

        c_item_orms: List[ClothingItemORM] = [
            self._to_orm_clothing_item(item)
            for item in aggregate.clothing_items.values()
        ]

        analysis_orm = ImageAnalysisORM(
            id=str(aggregate.id),
            source_image_id=str(aggregate.source_image_id),
            preprocessed_image_id=(
                str(aggregate.preprocessed_image_id)
                if aggregate.preprocessed_image_id
                else None
            ),
            status=str(aggregate.status.value.value),
            created_at=aggregate.timestamps.created_at,
            started_at=aggregate.timestamps.started_at,
            completed_at=aggregate.timestamps.completed_at,
            error_message=(
                aggregate.error.message if aggregate.error is not None else None
            ),
            error_origin=(
                aggregate.error.origin if aggregate.error is not None else None
            ),
        )

        return Models(
            analysis=analysis_orm, clothing_items=c_item_orms, steps=step_orms
        )
