from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from src.domain.image_analysis.errors import (
    InvalidTransitionException,
    MissingItemException,
    InvariantViolationException,
)

from src.domain.image_analysis.value_objects.clothing_item_vos import (
    ClothingItemId,
    Label,
)
from src.domain.shared.value_objects import (
    EmbeddingId,
)
from src.domain.shared.aggregates import Aggregate
from src.domain.shared.value_objects import (
    ImageArtifactID,
)
from src.domain.image_analysis.entities.clothing_item import (
    ClothingItem,
)
from src.domain.image_analysis.value_objects.image_analysis_vos import (
    AnalysisStatus,
    ImageAnalysisID,
    StatusEnum,
    AnalysisTimestamps,
    ProcessingHistory,
    ProcessingStep,
    AnalysisError,
)


# TODO: needs idemponcy for all methods
@dataclass(eq=False)
class ImageAnalysisAggregate(Aggregate):
    # Atributes
    id: ImageAnalysisID
    timestamps: AnalysisTimestamps
    status: AnalysisStatus
    p_history: ProcessingHistory
    clothing_items: Dict[ClothingItemId, ClothingItem]

    source_image_id: ImageArtifactID
    preprocessed_image_id: ImageArtifactID | None = None

    error: AnalysisError | None = None

    # query helpers
    def last_processing_step(self) -> ProcessingStep | None:
        return self.p_history.last_step

    def retries_for(self, status_enum: StatusEnum) -> int:
        return self.p_history.retries_for_status(AnalysisStatus(status_enum))

    def is_empty_result(self) -> bool:
        """
        Returns True if detection completed with no items found.
        Only valid after detection phase completes.
        """
        return self.status.value == StatusEnum.NO_CLOTHS

    # item helpers
    def add_clothing_item(self, item: ClothingItem):
        self.clothing_items[item.id] = item
        
    def remove_clothing_item(self, item: ClothingItem):
        self.clothing_items.pop(item.id)

    def attach_cropped_artifact_to_item(
        self, item_id: ClothingItemId, artifact_id: ImageArtifactID
    ) -> None:
        item = self.clothing_items.get(item_id)
        if item is None:
            raise MissingItemException(
                f"Could not find ClothingItem(id={item_id}) while attaching image artifact {artifact_id}. items:{self.clothing_items}"
            )

        item.attach_cropped_image(artifact_id)

    def attach_embedding_to_item(
        self, item_id: ClothingItemId, embedding_id: EmbeddingId
    ) -> None:
        item = self.clothing_items.get(item_id)
        if item is None:
            raise MissingItemException(
                f"Could not find ClothingItem(id={item_id}) while attaching embedding {embedding_id}. items:{self.clothing_items}"
            )
        item.attach_embedding(embedding_id)


    def _mark_transition_and_add_step(
        self,
        expected_status: StatusEnum | None,
        new_status: StatusEnum,
        message: str | None = None,
        timestamp: datetime | None = None,
    ):
        """Atomically transition status and add step with consistent timestamp."""
        if self.status.value == new_status:
            return
        if expected_status is not None and self.status.value not in (
            expected_status,
            StatusEnum.FAILED,
        ):
            raise InvalidTransitionException(
                f"Current status did not match expected. current:{self.status}, expected:{expected_status}"
            )

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        attempt = self.retries_for(new_status) + 1
        self.status = AnalysisStatus(new_status)

        step = ProcessingStep(
            status=self.status,
            timestamp=timestamp,
            attempt=attempt,
            message=message,
        )
        self.p_history = self.p_history.add_step(step)

    def _get_item_or_fail(self, item_id: ClothingItemId) -> ClothingItem:
        item = self.clothing_items.get(item_id)
        if not item:
            raise MissingItemException(f"Item {item_id} not found")
        return item

    def _check_cloth_items(self, expected: bool) -> None:
        """Ensure that the presence (or absence) of clothing items matches the current state."""
        has_items = len(self.clothing_items) > 0

        if expected and not has_items:
            raise InvariantViolationException(
                f"Expected clothing items to be present at status {self.status.value}, but none found."
            )

        if not expected and has_items:
            raise InvariantViolationException(
                f"Expected no clothing items at status {self.status.value}, but found some."
            )

    def _check_clothes_missing_property(self):
        missing_property = False
        for item in self.clothing_items.values():
            if item.label is None:
                missing_property = True
            if item.cropped_image_id is None:
                missing_property = True
            if item.embedding_id is None:
                missing_property = True
        if missing_property:
            raise MissingItemException(
                f"Some items are missing critical properties! {self.clothing_items}"
            )

    # lifecycle transitions
    def start(self) -> None:
        self._check_cloth_items(False)

        if len(self.p_history) > 0 and self.p_history.previuos_non_failed_status != StatusEnum.STARTED:
            raise InvariantViolationException(
                f"should not have any processing history:{self.p_history}. "
            )

        timestamp = datetime.now(timezone.utc)
        self._mark_transition_and_add_step(
            StatusEnum.CREATED, StatusEnum.STARTED, None, timestamp
        )
        self.timestamps = AnalysisTimestamps.mark_started(self.timestamps, timestamp)

    def start_preprocessing(self, message: str | None = None) -> None:
        self._mark_transition_and_add_step(
            StatusEnum.STARTED, StatusEnum.PREPROCESSING, message
        )

    def finish_preprocessing(
        self, preprocessed_image_id: ImageArtifactID, message: str | None = None
    ) -> None:
        self.preprocessed_image_id = preprocessed_image_id
        self._mark_transition_and_add_step(
            StatusEnum.PREPROCESSING, StatusEnum.PREPROCESSED, message
        )

    def start_detection(self, message: str | None = None) -> None:
        self._check_cloth_items(False)

        self._mark_transition_and_add_step(
            StatusEnum.PREPROCESSED, StatusEnum.DETECTING, message
        )

    # TODO: we need to think on how we will deal with cropped imgs and bboxs
    def finish_detection(
        self, detected_items: List[ClothingItem], message: str | None = None
    ) -> None:
        self._check_cloth_items(False)

        if self.preprocessed_image_id is None:
            raise MissingItemException("pre processed image is missing.")

        if len(detected_items) == 0:
            new_msg = (message + " - " if message else "") + "No Clothing items..."
            self._mark_transition_and_add_step(
                StatusEnum.DETECTING, StatusEnum.NO_CLOTHS, new_msg
            )
            return

        for item in detected_items:
            self.add_clothing_item(item)

        self._mark_transition_and_add_step(
            StatusEnum.DETECTING, StatusEnum.DETECTED, message
        )

    def start_describing(self, message: str | None = None) -> None:
        self._check_cloth_items(True)

        self._mark_transition_and_add_step(
            StatusEnum.DETECTED, StatusEnum.DESCRIBING, message
        )

    def finish_describing(
        self,
        cloth_labels: Dict[ClothingItemId, Label],
        message: str | None = None,
    ) -> None:

        if len(cloth_labels) != len(self.clothing_items):
            raise InvariantViolationException(
                f"cloth labels size is different than cloth items:{len(cloth_labels)}-{len(self.clothing_items)}"
            )
        self._check_cloth_items(True)

        for cloth_id in cloth_labels:
            item = self._get_item_or_fail(cloth_id)
            item.attach_label(cloth_labels[cloth_id])

        self._mark_transition_and_add_step(
            StatusEnum.DESCRIBING, StatusEnum.DESCRIBED, message
        )

    def start_embedding(self, message: str | None = None) -> None:
        self._check_cloth_items(True)

        self._mark_transition_and_add_step(
            StatusEnum.DESCRIBED, StatusEnum.EMBEDDING, message
        )

    def finish_embedding(
        self,
        cloth_embeddings: Dict[ClothingItemId, EmbeddingId],
        message: str | None = None,
    ) -> None:
        if len(cloth_embeddings) != len(self.clothing_items):
            raise InvariantViolationException(
                f"cloth embeddings size is different than cloth items:{len(cloth_embeddings)}-{len(self.clothing_items)}"
            )
        self._check_cloth_items(True)

        for item_id in cloth_embeddings:
            item = self._get_item_or_fail(item_id)
            item.attach_embedding(cloth_embeddings[item_id])

        self._mark_transition_and_add_step(
            StatusEnum.EMBEDDING, StatusEnum.EMBEDDED, message
        )

    def complete_without_items(self, message: str | None = None) -> None:
        """Complete analysis when no clothing items were detected."""
        self._check_cloth_items(False)

        timestamp = datetime.now(timezone.utc)
        self._mark_transition_and_add_step(
            StatusEnum.NO_CLOTHS,
            StatusEnum.COMPLETED,
            message,
            timestamp,
        )
        self.timestamps = AnalysisTimestamps.mark_completed(self.timestamps, timestamp)

    def complete_with_items(self, message: str | None = None) -> None:
        """Complete analysis with successfully processed clothing items."""
        self._check_cloth_items(True)
        self._check_clothes_missing_property()

        timestamp = datetime.now(timezone.utc)
        self._mark_transition_and_add_step(
            StatusEnum.EMBEDDED,
            StatusEnum.COMPLETED,
            message,
            timestamp,
        )
        self.timestamps = AnalysisTimestamps.mark_completed(self.timestamps, timestamp)

    def fail(self, message: str, origin: str | None) -> None:
        if self.status.is_terminal:
            raise InvalidTransitionException(
                f"Cannot fail terminal state {self.status.value}"
            )

        self.error = AnalysisError(message=message, origin=origin)
        self._mark_transition_and_add_step(
            expected_status=None, new_status=StatusEnum.FAILED, message=message
        )

    def cancel(self, message: str | None) -> None:
        if self.status.is_terminal:
            raise InvalidTransitionException("Cannot cancel a terminal state object")

        self._mark_transition_and_add_step(
            expected_status=None,  # pode vir de qualquer estado não terminal
            new_status=StatusEnum.CANCELLED,
            message=message,
        )
