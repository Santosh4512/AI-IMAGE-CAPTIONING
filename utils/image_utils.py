import os
from io import BytesIO
from typing import BinaryIO, Dict, Any

from PIL import Image

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_image_metadata(image_bytes: bytes) -> Dict[str, Any]:
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            width, height = image.size
            mime_type = image.get_format_mimetype() or "image/unknown"
            return {
                "width": width,
                "height": height,
                "dimensions": f"{width} × {height}px",
                "mime_type": mime_type,
                "format": (image.format or "UNKNOWN").upper(),
            }
    except Exception as exc:  # pragma: no cover - image decode path
        raise ValueError("The uploaded file is not a valid image.") from exc


def validate_image_file(uploaded_file: BinaryIO) -> Dict[str, Any]:
    if uploaded_file is None:
        raise ValueError("No file was uploaded.")

    filename = getattr(uploaded_file, "name", "uploaded_image") or "uploaded_image"
    extension = os.path.splitext(filename)[1].lower().lstrip(".")
    allowed_extensions = {"jpg", "jpeg", "png", "webp"}

    if extension not in allowed_extensions:
        raise ValueError("Unsupported file format. Please upload JPG, JPEG, PNG, or WEBP.")

    file_bytes = uploaded_file.getvalue()
    if not file_bytes:
        raise ValueError("The uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError("File too large. Please upload an image smaller than 15 MB.")

    mime_type = getattr(uploaded_file, "type", "") or ""
    if mime_type and mime_type not in SUPPORTED_IMAGE_TYPES:
        raise ValueError("The upload type is not supported. Use a valid image file.")

    metadata = get_image_metadata(file_bytes)
    image_format = metadata["format"].lower()
    if image_format not in {"jpg", "jpeg", "png", "webp"}:
        raise ValueError("The uploaded file is not a valid image.")

    return {
        "filename": filename,
        "mime_type": mime_type or metadata["mime_type"],
        "dimensions": metadata["dimensions"],
        "width": metadata["width"],
        "height": metadata["height"],
        "file_size": format_file_size(len(file_bytes)),
        "format": metadata["format"],
    }
