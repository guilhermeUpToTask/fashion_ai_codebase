# here we will process images, for now we will utilizes image bytes, but for cloud we can try emulate a s3 storage later
# all api infereces relationed with imgs are pointed to here


# here we will crop the main image into small croped imgs, creating few images crop in the db,
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
from fastapi.responses import HTMLResponse
import torch
from core.cloth_detection.yolo import crop_img
from core.embedding import img_to_vector, text_to_vector
from core.labelling import clip_labeling
from core.transformer_models import yolo_model, clip_model, clip_processor
from utils.images import pil_img_to_bytes, encode_image_base64
from utils.vectors import merge_two_vectors
from models.label import LabelingResponse

router = APIRouter(prefix="/inference/image", tags=["image_inference"])


# you want to see a DRY (Don't Repeat Yourself) version with decorators or exception middleware!
@router.post("/crop_clothes")
async def crop_cloth(
    img_file: UploadFile,  # needs to do some checks ups here, but we can assume that image comming from fastapi endpoint should be secure
):
    # Process the image
    # Maybe we should resize the image preserveting its aspect ratio without distortion , to be 640x640
    try:
        img_data = await img_file.read()
        img = Image.open(BytesIO(img_data))
        cropped_imgs = crop_img(img, model=yolo_model)
        img_base64_list: List[str] = []
        for image in cropped_imgs:
            img_bytes = pil_img_to_bytes(img=image, format="PNG")
            img_b64 = encode_image_base64(
                img_bytes
            )  # use StreamingResponse later for bytes response later, after prototyping

            img_base64_list.append(img_b64)

        return img_base64_list

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image format")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail="Model error: " + str(e))


@router.post("/label")
async def labels_for_img(img_file: UploadFile):
    print("Starting to categorize image")
    img_data = await img_file.read()
    img = Image.open(BytesIO(img_data))

    img_vector = img_to_vector.embed(
        img=img, model=clip_model, processor=clip_processor
    )
    
    img_labels = clip_labeling.generate_structured_label(
        img_vector=img_vector, model=clip_model, processor=clip_processor
    )
    label_text = f"a {img_labels.color} {img_labels.pattern} {img_labels.style} {img_labels.category}"
    label_vector = text_to_vector.embed_text(
        text=label_text, model=clip_model, processor=clip_processor
    )
    
    storage_vector: list[float] = merge_two_vectors(vector1=img_vector, vector2=label_vector).squeeze(0).tolist() # get a one dimensional vector

    response = LabelingResponse(label_data=img_labels, storage_vector=storage_vector)
    return response
