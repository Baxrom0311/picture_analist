"""
Image Service - Validation and optimization for uploaded artwork images.
"""
import os
import io
import logging
from PIL import Image
from django.conf import settings

from core.exceptions import ImageValidationError

logger = logging.getLogger(__name__)


class ImageService:
    """
    Service for image validation and optimization.
    """

    MAX_SIZE = getattr(settings, 'MAX_UPLOAD_SIZE', 10485760)  # 10MB
    ALLOWED_FORMATS = getattr(settings, 'ALLOWED_IMAGE_FORMATS', ['jpeg', 'jpg', 'png', 'webp'])
    THUMBNAIL_SIZE = (300, 300)

    def validate_image(self, image_file):
        """
        Validate uploaded image file.

        Checks:
        - File size
        - Format
        - Can be opened by Pillow

        Raises:
            ImageValidationError if validation fails
        """
        # Check file size
        if image_file.size > self.MAX_SIZE:
            raise ImageValidationError(
                f"Fayl hajmi {self.MAX_SIZE // (1024*1024)}MB dan oshmasligi kerak. "
                f"Joriy: {image_file.size / (1024*1024):.1f}MB"
            )

        # Check format
        ext = os.path.splitext(image_file.name)[1].lower().lstrip('.')
        if ext not in self.ALLOWED_FORMATS:
            raise ImageValidationError(
                f"Faqat {', '.join(self.ALLOWED_FORMATS)} formatlar qabul qilinadi. "
                f"Yuborilgan: {ext}"
            )

        # Try opening with Pillow
        try:
            img = Image.open(image_file)
            img.verify()
        except Exception:
            raise ImageValidationError("Fayl rasm sifatida ochilmadi. Iltimos boshqa rasm yuklang.")

        return True

    def get_image_metadata(self, image_file):
        """
        Extract image metadata.

        Returns:
            dict with width, height, format, file_size
        """
        img = Image.open(image_file)
        return {
            'width': img.size[0],
            'height': img.size[1],
            'format': (img.format or '').lower(),
            'file_size': image_file.size,
        }

    def optimize_image(self, image_path, max_size=1920, quality=85):
        """
        Optimize an image in-place.

        - Resize if exceeding max_size
        - Compress to JPEG quality
        """
        try:
            img = Image.open(image_path)

            # Resize if needed
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Save optimized
            img.convert('RGB').save(image_path, format='JPEG', quality=quality, optimize=True)
            logger.info(f"Image optimized: {image_path}")
            return True
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return False

    def create_thumbnail(self, image_path, output_path=None):
        """
        Create a thumbnail for the image.

        Args:
            image_path: Path to original image
            output_path: Path for thumbnail (default: adds _thumb suffix)

        Returns:
            Path to thumbnail
        """
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_thumb{ext}"

        try:
            img = Image.open(image_path)
            img.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img.save(output_path, quality=80)
            return output_path
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            return None
