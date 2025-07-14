
import torch
from huggingface_hub import hf_hub_download
from ultralytics import YOLO
from transformers import CLIPProcessor, CLIPModel
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules import (Conv, C2f, Bottleneck, SPPF, Concat, Detect, DFL)
from torch.nn import (Sequential, Conv2d, SiLU, BatchNorm2d, MaxPool2d,
                      AdaptiveAvgPool2d, Linear, ModuleList, Upsample)

# --- Best Practice: Define the device once ---
# This will automatically use the GPU if available, otherwise fall back to CPU.
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"--- ML Service: Models will be loaded on device: {device} ---")

# --- Load YOLO Model (requires safe_globals) ---
local_yolo_path = hf_hub_download("kesimeg/yolov8n-clothing-detection", "best.pt")
FASHION_MODEL_NAME = "patrickjohncyh/fashion-clip"

# --- Define ALL the classes that are safe to unpickle ---
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
    Upsample,
    DFL
]

# Load YOLO model with safe_globals context
with torch.serialization.safe_globals(safe_classes):
    yolo_model = YOLO(local_yolo_path).to(device)
    print(f"YOLO model to ${device} succeeded")

# --- Load CLIP Model (does NOT require safe_globals) ---
try:
    clip_model = CLIPModel.from_pretrained(FASHION_MODEL_NAME).to(device) # type: ignore
    print(f"CLIP model  to ${device} succeeded")
    clip_processor = CLIPProcessor.from_pretrained(FASHION_MODEL_NAME)
    if isinstance(clip_processor, tuple):
        clip_processor = clip_processor[0]
    print("CLIP model and processor loaded successfully")
except Exception as e:
    print(f"Error loading CLIP model: {e}")
    raise