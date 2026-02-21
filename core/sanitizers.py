"""
Input sanitization utilities for secure data handling.
"""
import re
import os
import html
import unicodedata

from rest_framework import serializers


def sanitize_text(value):
    """
    Sanitize text input by removing potentially dangerous content.

    - Strips HTML tags
    - Escapes special characters
    - Normalizes unicode
    - Removes control characters
    """
    if not isinstance(value, str):
        return value

    # Normalize unicode
    value = unicodedata.normalize('NFKC', value)

    # Remove control characters (except newline, tab)
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', value)

    # Strip HTML tags
    value = re.sub(r'<[^>]+>', '', value)

    # Escape HTML entities
    value = html.escape(value, quote=True)

    # Remove potential script injections
    value = re.sub(
        r'(javascript|vbscript|on\w+)\s*[:=]',
        '', value, flags=re.IGNORECASE
    )

    return value.strip()


def sanitize_filename(filename):
    """
    Make a filename safe for storage.

    - Remove path separators
    - Remove null bytes
    - Limit length
    - Only allow safe characters
    """
    if not filename:
        return 'unnamed'

    # Remove path separators and null bytes
    filename = os.path.basename(filename)
    filename = filename.replace('\x00', '')

    # Split name and extension
    name, ext = os.path.splitext(filename)

    # Only allow alphanumeric, dash, underscore, dot
    name = re.sub(r'[^\w\-.]', '_', name)

    # Limit length
    name = name[:100]

    # Ensure not empty
    if not name:
        name = 'unnamed'

    return f"{name}{ext.lower()}"


# =============================================================================
# Sanitized Serializer Fields
# =============================================================================

class SanitizedCharField(serializers.CharField):
    """CharField that automatically sanitizes input."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return sanitize_text(value)


class SanitizedTextField(serializers.CharField):
    """TextField that automatically sanitizes input while preserving newlines."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        # Preserve newlines but sanitize everything else
        lines = value.split('\n')
        sanitized_lines = [sanitize_text(line) for line in lines]
        return '\n'.join(sanitized_lines)
