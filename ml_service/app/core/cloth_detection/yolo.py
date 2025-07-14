from huggingface_hub import hf_hub_download
import torch
from ultralytics import YOLO
from PIL import Image


def extract_clothing_patches(img: Image.Image, model: YOLO) -> list[Image.Image]:
    """
    here we recive a image Pil type  from the api endpoint, the endpoint should instantice the image for simplicity
    """

    results = model.predict(img, conf=0.7)[0]  # pega o primeiro (e único) batch/result

    patches = []
    for box in results.boxes:
        # coords em formato [x1, y1, x2, y2]
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        patch = img.crop((x1, y1, x2, y2))
        patches.append(patch)

    return patches


def crop_img(img: Image.Image, model: YOLO) -> list[Image.Image]:
    """_summary_

    Args:
        img (Image.Image): The image thats will be processed and cropped by the model

    Returns:
        list[Image.Image]: The list of the cropped images
    """
    try:
        crops = extract_clothing_patches(img, model)
        if not crops:
            raise ValueError("No clothing items found in image.")
        return crops
    except Exception as e:
        # Optionally: log the error
        raise RuntimeError(f"Error in crop_img: {e}") from e
