"""
Custom permissions for Users app.
"""
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission: only allows the owner to access.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
