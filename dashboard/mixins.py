from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.contrib import messages


class DashboardAccessMixin(LoginRequiredMixin):
    """
    Mixin للتحقق من صلاحيات الوصول للوحة التحكم.
    يتأكد من أن المستخدم مسجل الدخول ولديه صلاحيات الوصول للوحة التحكم.
    """
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        # التحقق من تسجيل الدخول (يتم التعامل معه من قبل LoginRequiredMixin)
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # التحقق من صلاحية الوصول للوحة التحكم
        if not self.has_dashboard_access(request.user):
            messages.error(request, _('ليس لديك صلاحية الوصول للوحة التحكم'))
            return redirect('dashboard_access_denied')

        # التحقق من الصلاحيات المطلوبة إذا تم تحديدها
        if self.permission_required and not self.has_permission():
            messages.error(request, _('ليس لديك الصلاحيات المطلوبة للوصول لهذه الصفحة'))
            return redirect('dashboard_home')

        return super().dispatch(request, *args, **kwargs)

    def has_dashboard_access(self, user):
        """التحقق من صلاحيات المستخدم للوصول للوحة التحكم"""
        return user.is_staff or user.is_superuser or (
                hasattr(user, 'role') and user.role and user.role.can_access_dashboard
        )

    def has_permission(self):
        """التحقق من الصلاحيات المطلوبة"""
        user = self.request.user

        # المشرف الرئيسي لديه جميع الصلاحيات
        if user.is_superuser:
            return True

        # التحقق من صلاحيات محددة
        if isinstance(self.permission_required, str):
            return user.has_perm(self.permission_required)
        elif isinstance(self.permission_required, (list, tuple)):
            return all(user.has_perm(perm) for perm in self.permission_required)

        return True


class AjaxableResponseMixin:
    """
    Mixin للتعامل مع طلبات AJAX.
    يعيد استجابة JSON إذا كان الطلب AJAX، وإلا يعيد استجابة عادية.
    """

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = {
                'success': True,
                'message': _('تم الحفظ بنجاح'),
            }

            # إضافة URL إذا كان هناك رابط redirect
            if hasattr(self, 'get_success_url'):
                data['redirect_url'] = self.get_success_url()

            return JsonResponse(data)

        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('حدث خطأ أثناء الحفظ'),
                'errors': form.errors.as_json(),
            }, status=400)

        return response


class SuperuserRequiredMixin(LoginRequiredMixin):
    """
    Mixin للتحقق من أن المستخدم هو المشرف الرئيسي (superuser).
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.is_superuser:
            messages.error(request, _('هذه الصفحة متاحة فقط للمشرف الرئيسي'))
            return redirect('dashboard_home')

        return super().dispatch(request, *args, **kwargs)