
import base64
import glob
from io import BytesIO
import mimetypes
import os
import time
from uuid import UUID
import PIL
import requests
from PIL import Image, UnidentifiedImageError
import logging
from core import storage


logger = logging.getLogger(__name__)


# does those helpes needs to be async?

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


def get_or_generate_filename(pattern: str, job_id: UUID, idx) -> str:
    matches = glob.glob(pattern)
    if matches:
        # If you have multiple, pick the newest by file‐ctime
        latest = max(matches, key=os.path.getctime)
        img_filename = os.path.basename(latest)
    else:
        img_filename = generate_filename_for_img(
            img_name=f"cropped_img_{idx}", job_id=job_id, extension=".png"
        )
    return img_filename

# Helper Functions



def send_s3_img_to_service(
    img_filename: str, bucket_name: str, service_url: str, timeout: int = 30,
) -> requests.Response:
    """Downloads an image from S3 and send its to an service."""
    img_file = storage.download_file_from_s3(bucket_name, img_filename)
    mime_type, _ = mimetypes.guess_type(img_filename)
    files = {
        "img_file": (img_filename, img_file, mime_type or "application/octet-stream")
    }
    response = requests.post(url=service_url, files=files, timeout=timeout)
    return response


def parse_json(logger, response: requests.Response, expected_type=list):
    """
    Parse JSON payload from a requests.Response.

    Args:
        response (requests.Response): HTTP response to parse.
        task (celery.Task): Bound Celery task instance (self) for retry.
        expected_type (type): Expected Python type of the JSON payload.

    Returns:
        The parsed JSON payload if it matches expected_type.

    """
    try:
        payload = response.json()
        if not isinstance(payload, expected_type):
            raise ValueError(
                f"Expected {expected_type.__name__} got {type(payload).__name__}"
            )
        return payload
    except (ValueError, requests.JSONDecodeError) as err:
        logger.error(f"Malformed response from server , error{err}", exc_info=True)
        raise err
    

#later we can create a process image helper that will use this helper and other process like decoding
def create_and_verify_pil_img(img_bytes:BytesIO) -> Image.Image:
    try:
        img_bytes.seek(0)
        img = Image.open(img_bytes)
        img.verify()
        img_bytes.seek(0)
        #Can be converted to rgba here.
        return Image.open(img_bytes)
    except UnidentifiedImageError as e:
        logger.error("Failed to identify image: %s", e, exc_info=True)
        raise
    except OSError as e:
        logger.error("OS error while processing image: %s", e, exc_info=True)
        raise

    
    
def build_image_filename(img:Image.Image, id: UUID, idx:int | None = None, prefix:str='image') -> str:
    """
    Generate a filename for an image based on its index, format, and optional prefix.

    Args:
        idx: Index number (e.g., for enumeration).
        img: PIL Image object.
        prefix: Optional filename prefix (default: 'image').

    Returns:
        A string filename like "prefix_0.png".
    """
    ext = (img.format or "PNG").lower()
    idx_str = f"__{idx}" if idx else ""
    id_str = f"__{id}"
    return f"{prefix}{idx_str}{id_str}.{ext}"