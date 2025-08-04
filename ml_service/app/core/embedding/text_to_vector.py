from typing import cast
from transformers import CLIPProcessor, CLIPModel
import torch


# we can added the labeled texts into a vecto db later
def embed_text_list(
    texts: list[str], model: CLIPModel, processor: CLIPProcessor
) -> torch.Tensor:
    device = next(model.parameters()).device  # enforce that tensors would be in the same device as the model
    
    text_inputs = processor(
        text=texts, return_tensors="pt", padding=True, truncation=True, max_length=77
    )
    #move tensors to the same devise
    input_ids = cast(torch.Tensor, text_inputs["input_ids"]).to(device)
    attention_mask = cast(torch.Tensor, text_inputs["attention_mask"]).to(device)

    with torch.no_grad():
        text_features = model.get_text_features(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        text_features = text_features / text_features.norm(
            p=2, dim=-1, keepdim=True
        )  # normalize

    return text_features




def embed_text(text: str, model: CLIPModel, processor:CLIPProcessor) -> torch.Tensor:
    return embed_text_list([text],model, processor)[0].unsqueeze(0)