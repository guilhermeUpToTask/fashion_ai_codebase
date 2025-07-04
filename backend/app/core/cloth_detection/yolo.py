import os
from huggingface_hub import hf_hub_download
import torch
from ultralytics import YOLO
from PIL import Image

# Import all the necessary classes that the model file might need to unpickle
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules import (Conv, C2f, Bottleneck, SPPF, Concat, Detect, DFL)
from torch.nn import (Sequential, Conv2d, SiLU, BatchNorm2d, MaxPool2d,
                      AdaptiveAvgPool2d, Linear, ModuleList, Upsample)


# --- Download the model ---
local_weights_path = hf_hub_download("kesimeg/yolov8n-clothing-detection", "best.pt")


# --- Define ALL the classes that are safe to unpickle ---
# This includes standard PyTorch layers and custom Ultralytics layers.
safe_classes = [
    # Standard PyTorch Modules
    Sequential, Conv2d, SiLU, BatchNorm2d, MaxPool2d, AdaptiveAvgPool2d, Linear,

    # Custom Ultralytics Modules
    DetectionModel,
    Conv,
    C2f,
    Bottleneck,
    SPPF,
    Concat,
    Detect,
    ModuleList,
    Upsample,# <--- ADD THIS LINE
    DFL
]


# --- Load the model within the safe context ---
# This context manager tells torch.load that it's okay to unpickle the classes in our list.
with torch.serialization.safe_globals(safe_classes):
    model = YOLO(local_weights_path).to("cuda:0")

print("Model loaded successfully!")


# --- Your function remains the same ---
def extract_clothing_patches(image_path):
    """
    Recebe o caminho de uma imagem, roda o modelo e retorna lista de PIL.Images
    contendo cada região detectada como roupa.
    """
    img = Image.open(image_path).convert("RGB")
    results = model.predict(img, conf=0.3)[0]  # pega o primeiro (e único) batch/result

    patches = []
    for box in results.boxes:
        # coords em formato [x1, y1, x2, y2]
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        patch = img.crop((x1, y1, x2, y2))
        patches.append(patch)

    return patches

# Exemplo de uso

if __name__ == "__main__":
    os.makedirs("imgs", exist_ok=True)
    img_dir = "./imgs"
    crops_dir = "./cloth_crops"
    image_path = f"{img_dir}/example.jpeg"
    try:

        crops = extract_clothing_patches(image_path)
        print(f"Found {len(crops)} clothing items in '{image_path}'.")
        for i, patch in enumerate(crops):
            patch.save(f"{crops_dir}/crop_{i}.png")
        print("Saved cropped images as crop_0.png, crop_1.png, ...")
    except FileNotFoundError:
        print(f"Error: The image file '{image_path}' was not found.")
        print("Please create an 'example.jpg' file or change the path in the script.")