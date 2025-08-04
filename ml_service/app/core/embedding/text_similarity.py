from typing import List, cast
from transformers import CLIPProcessor, CLIPModel
import torch
from torch.nn.functional import cosine_similarity


from core.embedding.text_to_vector import embed_text, embed_text_list
from pydantic import BaseModel
from models.label import BestMatching

    
def embed_and_compare(text_list: List[str], comparing_text:str, model:CLIPModel, processor:CLIPProcessor) -> BestMatching:
    cadidates_embeddings = embed_text_list(text_list, model, processor)
    query_embedding = embed_text(comparing_text, model, processor)
    
    similarities = cosine_similarity(query_embedding, cadidates_embeddings)
    best_idx = torch.argmax(similarities).item()
    best_score = similarities[best_idx].item()
    best_text = text_list[best_idx]
    
    return BestMatching(text=best_text, score=best_score, index=best_idx)