from typing import cast
from transformers import CLIPProcessor, CLIPModel
import torch

styles = [
    "casual", "formal", "streetwear", "sporty", "vintage",
    "bohemian", "elegant", "grunge", "preppy", "chic",
    "punk", "business casual", "minimalist", "artsy", "classic","basic"
]
colors = ["red", "blue", "black", "yellow", "white"]
patterns = ["striped", "floral", "plaid", "solid"]
categories = ["shirt","polo shirt", "dress", "pants", "sweater", "polo sweater", "blouse"]

fashion_labels = [f"{style} {pattern} {color} {cat}" for style in styles for pattern in patterns for color in colors for cat in categories]


# we can added the labeled texts into a vecto db later
def embed_labels(labels:list[str], model: CLIPModel, processor: CLIPProcessor) -> torch.Tensor:
    
    text_inputs = processor(text=labels, return_tensors="pt", padding=True, truncation=True, max_length=77)
    input_ids = cast(torch.Tensor, text_inputs["input_ids"])
    attention_mask = cast(torch.Tensor, text_inputs["attention_mask"])
    
    with torch.no_grad():
        text_features = model.get_text_features(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)  # normalize 
       
    return text_features

def get_label_for_img(img_vector: torch.Tensor, model: CLIPModel, processor: CLIPProcessor) -> str: 
    labels_vector = embed_labels(fashion_labels, model=model, processor=processor)
    similarities = torch.matmul(img_vector, labels_vector.T) 
    best_idx = int(similarities.argmax(dim=1).item())
    return  fashion_labels[best_idx]