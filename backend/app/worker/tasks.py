# update the database from the worker tasks
from io import BytesIO
from uuid import UUID
import celery
import requests
from sqlmodel import Session
from app.celery import celery_app
from backend.app.models.image import ImageDB, StatusEnum, ImageCreate
from backend.app.models.label import StructuredLabel
from core.db import engine
from core.image_crud import update_job_status, get_image_by_id, create_image
from core.config import Settings
from PIL import Image
import mimetypes
import base64
import os
import logging
import time

logger = logging.getLogger(__name__)


# Helper Functions
def send_img_request(
    *, img_path: str, service_url: str, timeout: int
) -> requests.Response:
    with open(img_path, "rb") as img_file:
        mime_type, _ = mimetypes.guess_type(img_path)
        files = {
            "file": (
                img_path,
                img_file,
                mime_type or "application/octet-stream",
            )
        }
        response = requests.post(url=service_url, files=files, timeout=timeout)
    return response


def convert_base64_to_pil_image(img_b64: str) -> Image.Image:
    # with Image.open:
    img_bytes = base64.b64decode(img_b64)
    img = Image.open(BytesIO(img_bytes))
    return img


def save_image_file(img: Image.Image, imgs_dir: str, img_filename: str) -> str:
    os.makedirs(imgs_dir, exist_ok=True)  # create if not exists
    img_path = os.path.join(imgs_dir, img_filename)
    img.save(img_path, format="PNG")
    return img_path


def generate_filename_for_img(
    img_name: str,
    job_id: UUID,
    extension: str = ".png",
) -> str:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return f"{img_name}_{job_id}_{timestamp}{extension}"

def parse_and_retry(response:requests.Response, task: celery.Task, expected_type=list):
    """
    Parse JSON payload from a requests.Response and retry on failure.

    Args:
        response (requests.Response): HTTP response to parse.
        task (celery.Task): Bound Celery task instance (self) for retry.
        expected_type (type): Expected Python type of the JSON payload.

    Returns:
        The parsed JSON payload if it matches expected_type.

    Raises:
        Retry exception via task.retry if parsing fails or type mismatches.
    """
    try:
        payload = response.json()
        if not isinstance(payload, expected_type):
            raise ValueError(f"Expected {expected_type.__name__} got {type(payload).__name__}")
        return payload
    except(ValueError, requests.JSONDecodeError) as err:
        logger.error("Malformed response from ML service", exc_info=True)
        #retry the taks with the original exception
        raise task.retry(exc=err)
    
#---CELERY TASKS ---
@celery_app.task(
    name="tasks.crop_image_task",
    bind=True,
    autoretry_for=(requests.RequestException),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)  # bind gets acces to 'self'
def crop_image_task(self, job_id: UUID) -> list[ImageDB]:
    """_summary_

    Args:
        job_id (UUID): the id of the main image uploaded

    Task to crop an original image
    """
    with Session(engine) as session:
        try:
            logger.info(f"Starting crop image task for job:{job_id}")
            job_img = get_image_by_id(id=job_id, session=session)
            if not job_img:
                raise ValueError("No job image was found")

            update_job_status(
                session=session,
                job_image=job_img,
                new_status=StatusEnum.CROPPING,
                details="Step 1 of 2: Decting clothing items...",
            )

            logger.info(f"Sending request to ml service for job:{job_id}")

            # sending image to cropping process - needs retry logic
            response = send_img_request(
                img_path=job_img.path,
                service_url=f"{Settings.ML_SERVICE_URL}/crop_clothes",
                timeout=20,
            )
            response.raise_for_status()

            logger.info(
                f"request succeffuly made it to service to crop cloth pieces. job:{job_id}"
            )
            logger.info(f"Starting to parse the cloth images recived. job:{job_id}")

            # parse the response
            b64_images: list[str] = parse_and_retry(response=response, task=self, expected_type=list)
            logger.info(f"{len(b64_images)} cloth pieces scanned. job:{job_id}")

            cropped_imgs: list[ImageDB] = []
            for idx, b64_str in enumerate(b64_images):
                # convert base64 to PIL Image
                img = convert_base64_to_pil_image(b64_str)
                logger.info(
                    f"[{job_id}] Converted image {idx+1}/{len(b64_images)} to PIL, size={img.size}"
                )

                # save images in the crop_imgs
                img_filename = generate_filename_for_img(
                    img_name=f"cropped_img_{idx}", job_id=job_id
                )
                img_path = save_image_file(
                    img=img,
                    imgs_dir=Settings.CROPPED_IMGS_DIR,
                    img_filename=img_filename,
                )
                logger.info(
                    f"{idx} image file saved of ${len(b64_images)}. img_path:{img_path}, job:{job_id}"
                )

                # create a imagedb for each crop
                img_in = ImageCreate(
                    path=img_path,
                    filename=img_filename,
                    status=StatusEnum.CROPPED,
                    original_id=job_img.id,
                    format=img.format,
                )
                new_img = create_image(session=session, image_in=img_in)
                cropped_imgs.append(new_img)
                logger.info(
                    f"{idx} image metadata save into db from ${len(b64_images)}. job:{job_id}"
                )

            logger.info(f"all crop images saved succefully. job:{job_id}")
            update_job_status(
                session=session,
                job_image=job_img,
                new_status=StatusEnum.CROPPED,
                details="Step 1 of 2: Cloth Items Detected and Cropped.",
            )
            logger.info("crop image task finished!")
            return cropped_imgs
        except Exception as e:
            logger.error(f"[{job_id}] Error while cropping image", exc_info=True)
            raise e


@celery_app.task(name="tasks.label_image_task", bind=True)  # bind gets acces to 'self'
def label_image_task(
    self, job_id: UUID, crop_img_id: UUID
) -> str:  # < should return the structured label and the final vector
    """_summary_

    Args:
        job_id (UUID): the id of the main image uploaded
        crop_img_id (UUID): the id of the croped image
    Task to label a cropped image of a cloth piece and gets the final vector representation.
    """


@celery_app.task(
    name="tasks.save_image_vector_task", bind=True
)  # bind gets acces to 'self'
def save_image_vector_task(
    self,
    job_id: UUID,
    crop_img_id: UUID,
    structured_label: StructuredLabel,
    store_vector: list[float],
) -> list[ImageDB]:
    """_summary_

    Args:
        job_id (UUID): the id of the main image uploaded

    Task to save the merged vector of image and its label into a vector db(chromadb) with the structured label as metadata.
    """
