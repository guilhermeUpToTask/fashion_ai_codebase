from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Set, Tuple, TypeVar
from src.domain.image_analysis.entities.clothing_item import ClothingItem
from src.domain.shared.entities import Entity
from src.domain.shared.value_objects import GenericUUID
from src.domain.image_analysis.errors import CorruptedAggregateError
from src.domain.image_analysis.value_objects.image_analysis_vos import (
    ImageAnalysisID,
    StatusEnum,
)
from src.domain.image_analysis.aggregates.image_analysis_aggregate import (
    ImageAnalysisAggregate,
)


@dataclass(frozen=True)
class StatusRule:
    require_items: bool = False
    require_error: bool = False
    image_fields: Tuple[str, ...] = ()
    item_fields: Tuple[str, ...] = ()
    timestamp_fields: Tuple[str, ...] = ()
    context_validator: Callable[[ImageAnalysisAggregate], None] | None = None


class ImageAnalysisRules:
    STATUS_RULES: Dict[StatusEnum, StatusRule]

    def __init__(self):
        self.STATUS_RULES = {
            StatusEnum.CREATED: StatusRule(timestamp_fields=("created_at",)),
            StatusEnum.STARTED: StatusRule(
                timestamp_fields=("created_at", "started_at")
            ),
            StatusEnum.PREPROCESSED: StatusRule(
                image_fields=("preprocessed_image_id",),
                timestamp_fields=("created_at", "started_at"),
            ),
            StatusEnum.DETECTING: StatusRule(
                image_fields=("preprocessed_image_id",),
                timestamp_fields=("created_at", "started_at"),
            ),
            StatusEnum.DETECTED: StatusRule(
                image_fields=("preprocessed_image_id",),
                timestamp_fields=("created_at", "started_at"),
                require_items=True,
            ),
            StatusEnum.DESCRIBING: StatusRule(
                image_fields=("preprocessed_image_id",),
                timestamp_fields=("created_at", "started_at"),
                require_items=True,
            ),
            StatusEnum.DESCRIBED: StatusRule(
                image_fields=("preprocessed_image_id",),
                timestamp_fields=("created_at", "started_at"),
                item_fields=("label",),
                require_items=True,
            ),
            StatusEnum.EMBEDDING: StatusRule(
                image_fields=("preprocessed_image_id",),
                timestamp_fields=("created_at", "started_at"),
                item_fields=("label",),
                require_items=True,
            ),
            StatusEnum.EMBEDDED: StatusRule(
                image_fields=("preprocessed_image_id",),
                timestamp_fields=("created_at", "started_at"),
                item_fields=("label", "embedding_id"),
                require_items=True,
            ),
            StatusEnum.NO_CLOTHS: StatusRule(
                image_fields=("preprocessed_image_id",),
                timestamp_fields=("created_at", "started_at"),
            ),
            StatusEnum.COMPLETED: StatusRule(
                timestamp_fields=("created_at", "started_at", "completed_at"),
                context_validator=self.validate_completed,
            ),
            StatusEnum.FAILED: StatusRule(require_error=True),
            StatusEnum.CANCELLED: StatusRule(),
        }

    K = TypeVar("K", bound=GenericUUID)
    E = TypeVar("E", bound=Entity)

    def all_items_have_field(self, items: Mapping[K, E], field: str) -> bool:
        for item in items.values():
            if not hasattr(item, field):
                return False
            if getattr(item, field) is None:
                return False
        return True

    def validate_completed(self, img_analysis: ImageAnalysisAggregate):
        if img_analysis.preprocessed_image_id is None:
            raise CorruptedAggregateError(
                "Corrupted: COMPLETED state requires preprocessed_image_id."
            )

        prev_status = img_analysis.p_history.previuos_non_failed_status

        if prev_status == StatusEnum.NO_CLOTHS:
            self.validate_complete_no_cloths(img_analysis)
            return
        if prev_status == StatusEnum.EMBEDDED:
            self.validate_complete_embeddings(img_analysis)
            return

        raise CorruptedAggregateError(
            f"Corrupted: COMPLETED inconsistent with previous non-failed status {prev_status}"
        )

    def validate_complete_no_cloths(self, img_analysis: ImageAnalysisAggregate):
        if len(img_analysis.clothing_items) > 0:
            raise CorruptedAggregateError(
                "Corrupted: COMPLETED from NO_CLOTHS must have zero clothing_items."
            )

    def validate_complete_embeddings(self, img_analysis: ImageAnalysisAggregate):
        if len(img_analysis.clothing_items) == 0:
            raise CorruptedAggregateError(
                "Corrupted: COMPLETED from EMBEDDED requires clothing_items."
            )
        if self.all_items_have_field(img_analysis.clothing_items, "label") is False:
            raise CorruptedAggregateError(
                "Corrupted: COMPLETED from EMBEDDED requires all items to have label."
            )
        if (
            self.all_items_have_field(img_analysis.clothing_items, "embedding_id")
            is False
        ):
            raise CorruptedAggregateError(
                "Corrupted: COMPLETED from EMBEDDED requires all items to have embedding_id."
            )
        if (
            self.all_items_have_field(img_analysis.clothing_items, "cropped_image_id")
            is False
        ):
            raise CorruptedAggregateError(
                "Corrupted: COMPLETED from EMBEDDED requires all items to have cropped_image_id."
            )

    def validate_fields_for_status(self, img_analysis: ImageAnalysisAggregate):
        status = img_analysis.status.value

        status_rules = self.STATUS_RULES[status]

        for field in status_rules.image_fields:
            if getattr(img_analysis, field) is None:
                raise CorruptedAggregateError(
                    f"Image Analysis missing {field} in status {status}"
                )

        for field in status_rules.timestamp_fields:
            if getattr(img_analysis.timestamps, field) is None:
                raise CorruptedAggregateError(
                    f"Image Analysis timestamp missing {field} in status {status}"
                )

        if status_rules.require_items and len(img_analysis.clothing_items) == 0:
            raise CorruptedAggregateError(
                f"Image Analysis missing clothing items in status {status}"
            )
        for field in status_rules.item_fields:
            if not self.all_items_have_field(img_analysis.clothing_items, field):
                raise CorruptedAggregateError(
                    f"Image Analysis clothing items missing {field} in status {status}"
                )

        if status_rules.context_validator:
            status_rules.context_validator(img_analysis)

        if status_rules.require_error and img_analysis.error is None:
            raise CorruptedAggregateError(
                f"Image Analysis missing error in status {status}"
            )
