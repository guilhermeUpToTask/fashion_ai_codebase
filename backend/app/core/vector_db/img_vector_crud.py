# here we will do the operations dealing with chroma db


# function for add product data, ideal for the next phase of the project
import logging
from typing import List
import uuid
from chromadb import Collection
from chromadb.api import ClientAPI
from sqlmodel import Session

# import torch
from backend.app.models.query import QuerySimilarProduct
from models.label import StructuredLabel

logger = logging.getLogger(__name__)


# for now we will use a image data, the same that is used for querying and retrival
def add_image_embedding(
    img_id: uuid.UUID,
    img_vector: List[float],
    img_label: StructuredLabel,
    chroma_session: ClientAPI,
    collection_name: str,
):
    collection = chroma_session.get_or_create_collection(name=collection_name)
    collection.add(
        ids=[str(img_id)], embeddings=[img_vector], metadatas=[img_label.model_dump()]
    )
    logger.info("→ after collection.add")
    return img_id


def get_image_data(img_id: uuid.UUID, chroma_session: ClientAPI, collection_name: str):
    collection = chroma_session.get_or_create_collection(collection_name)
    result = collection.get(ids=[str(img_id)], include=["embeddings"])
    return result


def get_images_ids(collection: Collection) -> list[uuid.UUID]:
    result = collection.get()
    ids_list = result.get("ids", [[]])  # This is simpler and usually correct
    print("ids_list:", ids_list)
    return [uuid.UUID(id_str) for id_str in ids_list]


# #needs to change it to only recive the vectors as list, we will not have the pytorch or any of those deps in the main service
# def get_similar_imgs_for_vector(
#     vector: torch.Tensor, collection: Collection, top_k: int
# ) -> uuid.UUID | None:
#     # Wrap vector in a list to make it a batch of one vector

#     result_query = collection.query(query_embeddings=[vector.tolist()], n_results=top_k)

#     # ids is a list of lists: one list per query (here only one query)
#     ids = result_query.get("ids", [[]])[0]  # get the first query's result list

#     if not ids:  # safer check to avoid IndexError
#         return None


#     return uuid.UUID(ids[0])
def query_similar_imgs(
    query_vector: List[float],
    n_results: int,
    chroma_session: ClientAPI,
    collection_name: str,
) -> List[QuerySimilarProduct]:
    """
    Query the given ChromaDB collection for the top‑n most similar items
    to the provided embedding vector, and return their IDs as UUID objects.

    Args:
        query_vector:   A dense embedding (list of floats) to search for.
        n_results:      Number of closest matches to return.
        chroma_session: An active ChromaDB client/session.
        collection_name:Name of the collection to query.

    Returns:
        A list of UUIDs corresponding to the top‑n matches.
    """

    collection = chroma_session.get_collection(collection_name)
    result = collection.query(query_embeddings=[query_vector], n_results=n_results)
    ids = result["ids"][0]
    if not result["distances"]:
        raise ValueError("No distances Found in the query result for similar images")
    distances = result["distances"][0]
    # We can check later for bad UUID conversion check
    similar_products = [
        QuerySimilarProduct(
            product_id=uuid.UUID(ids[i]),
            score=(1 - distances[i]),
            rank=i+1
        )
        for i in range(len(ids))
    ]
    return similar_products


# # For batch vectors list, we will query all at same query function
# def get_similar_imgs_for_vector_list(
#     crop_vectors: list[torch.Tensor], collection, top_k=3
# ):
#     # Normalize and convert to list[float]
#     normalized = [
#         torch.nn.functional.normalize(v, p=2, dim=-1).tolist() for v in crop_vectors
#     ]

#     results = collection.query(query_embeddings=normalized, n_results=top_k)

#     return results


def delete_img_in_collection(img_id: uuid.UUID, collection: Collection) -> uuid.UUID:
    collection.delete(ids=[str(img_id)])
    return img_id
