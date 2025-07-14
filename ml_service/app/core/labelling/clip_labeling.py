import torch
from transformers import CLIPModel, CLIPProcessor
from core.labelling.vocab import LABEL_DICTIONARY
from core.embedding import label_to_vector
from models.label import StructuredLabel


def get_best_match_for_img(
    img_vector: torch.Tensor, labels: list[str], labels_vector: torch.Tensor
) -> str:
    similarities = torch.matmul(img_vector, labels_vector.T)
    best_idx = int(similarities.argmax(dim=1).item())
    best_label = labels[best_idx]

    return best_label


def generate_structured_label(
    img_vector: torch.Tensor, model: CLIPModel, processor: CLIPProcessor
) -> StructuredLabel:
    embedded_labels = {}

    #this result we can storage in a cache or something for not needing to embed every time the call is make it
    for label_type, label_list in LABEL_DICTIONARY.items():
        embeddings = label_to_vector.embed(
            labels=label_list, model=model, processor=processor
        )
        embedded_labels[label_type] = {"labels": label_list, "vectors": embeddings}
    
    #will comparate with all labels key(ex:category, style, color, pattern)
    best_matches = {
        key: get_best_match_for_img(
            img_vector=img_vector, labels=value["labels"], labels_vector=value["vectors"]
        )
        for key, value in embedded_labels.items()
    }
    return StructuredLabel(**best_matches)
