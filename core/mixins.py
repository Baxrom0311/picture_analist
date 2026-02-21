"""
Reusable mixins for views and models.
"""
from django.db import models


class TimestampMixin(models.Model):
    """Adds created_at and updated_at timestamp fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
