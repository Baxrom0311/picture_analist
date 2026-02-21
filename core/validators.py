"""
Custom validators.
"""
import os

from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image, UnidentifiedImageError


def validate_image_size(value):
    """Validate that the uploaded image does not exceed MAX_UPLOAD_SIZE."""
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10485760)
    if value.size > max_size:
        raise ValidationError(
            f'Fayl hajmi {max_size // (1024*1024)}MB dan oshmasligi kerak. '
            f'Joriy hajm: {value.size / (1024*1024):.1f}MB'
        )


def validate_image_format(value):
    """Validate that the uploaded file is in an allowed image format."""
    ext = os.path.splitext(value.name)[1].lower().lstrip('.')
    allowed = getattr(settings, 'ALLOWED_IMAGE_FORMATS', ['jpeg', 'jpg', 'png', 'webp'])
    normalized_allowed = {'jpeg' if fmt == 'jpg' else fmt for fmt in allowed}

    if ext not in allowed:
        raise ValidationError(
            f"Faqat {', '.join(allowed)} formatdagi fayllar qabul qilinadi. "
            f"Yuborilgan format: {ext}"
        )

    try:
        image = Image.open(value)
        image.verify()
        detected_format = (image.format or '').lower()
    except (UnidentifiedImageError, OSError):
        raise ValidationError("Yuklangan fayl haqiqiy rasm emas.")
    finally:
        # Ensure Django storage backends can read the file again after validation.
        if hasattr(value, 'seek'):
            value.seek(0)

    if detected_format and detected_format not in normalized_allowed:
        raise ValidationError(
            f"Fayl kontenti {detected_format} formatda. "
            f"Faqat {', '.join(allowed)} formatlar qabul qilinadi."
        )
