# views/accounts.py
# عروض إدارة المستخدمين والأدوار

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from accounts.models import User, Role, UserProfile, UserAddress, UserActivity
from .dashboard import DashboardAccessMixin


# قائمة المستخدمين
class UserListView(DashboardAccessMixin, View):
    """عرض قائمة المستخدمين"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')

        users = User.objects.all().order_by('-date_joined')

        # تطبيق البحث
        if query:
            users = users.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        # تطبيق التصفية حسب الدور
        if role_filter:
            users = users.filter(role__id=role_filter)

        # تصفية حسب الحالة
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

        # التصفح الجزئي
        paginator = Paginator(users, 10)  # 10 مستخدمين في كل صفحة
        page = request.GET.get('page', 1)
        users_page = paginator.get_page(page)

        # قائمة الأدوار للتصفية
        roles = Role.objects.all()

        context = {
            'users': users_page,
            'roles': roles,
            'query': query,
            'role_filter': role_filter,
            'status_filter': status_filter,
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/accounts/users_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': users_page.has_next(),
                'has_prev': users_page.has_previous(),
                'page': users_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/accounts/user_list.html', context)


# عرض تفاصيل المستخدم
class UserDetailView(DashboardAccessMixin, View):
    """عرض تفاصيل المستخدم"""

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # جلب الملف الشخصي إن وجد
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = None

        # جلب عناوين المستخدم
        addresses = user.addresses.all()

        # جلب سجل نشاط المستخدم
        activities = user.activities.all().order_by('-timestamp')[:20]

        # جلب طلبات المستخدم
        orders = user.orders.all().order_by('-created_at')[:10]

        context = {
            'user_obj': user,  # استخدم user_obj بدلاً من user لتجنب التعارض مع user الحالي
            'profile': profile,
            'addresses': addresses,
            'activities': activities,
            'orders': orders,
            'total_orders': user.orders.count(),
            'total_spent': user.total_spent,
        }

        return render(request, 'dashboard/accounts/user_detail.html', context)


# إنشاء وتحديث المستخدم
class UserFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث المستخدم"""

    def get(self, request, user_id=None):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard_users')

        if user_id:
            # تحديث مستخدم موجود
            user = get_object_or_404(User, id=user_id)
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = None
            form_title = 'تحديث المستخدم'
        else:
            # إنشاء مستخدم جديد
            user = None
            profile = None
            form_title = 'إنشاء مستخدم جديد'

        # جلب الأدوار المتاحة
        roles = Role.objects.all()

        context = {
            'user_obj': user,
            'profile': profile,
            'roles': roles,
            'form_title': form_title
        }

        return render(request, 'dashboard/accounts/user_form.html', context)

    def post(self, request, user_id=None):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard_users')

        # جمع البيانات من النموذج
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        role_id = request.POST.get('role')

        # التحقق من البيانات
        if not username or not email:
            messages.error(request, 'اسم المستخدم والبريد الإلكتروني مطلوبان')
            return redirect(request.path)

        # إنشاء أو تحديث المستخدم
        if user_id:
            user = get_object_or_404(User, id=user_id)

            # تحديث البيانات الأساسية
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            user.is_staff = is_staff
            user.is_superuser = is_superuser

            # تحديث كلمة المرور إذا تم تقديمها
            if password:
                user.set_password(password)

            # تحديث الدور
            if role_id:
                role = get_object_or_404(Role, id=role_id)
                user.role = role

            user.save()
            messages.success(request, 'تم تحديث المستخدم بنجاح')
        else:
            # إنشاء مستخدم جديد
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=is_active,
                    is_staff=is_staff,
                    is_superuser=is_superuser
                )

                # إضافة الدور
                if role_id:
                    role = get_object_or_404(Role, id=role_id)
                    user.role = role
                    user.save()

                messages.success(request, 'تم إنشاء المستخدم بنجاح')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء المستخدم: {str(e)}')
                return redirect(request.path)

        # معالجة الملف الشخصي
        bio = request.POST.get('bio', '')
        profession = request.POST.get('profession', '')
        company = request.POST.get('company', '')
        website = request.POST.get('website', '')
        twitter = request.POST.get('twitter', '')
        facebook = request.POST.get('facebook', '')
        instagram = request.POST.get('instagram', '')
        linkedin = request.POST.get('linkedin', '')

        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.bio = bio
            profile.profession = profession
            profile.company = company
            profile.website = website
            profile.twitter = twitter
            profile.facebook = facebook
            profile.instagram = instagram
            profile.linkedin = linkedin
            profile.save()
        except Exception as e:
            messages.warning(request, f'تم حفظ المستخدم ولكن حدث خطأ في حفظ الملف الشخصي: {str(e)}')

        # رفع صورة المستخدم إن وجدت
        avatar = request.FILES.get('avatar')
        if avatar:
            user.avatar = avatar
            user.save()

        return redirect('dashboard_user_detail', user_id=user.id)


