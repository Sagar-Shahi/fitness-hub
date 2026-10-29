"""Reusable validators for uploaded files."""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB

# ImageField already checks that the content is a real image (via Pillow);
# these add an extension allow-list and a size cap on top.
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
validate_image_extension = FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS)


def validate_image_size(file) -> None:
    if file.size > MAX_IMAGE_BYTES:
        raise ValidationError(
            'Image is too large (%(size).1f MB). The maximum allowed size is %(max)d MB.',
            code='file_too_large',
            params={'size': file.size / (1024 * 1024), 'max': MAX_IMAGE_BYTES // (1024 * 1024)},
        )
