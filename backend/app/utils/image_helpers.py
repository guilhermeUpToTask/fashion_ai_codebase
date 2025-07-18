
import base64
import glob
from io import BytesIO
import mimetypes
import os
import time
from uuid import UUID
import requests
from PIL import Image

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