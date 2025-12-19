# accounts/backends.py
from django.contrib.auth.backends import ModelBackend


class RolePermissionBackend(ModelBackend):
    """نظام مخصص للتحقق من صلاحيات المستخدم بناءً على الدور (Role)"""

    def has_perm(self, user_obj, perm, obj=None):
        # التحقق من تسجيل الدخول
        if not user_obj.is_active:
            return False

        # التحقق من المدير (superuser)
        if user_obj.is_superuser:
            return True

        # التحقق من الصلاحيات المباشرة (طريقة الأصل)
        if super().has_perm(user_obj, perm, obj):
            return True

        # التحقق من صلاحيات الدور
        if hasattr(user_obj, 'role') and user_obj.role:
            # تخزين جميع صلاحيات الدور كسلاسل نصية (app_label.codename)
            role_perms = [
                f"{p.content_type.app_label}.{p.codename}"
                for p in user_obj.role.permissions.select_related('content_type').all()
            ]

            # التحقق من وجود الصلاحية المطلوبة
            return perm in role_perms

        return False