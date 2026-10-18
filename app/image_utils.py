from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError

class ImageValidationError(ValueError): pass

def validate_image(path: Path, *, max_bytes: int, max_pixels: int, max_dimension: int) -> tuple[int, int]:
    try:
        if not path.is_file() or path.stat().st_size <= 0: raise ImageValidationError("The file is empty or missing.")
        if path.stat().st_size > max_bytes: raise ImageValidationError("Image exceeds the configured file-size limit.")
        with Image.open(path) as im:
            if im.format not in {"JPEG", "PNG", "WEBP"}: raise ImageValidationError("Please send a JPEG, PNG, or WebP image.")
            w, h = im.size
            if w <= 0 or h <= 0 or w * h > max_pixels: raise ImageValidationError("Image dimensions are too large.")
            if max(w, h) > max_dimension: raise ImageValidationError("Image width or height exceeds the configured limit.")
            im.verify()
        return w, h
    except ImageValidationError: raise
    except (UnidentifiedImageError, OSError, ValueError) as exc: raise ImageValidationError("This file is not a valid supported image.") from exc

def normalize_image(src: Path, dst: Path) -> None:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.save(dst, format="JPEG", quality=95, optimize=True)
