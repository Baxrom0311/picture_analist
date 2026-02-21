"""
Custom permission classes.
"""
from rest_framework.permissions import BasePermission


class IsArtist(BasePermission):
    """Allows access only to users with 'artist' role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'artist'
        )


class IsAdmin(BasePermission):
    """Allows access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'admin' or request.user.is_staff)
        )


class IsJudge(BasePermission):
    """Allows access only to users with 'judge' role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'judge'
        )


class IsJudgeOrAdmin(BasePermission):
    """Allows access to Judges and Admins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role in ['judge', 'admin'] or request.user.is_staff)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allows access only to the owner of the object
    or admin users.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin' or request.user.is_staff:
            return True
        # Check if the object has a 'user' attribute
        return hasattr(obj, 'user') and obj.user == request.user
