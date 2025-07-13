# here we will do the operations dealing with chroma db


# function for add product data, ideal for the next phase of the project
import uuid
from chromadb import Collection
from chromadb.api import ClientAPI
import torch
from models.image import ImageDB
import torch.nn.functional as F


# should be in a utils function
def merge_two_vectors(vector1: torch.Tensor, vector2: torch.Tensor) -> torch.Tensor:

    # Average and normalize again
    merged = (vector1 + vector2) / 2
    merged = F.normalize(merged, p=2, dim=-1)
    return merged


# for now we will use a image data, the same that is used for querying and retrival
def add_image_data(
    img_id: uuid.UUID,
    img_vector: torch.Tensor,
    label_vector: torch.Tensor,
    session: ClientAPI,
):
    collection = session.get_or_create_collection(name="imgs_colletion")
    merged_vector = merge_two_vectors(vector1=img_vector, vector2=label_vector)
    collection.add(
        ids=str(img_id),
        embeddings=merged_vector.tolist(),
        # metadatas= using single label, or separete categories like color, style, and type
    )
    return img_id


def add_list_img_data():
    pass


def get_image_data(img_id: uuid.UUID, collection: Collection):
    result = collection.get(ids=[str(img_id)], include=["embeddings"])
    return result


def get_images_ids(collection: Collection) -> list[uuid.UUID]:
    result = collection.get()
    ids_list = result.get("ids", [[]])  # This is simpler and usually correct
    print("ids_list:",ids_list)
    return [uuid.UUID(id_str) for id_str in ids_list]


def get_similar_imgs_for_vector(
    vector: torch.Tensor, collection: Collection, top_k: int
) -> uuid.UUID | None:
    # Wrap vector in a list to make it a batch of one vector

    result_query = collection.query(query_embeddings=[vector.tolist()], n_results=top_k)

    # ids is a list of lists: one list per query (here only one query)
    ids = result_query.get("ids", [[]])[0]  # get the first query's result list

    if not ids:  # safer check to avoid IndexError
        return None

    return uuid.UUID(ids[0])


# For batch vectors list, we will query all at same query function
def get_similar_imgs_for_vector_list(
    crop_vectors: list[torch.Tensor], collection, top_k=3
):
    # Normalize and convert to list[float]
    normalized = [
        torch.nn.functional.normalize(v, p=2, dim=-1).tolist() for v in crop_vectors
    ]

    results = collection.query(query_embeddings=normalized, n_results=top_k)

    return results

def delete_img_in_collection(img_id: uuid.UUID, collection: Collection) -> uuid.UUID:
    collection.delete(ids=[str(img_id)])
    return img_id