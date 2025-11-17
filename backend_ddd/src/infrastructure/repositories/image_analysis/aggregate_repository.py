from datetime import datetime, timezone
from typing import List, cast
from sqlalchemy import ColumnElement
from sqlmodel import Session, delete, select


from src.domain.shared.specifications import Specification
from src.domain.image_analysis.value_objects.image_analysis_vos import ImageAnalysisID
from src.domain.image_analysis.aggregates.image_analysis_aggregate import (
    ImageAnalysisAggregate,
)
from src.infrastructure.repositories.image_analysis.aggregate_data_mapper import (
    ImageAnalysisMapper,
    Models,
)
from src.infrastructure.repositories.image_analysis.orms import (
    ImageAnalysisORM,
    ClothingItemORM,
    ProcessingStepORM,
)
from src.infrastructure.db.specification_visitor import SQLModelSpecificationVisitor


class SQLModelImageAnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.mapper = ImageAnalysisMapper()
        self.visitor = SQLModelSpecificationVisitor(
            field_map={
                "status": ImageAnalysisORM.status,
                "created_at": ImageAnalysisORM.created_at,
                "started_at": ImageAnalysisORM.started_at,
                "completed_at": ImageAnalysisORM.completed_at,
                "source_image_id": ImageAnalysisORM.source_image_id,
            }
        )

    def add(self, aggregate: ImageAnalysisAggregate) -> None:
        models = self.mapper.aggregate_to_models(aggregate)

        self.session.add(models.analysis)

        for item in models.clothing_items:
            self.session.add(item)
        for step in models.steps:
            self.session.add(step)

    # TODO: here we are making 3 queries in db lets se if later we can make one just by joining
    def get_by_id(self, aggregate_id: ImageAnalysisID) -> ImageAnalysisAggregate | None:
        analysis_orm = self.session.get(ImageAnalysisORM, str(aggregate_id))
        if not analysis_orm:
            return None

        clothing_items = self.session.exec(
            select(ClothingItemORM).where(
                ClothingItemORM.image_aggregate_id == str(aggregate_id)
            )
        ).all()

        steps = self.session.exec(
            select(ProcessingStepORM)
            .where(ProcessingStepORM.image_aggregate_id == str(aggregate_id))
            .order_by(cast(ColumnElement, ProcessingStepORM.timestamp))
        ).all()

        # TODO: evaluate to work with sequence in the mapper to not need the conversion to list, as list will be converse to dict anyways
        models = Models(
            analysis=analysis_orm,
            clothing_items=list(clothing_items),
            steps=list(steps),
        )
        return self.mapper.models_to_aggregate(models)

    # TODO: put pagination logic here later
    def list_all(self) -> List[ImageAnalysisAggregate]:
        analysis_orms = self.session.exec(select(ImageAnalysisORM)).all()

        aggregates = []

        for analysis in analysis_orms:
            clothing_items = self.session.exec(
                select(ClothingItemORM).where(
                    ClothingItemORM.image_aggregate_id == analysis.id
                )
            ).all()

            steps = self.session.exec(
                select(ProcessingStepORM).where(
                    ProcessingStepORM.image_aggregate_id == analysis.id
                )
            ).all()

            models = Models(
                analysis=analysis,
                clothing_items=list(clothing_items),
                steps=list(steps),
            )
            aggregates.append(self.mapper.models_to_aggregate(models))

        return aggregates

    def find_by_specification(
        self, spec: Specification | None
    ) -> list[ImageAnalysisAggregate]:
        stmt = select(ImageAnalysisORM)

        if spec:
            predicate = spec.accept(self.visitor)
            stmt = stmt.where(predicate)

        analysis_orms = self.session.exec(stmt).all()

        aggregates = []
        for analysis_orm in analysis_orms:
            clothing_items = self.session.exec(
                select(ClothingItemORM).where(
                    ClothingItemORM.image_aggregate_id == analysis_orm.id
                )
            ).all()

            steps = self.session.exec(
                select(ProcessingStepORM)
                .where(ProcessingStepORM.image_aggregate_id == analysis_orm.id)
                .order_by(cast(ColumnElement, ProcessingStepORM.timestamp))
            ).all()

            models = Models(
                analysis=analysis_orm,
                clothing_items=list(clothing_items),
                steps=list(steps),
            )
            aggregates.append(self.mapper.models_to_aggregate(models))

        return aggregates

    # TODO:Test later if sqlmodel can handle updates inside the orm and sync without getting the items first then update or delete
    def update(self, aggregate: ImageAnalysisAggregate):
        analysis_orm = self.session.get(ImageAnalysisORM, str(aggregate.id))
        if not analysis_orm:
            raise ValueError("ImageAnalysisAggregate not found")

        models = self.mapper.aggregate_to_models(aggregate)
        analysis_orm.sqlmodel_update(models.analysis)
        self.session.add(analysis_orm)

        # Processing steps
        existing_keys = {
            (self.mapper._make_datetime_aware(step.timestamp), step.status)
            for step in analysis_orm.processing_steps
        }

        for step in models.steps:
            step_key = (step.timestamp, step.status)
            if not step_key in existing_keys:
                analysis_orm.processing_steps.append(step)

        # Items
        existing_items_list = self.session.exec(
            select(ClothingItemORM).where(
                ClothingItemORM.image_aggregate_id == str(aggregate.id)
            )
        ).all()
        updated_items = models.clothing_items

        existing_items_map = {item.id: item for item in existing_items_list}
        existing_items_ids = set(existing_items_map.keys())
        aggregate_items_ids = set(item.id for item in updated_items)

        items_to_delete_ids = existing_items_ids - aggregate_items_ids
        if items_to_delete_ids:
            stmt = delete(ClothingItemORM).where(
                cast(ColumnElement, ClothingItemORM.id).in_(items_to_delete_ids)
            )
            self.session.exec(stmt)  # type: ignore
            for item_id in items_to_delete_ids:
                del existing_items_map[item_id]
            
        for item_model in updated_items:
            if item_model.id in existing_items_ids:
                existing_item = existing_items_map[item_model.id]
                existing_item.sqlmodel_update(item_model)
                self.session.add(existing_item)
            else:
                self.session.add(item_model)

    def delete(self, aggregate_id: ImageAnalysisID) -> None:
        analysis_orm = self.session.get(ImageAnalysisORM, str(aggregate_id))
        if analysis_orm:
            # Cascade delete will handle clothing_items and processing_steps
            self.session.delete(analysis_orm)

    def flush(self) -> None:
        self.session.flush()
