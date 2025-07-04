import os
from typing import cast
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch


fashion_labels = [
        "t-shirt", "shirt", "blouse", "sweater", "hoodie", "jacket", "coat",
        "jeans", "trousers", "pants", "shorts", "skirt", "dress", "romper",
        "blue jeans", "black pants", "white t-shirt", "denim jacket",
        "graphic t-shirt", "striped shirt", "plaid shirt", "floral dress"
    ]


# we can added the labeled texts into a vecto db later
def embed_labels(labels:list[str], model: CLIPModel, processor: CLIPProcessor) -> torch.Tensor:
    
    text_inputs = processor(text=labels, return_tensors="pt", padding=True, truncation=True)
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
        
    

#from here we get the img vector and the initialized model, 

# we should add other patterns recognition, as color, and texture patterns
# lets break down here, we should first in our pipeline, embed each croped image, store in a temp vector for matching, then in other script we should label, and add metadata, then we normalize and return all the embeddings for be uisng into a matching endpoint
#  "ETL" (Extract, Transform, Load)
def label_and_rename_images():
    """
    Processes all images in a directory, classifies them using CLIP,
    and renames the files with their best-predicted label.
    """
    # --- 1. SETUP ---
    # Define the directory containing the cropped clothing images
    crops_folder = "cloth_crops"

    if not os.path.isdir(crops_folder):
        print(f"Error: The directory '{crops_folder}' was not found.")
        print("Please create it and add your cropped images.")
        return

    # Load the pre-trained Fashion-CLIP model and processor
    print("Loading Fashion-CLIP model and processor...")
    model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
    processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")
    # If the above line returns a tuple, unpack it:
    if isinstance(processor, tuple):
     processor = processor[0]    
    
    print("Model loaded successfully.")
    
    # Define the list of candidate labels for classification
    labels = [
        "t-shirt", "shirt", "blouse", "sweater", "hoodie", "jacket", "coat",
        "jeans", "trousers", "pants", "shorts", "skirt", "dress", "romper",
        "blue jeans", "black pants", "white t-shirt", "denim jacket",
        "graphic t-shirt", "striped shirt", "plaid shirt", "floral dress"
    ]

    # Find all image files in the specified folder
    image_files = [
        f for f in os.listdir(crops_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    if not image_files:
        print(f"No image files found in '{crops_folder}'.")
        return

    print(f"\nFound {len(image_files)} images to process.")

    # --- 2. PROCESSING LOOP ---
    for filename in image_files:
        original_path = os.path.join(crops_folder, filename)
        
        try:
            # Load the cropped image
            image = Image.open(original_path).convert("RGB")

            # Preprocess the image and all text labels
            # The model will compare the single image to all text labels
            inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)

            # Perform inference to get similarity scores
            with torch.no_grad(): # Use no_grad for efficiency as we are not training
                outputs = model(**inputs)
            
            logits_per_image = outputs.logits_per_image
            # --- 3. GET BEST LABEL AND RENAME ---
            # Find the index of the label with the highest score
            best_label_index = logits_per_image.argmax().item()
            
            
            best_label_text = labels[best_label_index]
            
            # Create a filename-safe version of the label (e.g., "white t-shirt" -> "white_t-shirt")
            safe_label = best_label_text.replace(' ', '_').lower()
            
            # Construct the new filename and path
            new_filename = f"{safe_label}_{filename}"
            new_path = os.path.join(crops_folder, new_filename)
            
            # Rename the file
            os.rename(original_path, new_path)
            
            print(f"Processed '{filename}': Classified as '{best_label_text}'. Renamed to '{new_filename}'.")

        except Exception as e:
            print(f"Could not process '{filename}'. Error: {e}")

# Run the main function when the script is executed
if __name__ == "__main__":
    label_and_rename_images()