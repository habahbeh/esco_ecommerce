from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


def permission_required(perm):
    """
    مُزخرف للتحقق من صلاحية محددة
    """

    def check_perms(user):
        # السماح للمشرف (superuser) دائمًا
        if user.is_superuser:
            return True
        # التحقق من الصلاحية المطلوبة
        if user.has_perm(perm):
            return True
        return False

    return user_passes_test(check_perms, login_url=None, redirect_field_name=None)


def handle_no_permission(request):
    """
    معالجة حالة عدم وجود صلاحية
    """
    messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
    return redirect('dashboard:dashboard_home')