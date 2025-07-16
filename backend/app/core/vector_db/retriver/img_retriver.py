

#retriver process into choma db 
from chromadb import Collection
from sqlmodel import Session
from models.image import ImageDB
from core.vector_db.img_vector_crud import get_similar_imgs_for_vector
from core.image_crud import get_image_by_id
from torch import Tensor


#we will change this to work with a list of float
def retrive_most_similar_img(img_vector: Tensor, label_vector, collection:Collection, session:Session) -> ImageDB | None:
    retriver_vector = merge_two_vectors(img_vector, label_vector)
    similar_img_id = get_similar_imgs_for_vector(vector=retriver_vector, collection=collection, top_k=1)
    if not similar_img_id:
        return None
    return get_image_by_id(id=similar_img_id, session=session)