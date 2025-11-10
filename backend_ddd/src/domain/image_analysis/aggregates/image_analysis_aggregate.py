from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from src.domain.image_analysis.errors import (
    InvalidTransitionException,
    MissingItemException,
    InvariantViolationException,
)

from src.domain.image_analysis.value_objects.clothing_item_value_objects import (
    ClothingItemId,
    Label,
)
from src.domain.image_analysis.value_objects.embedding_value_objects import (
    EmbeddingId,
)
from src.domain.shared.aggregates import Aggregate
from src.domain.image_analysis.value_objects.image_artifact_value_objects import (
    ImageArtifactID,
)
from src.domain.image_analysis.entities.clothing_item import (
    ClothingItem,
)
from src.domain.image_analysis.value_objects.image_analysis_value_objects import (
    AnalysisStatus,
    ClothingItemsMap,
    ImageAnalysisID,
    AnalysisStatusEnum,
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
    clothing_items: ClothingItemsMap

    source_image_id: ImageArtifactID
    preprocessed_image_id: ImageArtifactID | None

    error: AnalysisError | None

    # query helpers
    def last_processing_step(self) -> ProcessingStep | None:
        return self.p_history.last_step

    def retries_for(self, status_enum: AnalysisStatusEnum) -> int:
        return self.p_history.retries_for_status(AnalysisStatus(status_enum))

    # item helpers
    def add_clothing_item(self, item: ClothingItem) -> None:
        self.clothing_items.add(item)

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

    # internal helpers
    def _add_step(
        self, status_enum: AnalysisStatusEnum, message: str | None = None
    ) -> None:

        attempt = self.retries_for(status_enum) + 1

        step = ProcessingStep(
            status=AnalysisStatus(status_enum),
            timestamp=datetime.now(timezone.utc),
            attempt=attempt,
            message=message,
        )
        self.p_history.add_step(step)

    # TODO: evaluate the neeed to add a timestamp for status updates

    def _mark_transition(
        self, expected_status: AnalysisStatusEnum, new_status: AnalysisStatusEnum
    ):
        if self.status.value != expected_status:
            raise InvalidTransitionException(
                f"Current status did not match the expected status for this transition. current:{self.status}, expected:{expected_status}"
            )
        self.status = AnalysisStatus(new_status)

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
        for item in self.clothing_items:
            if item.label is None:
                missing_property = True
            if item.cropped_image_id is None:
                missing_property = True
            if item.embedding_id is None:
                missing_property = True
        if missing_property:
            raise MissingItemException(
                f"Some items is missing critical propertys! {self.clothing_items}"
            )

    # lifecycle transitions
    def start(self) -> None:
        self._check_cloth_items(False)

        if len(self.p_history) > 0:
            raise InvariantViolationException(
                f"should not have any processing history:{len(self.p_history)} "
            )
        if self.source_image_id is None:
            raise MissingItemException(f"Source image is missing, cannot start...")

        self.timestamps = AnalysisTimestamps.mark_started(self.timestamps)
        self._add_step(AnalysisStatusEnum.STARTED)

    def start_preprocessing(self, message: str | None = None) -> None:
        self._check_cloth_items(False)

        self._mark_transition(
            AnalysisStatusEnum.STARTED,
            AnalysisStatusEnum.PREPROCESSING,
        )
        self._add_step(AnalysisStatusEnum.PREPROCESSING, message)

    def finish_preprocessing(
        self, preprocessed_image_id: ImageArtifactID, message: str | None = None
    ) -> None:
        self._check_cloth_items(False)

        self.preprocessed_image_id = preprocessed_image_id

        self._mark_transition(
            AnalysisStatusEnum.PREPROCESSING,
            AnalysisStatusEnum.PREPROCESSED,
        )
        self._add_step(AnalysisStatusEnum.PREPROCESSED, message)

    def start_detection(self, message: str | None = None) -> None:
        self._check_cloth_items(False)

        self._mark_transition(
            AnalysisStatusEnum.PREPROCESSED, AnalysisStatusEnum.DETECTING
        )
        self._add_step(AnalysisStatusEnum.DETECTING, message)

    # TODO: we need to think on how we will deal with cropped imgs and bboxs
    def finish_detection(
        self, detected_items: List[ClothingItem], message: str | None = None
    ) -> None:
        self._check_cloth_items(False)

        if self.preprocessed_image_id is None:
            raise MissingItemException("pre processed image is missing.")

        if len(detected_items) == 0:
            self._mark_transition(
                AnalysisStatusEnum.DETECTING, AnalysisStatusEnum.NO_CLOTHS
            )
            new_msg = (message + " - " if message else "") + "No Clothing items..."
            self._add_step(AnalysisStatusEnum.NO_CLOTHS, new_msg)
            return

        for item in detected_items:
            self.add_clothing_item(item)

        self._mark_transition(AnalysisStatusEnum.DETECTING, AnalysisStatusEnum.DETECTED)
        self._add_step(AnalysisStatusEnum.DETECTED, message)

    def start_describing(self, message: str | None = None) -> None:
        if self.status.value == AnalysisStatusEnum.NO_CLOTHS:
            return
        self._check_cloth_items(True)

        self._mark_transition(
            AnalysisStatusEnum.DETECTED, AnalysisStatusEnum.DESCRIBING
        )
        self._add_step(AnalysisStatusEnum.DESCRIBING, message)

    def finish_describing(
        self,
        cloth_labels: Dict[ClothingItemId, Label],
        message: str | None = None,
    ) -> None:
        if self.status.value == AnalysisStatusEnum.NO_CLOTHS:
            return

        if len(cloth_labels) != len(self.clothing_items):
            raise InvariantViolationException(
                f"cloth labels size is diferent than cloth items:{len(cloth_labels)}-{len(self.clothing_items)}"
            )
        self._check_cloth_items(True)

        for cloth_id in cloth_labels:
            item = self._get_item_or_fail(cloth_id)
            item.attach_label(cloth_labels[cloth_id])

        self._mark_transition(
            AnalysisStatusEnum.DESCRIBING, AnalysisStatusEnum.DESCRIBED
        )
        self._add_step(AnalysisStatusEnum.DESCRIBED, message)

    def start_embedding(self, message: str | None = None) -> None:
        if self.status.value == AnalysisStatusEnum.NO_CLOTHS:
            return
        self._check_cloth_items(True)

        self._mark_transition(
            AnalysisStatusEnum.DESCRIBED, AnalysisStatusEnum.EMBEDDING
        )
        self._add_step(AnalysisStatusEnum.EMBEDDING, message)

    def finish_embedding(
        self,
        cloth_embeddings: Dict[ClothingItemId, EmbeddingId],
        message: str | None = None,
    ) -> None:
        if self.status.value == AnalysisStatusEnum.NO_CLOTHS:
            return

        if len(cloth_embeddings) != len(self.clothing_items):
            raise InvariantViolationException(
                f"cloth embeddings size is diferent than cloth items:{len(cloth_embeddings)}-{len(self.clothing_items)}"
            )
        self._check_cloth_items(True)

        for item_id in cloth_embeddings:
            item = self._get_item_or_fail(item_id)
            if item.embedding_id is not None:
                raise InvariantViolationException(
                    f"Item {item_id} already has an embedding."
                )
            item.attach_embedding(cloth_embeddings[item_id])

        self._mark_transition(AnalysisStatusEnum.EMBEDDING, AnalysisStatusEnum.EMBEDDED)
        self._add_step(AnalysisStatusEnum.EMBEDDED, message)

    def complete(self, message: str | None = None) -> None:
        if self.status.value == AnalysisStatusEnum.NO_CLOTHS:
            self._check_cloth_items(False)
        else:
            self._check_cloth_items(True)
            self._check_clothes_missing_property()

        self._mark_transition(AnalysisStatusEnum.EMBEDDED, AnalysisStatusEnum.COMPLETED)
        self.timestamps = AnalysisTimestamps.mark_completed(self.timestamps)
        self._add_step(AnalysisStatusEnum.COMPLETED, message)

    # TODO: lets think in a strategy on dealing with theses
    def fail(self, message: str, origin: str | None) -> None:
        NotImplementedError()

    def cancel(self, message: str | None) -> None:
        NotImplementedError()
