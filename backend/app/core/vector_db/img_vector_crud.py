import logging
from typing import List
import uuid
from chromadb import Collection
from chromadb.api import ClientAPI

from models.label import StructuredLabel

logger = logging.getLogger(__name__)


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


def delete_img_in_collection(img_id: uuid.UUID, collection: Collection) -> uuid.UUID:
    collection.delete(ids=[str(img_id)])
    return img_id
