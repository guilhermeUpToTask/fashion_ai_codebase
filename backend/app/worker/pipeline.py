# In backend/app/worker/pipeline.py

from typing import cast
from uuid import UUID
from celery import Task, chain

# --- Import the app instance ---
from celery_app import app as celery_app

# --- Remove direct task imports if they cause circular issues ---
# from worker.tasks import crop_image_task, split_for_indexing_task
import logging
from worker.tasks import crop_image_task

logger = logging.getLogger(__name__)


def test_task(img_id: UUID):
    logger.warning("testings if the task will be executed")

    res = crop_image_task.delay(img_id)  # type: ignore
    logger.warning(f"Task ID: {res.id}")
    return res


def start_indexing_pipeline(img_id: UUID) -> str | None:
    """Kicks off the indexing workflow."""
    logger.info("Starting Indexing papipeline")
    # Create the workflow using task names (strings) which is safer
    workflow = chain(
        celery_app.signature("tasks.crop_image_task", kwargs={"job_id": str(img_id)}),
        celery_app.signature(
            "tasks.split_for_indexing_task", kwargs={"job_id": str(img_id)}
        ),
    )

    async_result = workflow.apply_async()
    if async_result and async_result.id:
        logger.info(
            f"Started indexing pipeline for job {img_id} with task ID {async_result.id}"
        )
        return async_result.id
    else:
        logger.error(
            f"Failed to start indexing pipeline for job {img_id}. Task was not enqueued."
        )
        return None


def start_querying_pipeline(img_id: UUID) -> str | None:
    """Kicks off the querying workflow"""
    # we need to do almost same process as starting indexing pipeline. crop the image, label it, but instead of saving, we will use the result to query similars.
    # save into the query sql_model in the end.
    logger.info("Starting the querying pipeline")
    workflow = chain(
        celery_app.signature("tasks.crop_image_task", kwargs={"job_id": str(img_id)}),
        celery_app.signature(
            "tasks.split_for_querying_task", kwargs={"job_id": str(img_id)}
        ),
    )
    
    async_result = workflow.apply_async()
    if async_result and async_result.id:
        logger.info(
            f"Started querying pipeline for job {img_id} with task ID {async_result.id}"
        )
        return async_result.id
    else:
        logger.error(
            f"Failed to start querying pipeline for job {img_id}. Task was not enqueued."
        )
        return None

