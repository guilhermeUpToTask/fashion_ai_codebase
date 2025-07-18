from typing import cast
from uuid import UUID
from celery import Task, chain, group, chord
from sqlmodel import Session
from worker.tasks import crop_image_task, split_for_indexing_task
from core.db import engine
from core.image_crud import update_job_status, get_image_by_id
from models.image import StatusEnum
from app.celery import celery_app
import logging

logger = logging.getLogger(__name__)


def start_indexing_pipeline(img_id: UUID) -> str | None:
    """Kicks off the indexing workflow."""
    # Chain: Crop -> Slipt (which handles the rest fan in fan out processes)
    crop_image = cast(Task, crop_image_task)
    split_for_indexing = cast(Task, split_for_indexing_task)
    workflow = chain(crop_image.s(job_id=img_id), split_for_indexing.s(job_id=img_id))
    
    async_result = workflow.apply_async()
    if async_result is not None:
        logger.info(f"Started indexing pipeline for job {img_id} with task ID {async_result.id}")
        return async_result.id
    else:
        logger.warning(f"Started indexing pipeline for job {img_id}, but async_result or its id is None")
        return None

def start_querying_pipeline(img_id: UUID) -> str:
    return ""
