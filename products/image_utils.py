import io
import os
import logging
from PIL import Image, ImageOps
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

IMAGE_MAX_DIMENSION = getattr(settings, 'IMAGE_MAX_DIMENSION', 1200)
IMAGE_QUALITY = getattr(settings, 'IMAGE_QUALITY', 85)
THUMBNAIL_SIZE = getattr(settings, 'IMAGE_THUMBNAIL_SIZE', (300, 300))
MEDIUM_SIZE = getattr(settings, 'IMAGE_MEDIUM_SIZE', (600, 600))


def _open_and_prepare(source):
    """
    Open image from a file path (str) or Django ImageField/File.
    Returns a PIL Image in RGB mode with EXIF rotation applied, or None.
    """
    try:
        if isinstance(source, str):
            img = Image.open(source)
        else:
            source.open('rb')
            img = Image.open(source)
    except Exception as e:
        logger.warning("Could not open image: %s — %s", source, e)
        return None

    img = ImageOps.exif_transpose(img)

    if img.mode in ('RGBA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    return img


def optimize_image(source, max_dimension=None, quality=None):
    """
    Optimize an image: resize if larger than max_dimension, compress with given quality.
    Preserves aspect ratio. Never upscales small images.
    source: file path (str) or Django ImageField.
    Returns (ContentFile, filename) or None.
    """
    max_dimension = max_dimension or IMAGE_MAX_DIMENSION
    quality = quality or IMAGE_QUALITY

    img = _open_and_prepare(source)
    if img is None:
        return None

    original_size = img.size
    if max(original_size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)

    if isinstance(source, str):
        name = os.path.splitext(os.path.basename(source))[0]
    else:
        name = os.path.splitext(os.path.basename(source.name))[0]
    filename = f"{name}.jpg"

    return ContentFile(buffer.getvalue()), filename


def generate_variant(source, size, suffix, quality=None):
    """
    Generate a resized variant (thumbnail or medium) from source.
    source: file path (str) or Django ImageField.
    Returns (ContentFile, filename) or None.
    """
    quality = quality or IMAGE_QUALITY

    img = _open_and_prepare(source)
    if img is None:
        return None

    img.thumbnail(size, Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)

    if isinstance(source, str):
        name = os.path.splitext(os.path.basename(source))[0]
    else:
        name = os.path.splitext(os.path.basename(source.name))[0]
    filename = f"{name}_{suffix}.jpg"

    return ContentFile(buffer.getvalue()), filename


def generate_thumbnail(source, size=None, quality=None):
    return generate_variant(source, size or THUMBNAIL_SIZE, 'thumb', quality)


def generate_medium(source, size=None, quality=None):
    return generate_variant(source, size or MEDIUM_SIZE, 'medium', quality)


def get_image_size_kb(file_path):
    try:
        return os.path.getsize(file_path) / 1024
    except OSError:
        return 0
