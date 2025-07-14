
import base64
from io import BytesIO
from PIL import Image

def pil_img_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
    """
    Convert a PIL Image to bytes.

    Args:
        img (Image.Image): The PIL Image to convert.
        format (str): The image format to use (default: 'PNG').

    Returns:
        bytes: The image data in bytes.
    """
    buf = BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def encode_image_base64(img_bytes:bytes):
    """
    Encode raw image bytes to a base64-encoded string.

    Args:
        img_bytes (bytes): The raw bytes of the image to encode.

    Returns:
        str: Base64-encoded string representation of the image bytes, decoded as UTF-8.
    """
    return base64.b64encode(img_bytes).decode("utf-8")