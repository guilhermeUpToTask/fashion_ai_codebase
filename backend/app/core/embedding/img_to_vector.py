from typing import cast
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

#from here we get the img vector and the initialized model, 

#Device handling:
#If you want to support GPU inference, consider moving tensors and model to the same device:
#Type hint for processor:
#If you’re embedding images only, using CLIPImageProcessor might be clearer than CLIPProcessor (which handles both text and image).
#Add error handling (optional):
#You might want to add a check in case pixel_values is missing, or the input is invalid.


def embed(img: Image.Image, model: CLIPModel, processor: CLIPProcessor) -> torch.Tensor:

    inputs = processor(images=img, return_tensors="pt")
    pixel_values = cast(torch.FloatTensor, inputs["pixel_values"]) # Key might be missing	Use inputs.get() with a default
    
    with torch.no_grad():
        outputs = model.get_image_features(pixel_values=pixel_values)  # shape: [1, 512]
        image_embedding = outputs / outputs.norm(p=2, dim=-1, keepdim=True)  # L2 normalize (optional for similarity search)
    
    return image_embedding

def embed_multiples_imgs():
    return 