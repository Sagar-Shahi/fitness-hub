"""Admin form mixin that enforces extension and size limits on uploaded images."""

from django import forms
from django.db import models

from .validators import validate_image_extension, validate_image_size


class SafeImageUploadForm(forms.ModelForm):
    """Applies the allow-list and size cap to every ImageField on the model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field, forms.ImageField):
                field.validators = [*field.validators, validate_image_extension, validate_image_size]


def safe_form_for(model_cls):
    """Build a ModelForm subclass for `model_cls` that validates image uploads."""
    meta = type('Meta', (), {'model': model_cls, 'fields': '__all__'})
    return type(f'{model_cls.__name__}SafeForm', (SafeImageUploadForm,), {'Meta': meta})
