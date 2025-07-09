#ingest all the cropped cloth crops imgs and save into a temp vector with metadatas using labelling imgs, and then normalazing all of it

from typing import TypedDict
from PIL import Image
import torch
from core.embedding import img_to_vector, label_for_img 
from transformers import CLIPProcessor, CLIPModel
import torch.nn.functional as F
FASHION_MODEL = "patrickjohncyh/fashion-clip"

#later we wiil see if there is any difference between typed dict and namedTurple(immutable)
class ImageInfo(TypedDict):
    label: str
    label_vector: torch.Tensor
    img_vector: torch.Tensor

def get_img_from_path(img_path: str) -> Image.Image:
    return Image.open(img_path).convert("RGB")

def init_model(model_name:str) -> CLIPModel:
    return CLIPModel.from_pretrained(model_name)

def init_processor(model_name:str) -> CLIPProcessor:
    processor = CLIPProcessor.from_pretrained(model_name)
    # If the above line returns a tuple, unpack it:
    if isinstance(processor, tuple):
        processor = processor[0]
    return processor


def ingest(img_path:str) ->ImageInfo:
    model = init_model(FASHION_MODEL)
    processor = init_processor(FASHION_MODEL)
    
    img = get_img_from_path(img_path=img_path)
    img_vector = img_to_vector.embed(img=img, model=model, processor=processor)
    label_data = label_for_img.get_label_for_img(img_vector=img_vector, model=model, processor=processor)
    
    return {"img_vector": img_vector, "label": label_data.best_label, "label_vector": label_data.best_vector}