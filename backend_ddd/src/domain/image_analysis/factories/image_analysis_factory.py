from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Set, Tuple
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
from src.domain.image_analysis.rules.analysis_aggregate_rules import ImageAnalysisRules


class ImageAnalysisFactory:
    rules: ImageAnalysisRules

    def __init__(self):
        self.rules = ImageAnalysisRules()

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

    def build_items_map(
        self, analysis_id: ImageAnalysisID, items: List[ClothingItem]
    ) -> Dict[ClothingItemId, ClothingItem]:
        items_map: dict[ClothingItemId, ClothingItem] = {}

        for item in items:
            if item.image_aggregate_id != analysis_id:
                raise CorruptedAggregateError(
                    f"Origin id mismatch!  ClothingItem id:{item.id} has image_aggregate_id {item.image_aggregate_id}, but expected {analysis_id}."
                )
            if item.id in items_map:
                raise CorruptedAggregateError(f"Duplicate item ID found: {item.id}")
            items_map[item.id] = item

        return items_map

    def reconstitute(
        self,
        id: ImageAnalysisID,
        source_img_id: ImageArtifactID,
        clothing_items: List[ClothingItem],
        status: AnalysisStatus,
        steps: List[ProcessingStep],
        created_at: datetime,
        error: AnalysisError | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None  = None,
        preprocessed_img_id: ImageArtifactID | None = None,
    ) -> ImageAnalysisAggregate:

        timestamps = AnalysisTimestamps(created_at, started_at, completed_at)
        items_dict = self.build_items_map(id, clothing_items)
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
        self.rules.validate_fields_for_status(img_aggregate)
        return img_aggregate
