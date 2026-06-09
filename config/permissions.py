from rest_framework import permissions


class IsEmployerOrReadOnly(permissions.BasePermission):
    """Allow read-only for everyone, write only for employers"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == "employer"


class IsCandidate(permissions.BasePermission):
    """Allow access only to candidates"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "candidate"


class IsEmployer(permissions.BasePermission):
    """Allow access only to employers"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "employer"


class IsAdmin(permissions.BasePermission):
    """Allow access only to admins"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == "admin"
            or request.user.is_superuser
            or request.user.is_staff
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow edit only to object owner"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(obj, "employer") and obj.employer == request.user


class IsJobOwnerOrAdmin(permissions.BasePermission):
    """Allow job edit/delete to the owner OR any staff/superuser/admin-role user"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser or request.user.is_staff:
            return True
        if hasattr(request.user, "role") and request.user.role == "admin":
            return True
        return obj.employer == request.user


class IsApplicationOwnerOrEmployer(permissions.BasePermission):
    """Allow candidate to view own application, employer to view theirs"""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "candidate":
            return obj.candidate == request.user
        if request.user.role == "employer":
            return obj.job.employer == request.user
        return False


class IsApplicationEmployer(permissions.BasePermission):
    """Allow employer to update application status"""

    def has_object_permission(self, request, view, obj):
        return obj.job.employer == request.user
