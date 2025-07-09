#here we will do the operations dealing with chroma db


# function for add product data, ideal for the next phase of the project
import uuid
from chromadb import Collection
from chromadb.api import ClientAPI
import torch
from models.image import ImageDB
import torch.nn.functional as F

#should be in a utils function
def merge_two_vectors(vector1:torch.Tensor, vector2:torch.Tensor) -> torch.Tensor:
    
    # Average and normalize again
    merged = (vector1 + vector2) / 2
    merged = F.normalize(merged, p=2, dim=-1)    
    return merged

#for now we will use a image data, the same that is used for querying and retrival
def add_image_data(img_id: uuid.UUID, img_vector: torch.Tensor, label_vector: torch.Tensor, session: ClientAPI) : 
    collection = session.get_or_create_collection(name="imgs_colletion")
    merged_vector = merge_two_vectors(vector1=img_vector, vector2=label_vector)
    collection.add(
        ids=str(img_id),
        embeddings=merged_vector.tolist()
        # metadatas= using single label, or separete categories like color, style, and type
    )
    return img_id

def add_list_img_data():
    pass


def get_image_data(img_id: uuid.UUID, collection: Collection): 
    result = collection.get(ids=[str(img_id)], include=["embeddings"])
    return result
