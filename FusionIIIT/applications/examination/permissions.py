from rest_framework.permissions import BasePermission

from applications.globals.models import HoldsDesignation


def _user_roles(user):
    roles = set()
    if not user or not user.is_authenticated:
        return roles
    if user.is_superuser:
        roles.add("superuser")
    extra_info = getattr(user, "extrainfo", None)
    if extra_info and extra_info.user_type:
        roles.add(extra_info.user_type)
    if extra_info and extra_info.last_selected_role:
        roles.add(extra_info.last_selected_role)
    for held in HoldsDesignation.objects.filter(working=user).select_related("designation"):
        roles.add(str(held.designation.name))
        roles.add(str(held.designation.full_name))
    return {role.lower() for role in roles if role}


class BaseRolePermission(BasePermission):
    allowed_roles = tuple()

    def has_permission(self, request, view):
        roles = _user_roles(request.user)
        return any(role in roles for role in self.allowed_roles)


class IsStudent(BaseRolePermission):
    allowed_roles = ("student",)


class IsFaculty(BaseRolePermission):
    allowed_roles = ("faculty", "assistant professor", "associate professor", "professor")


class IsAcadAdmin(BaseRolePermission):
    allowed_roles = ("acadadmin", "academic admin", "superuser")


class IsDean(BaseRolePermission):
    allowed_roles = ("dean academic", "dean", "superuser")