# حذف المستخدم
@method_decorator(login_required, name='dispatch')
class UserDeleteView(DashboardAccessMixin, View):
    """حذف المستخدم"""

    def post(self, request, user_id):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard_users')

        user = get_object_or_404(User, id=user_id)

        # لا يمكن حذف المستخدم الحالي
        if user == request.user:
            messages.error(request, 'لا يمكن حذف حسابك الحالي')
            return redirect('dashboard_users')

        # حذف المستخدم
        try:
            user.delete()
            messages.success(request, 'تم حذف المستخدم بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف المستخدم: {str(e)}')

        return redirect('dashboard_users')


# إدارة الأدوار
class RoleListView(DashboardAccessMixin, View):
    """عرض قائمة الأدوار"""

    def get(self, request):
        roles = Role.objects.all()

        context = {
            'roles': roles
        }

        return render(request, 'dashboard/accounts/role_list.html', context)


# إنشاء وتحديث الدور
class RoleFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث الدور"""

    def get(self, request, role_id=None):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard_roles')

        if role_id:
            # تحديث دور موجود
            role = get_object_or_404(Role, id=role_id)
            form_title = 'تحديث الدور'
        else:
            # إنشاء دور جديد
            role = None
            form_title = 'إنشاء دور جديد'

        # جلب الصلاحيات المتاحة
        from django.contrib.auth.models import Permission
        permissions = Permission.objects.all().order_by('content_type__app_label', 'content_type__model')

        context = {
            'role': role,
            'permissions': permissions,
            'form_title': form_title
        }

        return render(request, 'dashboard/accounts/role_form.html', context)

    def post(self, request, role_id=None):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard_roles')

        # جمع البيانات من النموذج
        name = request.POST.get('name')
        description = request.POST.get('description')
        permission_ids = request.POST.getlist('permissions')

        # التحقق من البيانات
        if not name:
            messages.error(request, 'اسم الدور مطلوب')
            return redirect(request.path)

        # إنشاء أو تحديث الدور
        if role_id:
            role = get_object_or_404(Role, id=role_id)
            role.name = name
            role.description = description
            role.save()
            messages.success(request, 'تم تحديث الدور بنجاح')
        else:
            # إنشاء دور جديد
            try:
                role = Role.objects.create(
                    name=name,
                    description=description
                )
                messages.success(request, 'تم إنشاء الدور بنجاح')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء الدور: {str(e)}')
                return redirect(request.path)

        # تحديث الصلاحيات
        from django.contrib.auth.models import Permission
        permissions = Permission.objects.filter(id__in=permission_ids)
        role.permissions.set(permissions)

        return redirect('dashboard_roles')


# حذف الدور
@method_decorator(login_required, name='dispatch')
class RoleDeleteView(DashboardAccessMixin, View):
    """حذف الدور"""

    def post(self, request, role_id):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard_roles')

        role = get_object_or_404(Role, id=role_id)

        # التحقق من عدم وجود مستخدمين يستخدمون هذا الدور
        if role.users.exists():
            messages.error(request, 'لا يمكن حذف الدور لأنه مستخدم من قبل بعض المستخدمين')
            return redirect('dashboard_roles')

        # حذف الدور
        try:
            role.delete()
            messages.success(request, 'تم حذف الدور بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الدور: {str(e)}')

        return redirect('dashboard_roles')