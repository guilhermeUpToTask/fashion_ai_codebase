from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Tuple
from src.domain.image_analysis.aggregates.image_analysis_aggregate import (
    ImageAnalysisAggregate,
)
from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.image_analysis.value_objects.clothing_item_vos import ClothingItemId
from src.domain.image_analysis.value_objects.image_analysis_vos import (
    AnalysisError,
    AnalysisStatus,
    AnalysisTimestamps,
    ImageAnalysisID,
    ProcessingHistory,
    ProcessingStep,
    StatusEnum,
)
from src.domain.image_analysis.value_objects.image_artifact_vos import ImageArtifactID

from src.domain.image_analysis.errors import CorruptedAggregateError


@dataclass(frozen=True)
class StatusRule:
    image_fields: Tuple[str, ...]
    item_fields: Tuple[str, ...]
    require_items: bool
    context_validator: Callable[[ImageAnalysisAggregate], None] | None = None


#TODO: split the status rules into its only class and file later
#TODO: validate the timestamps aswell
#TODO: validate for duplicates clothing items
#TODO: validate if the ids from clothing item match the image id
#TODO: validate having processing history for each status
class ImageAnalysisFactory:
    def create(self, img_id: ImageArtifactID) -> ImageAnalysisAggregate:
        timestamps = AnalysisTimestamps(created_at=datetime.now(timezone.utc))
        created_status = AnalysisStatus(StatusEnum.CREATED)

        return ImageAnalysisAggregate(
            id=ImageAnalysisID.next_id(),
            timestamps=timestamps,
            source_image_id=img_id,
            p_history=ProcessingHistory(steps=()),
            status=created_status,
            clothing_items={},
        )

    def _all_items_have_field(self, items: dict, field: str) -> bool:
        for item in items.values():
            if not hasattr(item, field):
                return False
            if getattr(item, field) is None:
                return False
        return True

    # TODO: split into other functions later
    def _validate_completed(self, img_analysis: ImageAnalysisAggregate):
        if img_analysis.preprocessed_image_id is None:
            raise CorruptedAggregateError(
                "Corrupted: COMPLETED state requires preprocessed_image_id."
            )

        prev_status = img_analysis.p_history.previuos_non_failed_status

        if prev_status == StatusEnum.NO_CLOTHS:
            if len(img_analysis.clothing_items) > 0:
                raise CorruptedAggregateError(
                    "Corrupted: COMPLETED from NO_CLOTHS must have zero clothing_items."
                )
            return

        if prev_status == StatusEnum.EMBEDDED:
            if len(img_analysis.clothing_items) == 0:
                raise CorruptedAggregateError(
                    "Corrupted: COMPLETED from EMBEDDED requires clothing_items."
                )
            if (
                self._all_items_have_field(img_analysis.clothing_items, "label")
                is False
            ):
                raise CorruptedAggregateError(
                    "Corrupted: COMPLETED from EMBEDDED requires all items to have label."
                )
            if (
                self._all_items_have_field(img_analysis.clothing_items, "embedding_id")
                is False
            ):
                raise CorruptedAggregateError(
                    "Corrupted: COMPLETED from EMBEDDED requires all items to have embedding_id."
                )
            if (
                self._all_items_have_field(
                    img_analysis.clothing_items, "cropped_image_id"
                )
                is False
            ):
                raise CorruptedAggregateError(
                    "Corrupted: COMPLETED from EMBEDDED requires all items to have cropped_image_id."
                )
            return

        raise CorruptedAggregateError(
            f"Corrupted: COMPLETED inconsistent with previous non-failed status {prev_status}"
        )

    def _verify_fields_for_status(self, img_analysis: ImageAnalysisAggregate):
        status = img_analysis.status.value

        STATUS_RULES: Dict[StatusEnum, StatusRule] = {
            StatusEnum.CREATED: StatusRule((), (), False),
            StatusEnum.STARTED: StatusRule((), (), False),
            StatusEnum.PREPROCESSED: StatusRule(("preprocessed_image_id",), (), False),
            StatusEnum.DETECTING: StatusRule(("preprocessed_image_id",), (), False),
            StatusEnum.DETECTED: StatusRule(("preprocessed_image_id",), (), True),
            StatusEnum.DESCRIBING: StatusRule(("preprocessed_image_id",), (), True),
            StatusEnum.DESCRIBED: StatusRule(
                ("preprocessed_image_id",), ("label",), True
            ),
            StatusEnum.EMBEDDING: StatusRule(
                ("preprocessed_image_id",), ("label",), True
            ),
            StatusEnum.EMBEDDED: StatusRule(
                ("preprocessed_image_id",), ("label", "embedding_id"), True
            ),
            StatusEnum.NO_CLOTHS: StatusRule(("preprocessed_image_id",), (), False),
            StatusEnum.COMPLETED: StatusRule((), (), False, self._validate_completed),
            StatusEnum.FAILED: StatusRule((), (), False),
            StatusEnum.CANCELLED: StatusRule((), (), False),
        }

        rules = STATUS_RULES[status]

        for field in rules.image_fields:
            if getattr(img_analysis, field) is None:
                raise CorruptedAggregateError(
                    f"Image Analysis missing {field} in status {status}"
                )
        if rules.require_items and len(img_analysis.clothing_items) == 0:
            raise CorruptedAggregateError(
                f"Image Analysis missing clothing items in status {status}"
            )
        for field in rules.item_fields:
            if not self._all_items_have_field(img_analysis.clothing_items, field):
                raise CorruptedAggregateError(
                    f"Image Analysis clothing items missing {field} in status {status}"
                )
        if rules.context_validator:
            rules.context_validator(img_analysis)

    def reconstitute(
        self,
        id: ImageAnalysisID,
        created_at: datetime,
        started_at: datetime | None,
        completed_at: datetime | None,
        source_img_id: ImageArtifactID,
        preprocessed_img_id: ImageArtifactID,
        clothing_items: List[ClothingItem],
        status: AnalysisStatus,
        steps: List[ProcessingStep],
        error: AnalysisError | None,
    ) -> ImageAnalysisAggregate:

        timestamps = AnalysisTimestamps(created_at, started_at, completed_at)
        items_dict = {item.id: item for item in clothing_items}
        processing_history = ProcessingHistory(steps=tuple(steps))

        img_aggregate = ImageAnalysisAggregate(
            id=id,
            timestamps=timestamps,
            source_image_id=source_img_id,
            preprocessed_image_id=preprocessed_img_id,
            clothing_items=items_dict,
            p_history=processing_history,
            status=status,
            error=error,
        )
        self._verify_fields_for_status(img_aggregate)
        return img_aggregate
