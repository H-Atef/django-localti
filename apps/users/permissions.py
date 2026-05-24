
from rest_framework.permissions import BasePermission

from apps.users.helpers.constants import UserRole


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )


class IsInfluencer(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.INFLUENCER
        )


class IsMarketer(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.MARKETER
        )


class IsLocalBrand(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.LOCAL_BRAND
        )


class IsAdminOrMarketer(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                UserRole.ADMIN,
                UserRole.MARKETER,
            ]
        )


class IsAdminOrSelf(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role == UserRole.ADMIN:
            return True
        if hasattr(obj, "user"):
            return obj.user == request.user
        return obj == request.user