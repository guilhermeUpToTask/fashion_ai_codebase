from fastapi import APIRouter, HTTPException
from models.label import BestMatching, MatchingRequestBody
from core.embedding.text_similarity import embed_and_compare
from core.transformer_models import clip_model, clip_processor

router = APIRouter(prefix="/inference/text", tags=["text_inference"])


@router.post("/matching")
async def match_texts(
    body: MatchingRequestBody,
) -> BestMatching:
    if not body.candidates:
        raise HTTPException(status_code=400, detail="Candidates list cannot be empty.")
    if not body.target.strip():
        raise HTTPException(status_code=400, detail="Target text cannot be empty.")

    result = embed_and_compare(
        text_list=body.candidates,
        comparing_text=body.target,
        model=clip_model,
        processor=clip_processor,
    )
    return result
