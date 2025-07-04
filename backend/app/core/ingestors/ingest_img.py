#ingest all the cropped cloth crops imgs and save into a temp vector with metadatas using labelling imgs, and then normalazing all of it

from PIL import Image
from core.embedding import img_to_vector, label_for_img
from transformers import CLIPProcessor, CLIPModel

FASHION_MODEL = "patrickjohncyh/fashion-clip"


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


def ingest(img_path:str):
    model = init_model(FASHION_MODEL)
    processor = init_processor(FASHION_MODEL)
    
    img = get_img_from_path(img_path=img_path)
    img_vector = img_to_vector.embed(img=img, model=model, processor=processor)
    
    label = label_for_img.get_label_for_img(img_vector=img_vector, model=model, processor=processor)
    
    print(f"label for img:{label} img_path:{img_path}")
    

if __name__ == "__main__":
    img_path= "./cloth_crops/blouse_crop_1.png"
    ingest(img_path)