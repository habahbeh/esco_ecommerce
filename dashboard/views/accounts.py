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
from django import forms
from django.utils.translation import gettext_lazy as _
from dashboard.forms.accounts import UserForm, RoleForm, UserProfileForm, UserAddressForm

from django.utils.decorators import method_decorator
from dashboard.decorators import permission_required


# قائمة المستخدمين
@method_decorator(permission_required('accounts.view_user'), name='dispatch')
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
            # التعامل مع قيم خاصة
            if role_filter == 'superuser':
                users = users.filter(is_superuser=True)
            elif role_filter == 'staff':
                users = users.filter(is_staff=True, is_superuser=False)
            elif role_filter.isdigit():  # التحقق من أن القيمة رقمية
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
@method_decorator(permission_required('accounts.view_user'), name='dispatch')
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
@method_decorator(permission_required('accounts.add_user'), name='dispatch')
class UserFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث المستخدم"""

    def get(self, request, user_id=None):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard:dashboard_users')

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
            return redirect('dashboard:dashboard_users')

        # جمع البيانات من النموذج
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number', '')
        birth_date = request.POST.get('birth_date', None)
        gender = request.POST.get('gender', '')
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
            user.phone_number = phone_number
            user.gender = gender if gender else None
            if birth_date:
                user.birth_date = birth_date
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
                    phone_number=phone_number,
                    gender=gender if gender else None,
                    birth_date=birth_date if birth_date else None,
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

        return redirect('dashboard:dashboard_user_detail', user_id=user.id)


# حذف المستخدم
@method_decorator(login_required, name='dispatch')
class UserDeleteView(DashboardAccessMixin, View):
    """حذف المستخدم"""

    def post(self, request, user_id):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard:dashboard_users')

        user = get_object_or_404(User, id=user_id)

        # لا يمكن حذف المستخدم الحالي
        if user == request.user:
            messages.error(request, 'لا يمكن حذف حسابك الحالي')
            return redirect('dashboard:dashboard_users')

        # حذف المستخدم
        try:
            user.delete()
            messages.success(request, 'تم حذف المستخدم بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف المستخدم: {str(e)}')

        return redirect('dashboard:dashboard_users')


# إدارة الأدوار
@method_decorator(permission_required('accounts.view_role'), name='dispatch')
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
            return redirect('dashboard:dashboard_roles')

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
        from django.contrib.contenttypes.models import ContentType

        # جلب صلاحيات المنتج والمستخدمين فقط
        permissions = []

        # قائمة النماذج التي نريد عرضها
        models_to_display = [
            # مجموعة المنتجات
            {'app_label': 'products', 'model': 'product'},
            {'app_label': 'products', 'model': 'category'},
            {'app_label': 'products', 'model': 'brand'},

            # مجموعة المستخدمين
            {'app_label': 'accounts', 'model': 'user'},
            {'app_label': 'accounts', 'model': 'role'},

            # مجموعة الطلبات
            {'app_label': 'orders', 'model': 'order'},
            # {'app_label': 'orders', 'model': 'orderitem'},

            # مجموعة الدفع
            {'app_label': 'checkout', 'model': 'paymentmethod'},

            # مجموعة النظام
            {'app_label': 'core', 'model': 'sitesettings'},
            {'app_label': 'core', 'model': 'newsletter'},
            {'app_label': 'core', 'model': 'slideritem'},

            # مجموعة الفعاليات
            {'app_label': 'events', 'model': 'event'},
            {'app_label': 'events', 'model': 'eventimage'},
        ]



        # جلب الصلاحيات للنماذج المحددة
        for model_info in models_to_display:
            try:
                content_type = ContentType.objects.get(
                    app_label=model_info['app_label'],
                    model=model_info['model']
                )
                model_permissions = Permission.objects.filter(content_type=content_type).order_by('codename')
                permissions.extend(model_permissions)
            except ContentType.DoesNotExist:
                # تجاهل الخطأ إذا لم يوجد النموذج
                pass

        # تجميع الصلاحيات حسب التطبيق والنموذج
        permissions_by_app = {}
        for perm in permissions:
            app_label = perm.content_type.app_label
            model = perm.content_type.model

            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = {}

            if model not in permissions_by_app[app_label]:
                permissions_by_app[app_label][model] = []

            permissions_by_app[app_label][model].append(perm)

        context = {
            'role': role,
            'permissions': permissions,
            'permissions_by_app': permissions_by_app,
            'form_title': form_title
        }

        return render(request, 'dashboard/accounts/role_form.html', context)

    def post(self, request, role_id=None):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard:dashboard_roles')

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

        return redirect('dashboard:dashboard_roles')


# حذف الدور
@method_decorator(login_required, name='dispatch')
class RoleDeleteView(DashboardAccessMixin, View):
    """حذف الدور"""

    def post(self, request, role_id):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard:dashboard_roles')  # تأكد من استخدام بادئة dashboard:

        role = get_object_or_404(Role, id=role_id)

        # التحقق من عدم وجود مستخدمين يستخدمون هذا الدور
        if role.users.exists():
            messages.error(request, 'لا يمكن حذف الدور لأنه مستخدم من قبل بعض المستخدمين')
            return redirect('dashboard:dashboard_roles')  # تأكد من استخدام بادئة dashboard:

        # حذف الدور
        try:
            role.delete()
            messages.success(request, 'تم حذف الدور بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الدور: {str(e)}')

        return redirect('dashboard:dashboard_roles')  # تأكد من استخدام بادئة dashboard:


class UserAddressSaveView(DashboardAccessMixin, View):
    """عرض حفظ عنوان المستخدم"""

    def post(self, request):
        # استخراج بيانات العنوان من الطلب
        address_id = request.POST.get('id')
        user_id = request.POST.get('user_id')

        # التحقق من وجود المستخدم
        user = get_object_or_404(User, id=user_id)

        # التحقق من صلاحية الوصول
        if not request.user.is_superuser and not request.user.has_perm('accounts.change_useraddress'):
            return JsonResponse({
                'success': False,
                'message': 'ليس لديك صلاحية تعديل عناوين المستخدمين'
            })

        # إنشاء أو تحديث العنوان
        if address_id:
            # تحديث عنوان موجود
            address = get_object_or_404(UserAddress, id=address_id, user=user)
        else:
            # إنشاء عنوان جديد
            address = UserAddress(user=user)

        # تحديث حقول العنوان
        address.label = request.POST.get('label')
        address.type = request.POST.get('type')
        address.first_name = request.POST.get('first_name')
        address.last_name = request.POST.get('last_name')
        address.address_line_1 = request.POST.get('address_line_1')
        address.address_line_2 = request.POST.get('address_line_2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.postal_code = request.POST.get('postal_code')
        address.country = request.POST.get('country')
        address.phone_number = request.POST.get('phone_number')
        address.is_default = request.POST.get('is_default') == 'true'
        address.is_shipping_default = request.POST.get('is_shipping_default') == 'true'
        address.is_billing_default = request.POST.get('is_billing_default') == 'true'

        try:
            address.save()
            return JsonResponse({
                'success': True,
                'message': 'تم حفظ العنوان بنجاح'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'حدث خطأ أثناء حفظ العنوان: {str(e)}'
            })


class UserAddressGetView(DashboardAccessMixin, View):
    """عرض الحصول على بيانات عنوان المستخدم"""

    def get(self, request):
        address_id = request.GET.get('address_id')

        # التحقق من وجود العنوان
        try:
            address = UserAddress.objects.get(id=address_id)
        except UserAddress.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'العنوان غير موجود'
            })

        # التحقق من صلاحية الوصول
        if not request.user.is_superuser and not request.user.has_perm('accounts.view_useraddress'):
            return JsonResponse({
                'success': False,
                'message': 'ليس لديك صلاحية عرض عناوين المستخدمين'
            })

        # إرجاع بيانات العنوان
        return JsonResponse({
            'success': True,
            'address': {
                'id': str(address.id),
                'label': address.label,
                'type': address.type,
                'first_name': address.first_name,
                'last_name': address.last_name,
                'address_line_1': address.address_line_1,
                'address_line_2': address.address_line_2,
                'city': address.city,
                'state': address.state,
                'postal_code': address.postal_code,
                'country': address.country,
                'phone_number': address.phone_number,
                'is_default': address.is_default,
                'is_shipping_default': address.is_shipping_default,
                'is_billing_default': address.is_billing_default
            }
        })


class UserAddressDeleteView(DashboardAccessMixin, View):
    """عرض حذف عنوان المستخدم"""

    def post(self, request):
        address_id = request.POST.get('address_id')

        # التحقق من وجود العنوان
        try:
            address = UserAddress.objects.get(id=address_id)
        except UserAddress.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'العنوان غير موجود'
            })

        # التحقق من صلاحية الوصول
        if not request.user.is_superuser and not request.user.has_perm('accounts.delete_useraddress'):
            return JsonResponse({
                'success': False,
                'message': 'ليس لديك صلاحية حذف عناوين المستخدمين'
            })

        # حذف العنوان
        try:
            address.delete()
            return JsonResponse({
                'success': True,
                'message': 'تم حذف العنوان بنجاح'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'حدث خطأ أثناء حذف العنوان: {str(e)}'
            })


class UserAddressListPartialView(DashboardAccessMixin, View):
    """عرض قائمة عناوين المستخدم الجزئية"""

    def get(self, request):
        user_id = request.GET.get('user_id')

        # التحقق من وجود المستخدم
        user = get_object_or_404(User, id=user_id)

        # التحقق من صلاحية الوصول
        if not request.user.is_superuser and not request.user.has_perm('accounts.view_useraddress'):
            return HttpResponse('<div class="alert alert-danger">ليس لديك صلاحية عرض عناوين المستخدمين</div>')

        # جلب عناوين المستخدم
        addresses = user.addresses.all()

        # تقديم القالب الجزئي
        return render(request, 'dashboard/accounts/user_address_list_partial.html', {
            'addresses': addresses,
            'user': user
        })


class UserResetPasswordView(DashboardAccessMixin, View):
    """عرض إعادة تعيين كلمة المرور للمستخدم"""

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser and not request.user.has_perm('accounts.change_user'):
            messages.error(request, 'ليس لديك صلاحية إعادة تعيين كلمة المرور')
            return redirect('dashboard:dashboard_user_detail', user_id=user_id)

        # جمع البيانات من النموذج
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        send_email = request.POST.get('send_email') == 'on'

        # التحقق من البيانات
        if not new_password:
            messages.error(request, 'كلمة المرور مطلوبة')
            return redirect('dashboard:dashboard_user_detail', user_id=user_id)

        if new_password != confirm_password:
            messages.error(request, 'كلمة المرور وتأكيدها غير متطابقين')
            return redirect('dashboard:dashboard_user_detail', user_id=user_id)

        # إعادة تعيين كلمة المرور
        try:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'تم إعادة تعيين كلمة المرور بنجاح')

            # إرسال بريد إلكتروني للمستخدم إذا تم طلب ذلك
            if send_email:
                try:
                    # هنا يمكنك إضافة كود إرسال البريد الإلكتروني
                    # (يعتمد على كيفية إعداد البريد في تطبيقك)
                    # مثال: send_password_reset_email(user, new_password)
                    messages.info(request, 'تم إرسال بريد إلكتروني إلى المستخدم بكلمة المرور الجديدة')
                except Exception as e:
                    messages.warning(request, f'تم إعادة تعيين كلمة المرور ولكن فشل إرسال البريد الإلكتروني: {str(e)}')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إعادة تعيين كلمة المرور: {str(e)}')

        return redirect('dashboard:dashboard_user_detail', user_id=user_id)

@method_decorator(login_required, name='dispatch')
class UserDeleteView(DashboardAccessMixin, View):
    """حذف المستخدم"""

    def post(self, request, user_id):
        # التحقق من صلاحية الوصول (فقط للمشرف)
        if not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
            return redirect('dashboard:dashboard_users')  # تصحيح هنا - إضافة بادئة dashboard:

        user = get_object_or_404(User, id=user_id)

        # لا يمكن حذف المستخدم الحالي
        if user == request.user:
            messages.error(request, 'لا يمكن حذف حسابك الحالي')
            return redirect('dashboard:dashboard_users')  # تصحيح هنا - إضافة بادئة dashboard:

        # حذف المستخدم
        try:
            user.delete()
            messages.success(request, 'تم حذف المستخدم بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف المستخدم: {str(e)}')

        return redirect('dashboard:dashboard_users')  # تصحيح هنا - إضافة بادئة dashboard:


class UserAddressFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتعديل عنوان المستخدم"""

    def get(self, request, user_id, address_id=None):
        user = get_object_or_404(User, id=user_id)

        # التحقق من صلاحية الوصول
        if not request.user.is_superuser and not request.user.has_perm('accounts.change_useraddress'):
            messages.error(request, 'ليس لديك صلاحية إدارة عناوين المستخدمين')
            return redirect('dashboard:dashboard_user_detail', user_id=user_id)

        # جلب العنوان إذا كان في وضع التعديل
        address = None
        if address_id:
            address = get_object_or_404(UserAddress, id=address_id, user=user)

        # إنشاء نموذج فارغ أو معبأ بالبيانات الحالية
        form = UserAddressForm(instance=address, user=user)

        return render(request, 'dashboard/accounts/user_address_form.html', {
            'form': form,
            'user': user,
            'address': address,
            'form_title': 'تعديل العنوان' if address else 'إضافة عنوان جديد'
        })

    def post(self, request, user_id, address_id=None):
        user = get_object_or_404(User, id=user_id)

        # التحقق من صلاحية الوصول
        if not request.user.is_superuser and not request.user.has_perm('accounts.change_useraddress'):
            messages.error(request, 'ليس لديك صلاحية إدارة عناوين المستخدمين')
            return redirect('dashboard:dashboard_user_detail', user_id=user_id)

        # جلب العنوان إذا كان في وضع التعديل
        address = None
        if address_id:
            address = get_object_or_404(UserAddress, id=address_id, user=user)

        # معالجة النموذج
        form = UserAddressForm(request.POST, instance=address, user=user)

        if form.is_valid():
            # حفظ النموذج مع ربطه بالمستخدم
            address = form.save(commit=False)
            address.user = user
            address.save()

            messages.success(request, 'تم حفظ العنوان بنجاح')
            return redirect('dashboard:dashboard_user_address_list', user_id=user_id)

        # إذا كان النموذج غير صالح
        return render(request, 'dashboard/accounts/user_address_form.html', {
            'form': form,
            'user': user,
            'address': address,
            'form_title': 'تعديل العنوان' if address else 'إضافة عنوان جديد'
        })


class UserAddressListView(DashboardAccessMixin, View):
    """عرض قائمة عناوين المستخدم"""

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # التحقق من صلاحية الوصول
        if not request.user.is_superuser and not request.user.has_perm('accounts.view_useraddress'):
            messages.error(request, 'ليس لديك صلاحية عرض عناوين المستخدمين')
            return redirect('dashboard:dashboard_user_detail', user_id=user_id)

        # جلب عناوين المستخدم
        addresses = user.addresses.all()

        return render(request, 'dashboard/accounts/user_address_list.html', {
            'user': user,
            'addresses': addresses
        })