# # accounts/views.py
# """
# المشاهدات الخاصة بتطبيق الحسابات
# Accounts app views
# """
#
# from django.shortcuts import render, redirect, get_object_or_404
# from django.views import View
# from django.views.generic import (
#     TemplateView, CreateView, UpdateView, ListView,
#     DetailView, FormView, DeleteView
# )
# from django.contrib.auth import login, logout, authenticate
# from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# from django.contrib.auth.views import (
#     PasswordResetView, PasswordResetConfirmView,
#     PasswordResetDoneView, PasswordResetCompleteView
# )
# from django.contrib.auth.decorators import login_required, user_passes_test
# from django.contrib import messages
# from django.urls import reverse_lazy, reverse
# from django.utils.translation import gettext_lazy as _
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_protect
# from django.views.decorators.debug import sensitive_post_parameters
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.utils.encoding import force_bytes, force_str
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.conf import settings
# from django.http import HttpResponseRedirect, Http404
# from django.contrib.sites.shortcuts import get_current_site
# from django.db.models import Q
#
# from .models import User, UserProfile, UserAddress, UserActivity, Role
# from .forms import (
#     CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm,
#     ExtendedUserProfileForm, UserAddressForm, PasswordChangeForm,
#     NotificationPreferencesForm, EmailVerificationForm,
#     CustomPasswordResetForm, CustomSetPasswordForm,
#     RoleForm, AdminUserManagementForm
# )
#
# from orders.models import Order
#
#
# class StaffRequiredMixin(UserPassesTestMixin):
#     """
#     ميكسن للتحقق من أن المستخدم مشرف
#     Mixin to check if user is staff
#     """
#     def test_func(self):
#         return self.request.user.is_staff or self.request.user.is_superuser
#
#     def handle_no_permission(self):
#         messages.error(self.request, _("ليس لديك صلاحية للوصول إلى هذه الصفحة"))
#         return redirect('accounts:login')
#
#
# class SuperUserRequiredMixin(UserPassesTestMixin):
#     """
#     ميكسن للتحقق من أن المستخدم مدير للنظام
#     Mixin to check if user is superuser
#     """
#     def test_func(self):
#         return self.request.user.is_superuser
#
#     def handle_no_permission(self):
#         messages.error(self.request, _("ليس لديك صلاحية للوصول إلى هذه الصفحة"))
#         return redirect('accounts:login')
#
#
# class RegisterView(CreateView):
#     """
#     عرض التسجيل - يتيح للمستخدمين التسجيل في الموقع
#     Register view - allows users to register on the site
#     """
#     model = User
#     template_name = 'accounts/register.html'
#     form_class = CustomUserCreationForm
#     success_url = reverse_lazy('accounts:register_done')
#
#     @method_decorator(sensitive_post_parameters())
#     @method_decorator(csrf_protect)
#     def dispatch(self, request, *args, **kwargs):
#         if request.user.is_authenticated:
#             return redirect('core:home')
#         return super().dispatch(request, *args, **kwargs)
#
#     def form_valid(self, form):
#         # حفظ المستخدم بشكل آمن
#         user = form.save()
#
#         # إنشاء سجل نشاط
#         UserActivity.objects.create(
#             user=user,
#             activity_type='registration',
#             description=_('تم التسجيل في الموقع'),
#             ip_address=self.request.META.get('REMOTE_ADDR')
#         )
#
#         # إرسال بريد التحقق
#         self.send_verification_email(user)
#
#         return super().form_valid(form)
#
#     def send_verification_email(self, user):
#         """إرسال بريد إلكتروني للتحقق"""
#         current_site = get_current_site(self.request)
#         subject = _('تفعيل حسابك في {0}').format(current_site.name)
#         verification_link = self.request.build_absolute_uri(
#             reverse('accounts:verify_email', kwargs={'token': user.verification_token})
#         )
#
#         message = render_to_string('accounts/email/verification_email.html', {
#             'user': user,
#             'verification_link': verification_link,
#             'site_name': current_site.name,
#             'expiry_hours': 24,  # صلاحية الرمز 24 ساعة
#         })
#
#         try:
#             send_mail(
#                 subject,
#                 message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [user.email],
#                 fail_silently=False,
#                 html_message=message
#             )
#         except Exception as e:
#             # تسجيل الخطأ ولكن لا نعرضه للمستخدم
#             print(f"Error sending verification email: {e}")
#
#
# class RegisterDoneView(TemplateView):
#     """
#     عرض اكتمال التسجيل - يعرض رسالة تأكيد إكمال التسجيل
#     Register done view - displays registration confirmation message
#     """
#     template_name = 'accounts/register_done.html'
#
#
# class EmailVerificationView(View):
#     """
#     عرض تفعيل البريد الإلكتروني - يتحقق من رمز التفعيل ويفعل حساب المستخدم
#     Email verification view - verifies token and activates user account
#     """
#     template_name = 'accounts/verify_email.html'
#
#     def get(self, request, token):
#         # البحث عن المستخدم بواسطة الرمز
#         user = get_object_or_404(User, verification_token=token)
#         form = EmailVerificationForm(user=user, initial={'token': token})
#
#         context = {
#             'form': form,
#             'token': token
#         }
#         return render(request, self.template_name, context)
#
#     def post(self, request, token):
#         # البحث عن المستخدم بواسطة الرمز
#         user = get_object_or_404(User, verification_token=token)
#         form = EmailVerificationForm(user=user, data=request.POST)
#
#         if form.is_valid():
#             # تم تفعيل الحساب بنجاح
#             messages.success(request, _('تم تفعيل حسابك بنجاح! يمكنك الآن تسجيل الدخول.'))
#             return redirect('accounts:login')
#
#         # إذا كان الرمز غير صالح
#         context = {
#             'form': form,
#             'token': token
#         }
#         return render(request, self.template_name, context)
#
#
# class ResendVerificationEmailView(FormView):
#     """
#     عرض إعادة إرسال بريد التفعيل
#     Resend verification email view
#     """
#     template_name = 'accounts/resend_verification.html'
#     form_class = forms.Form
#
#     def form_valid(self, form):
#         email = self.request.POST.get('email')
#         try:
#             user = User.objects.get(email=email, is_verified=False)
#             # إنشاء رمز تحقق جديد
#             user.generate_verification_token()
#
#             # إرسال البريد
#             current_site = get_current_site(self.request)
#             subject = _('تفعيل حسابك في {0}').format(current_site.name)
#             verification_link = self.request.build_absolute_uri(
#                 reverse('accounts:verify_email', kwargs={'token': user.verification_token})
#             )
#
#             message = render_to_string('accounts/email/verification_email.html', {
#                 'user': user,
#                 'verification_link': verification_link,
#                 'site_name': current_site.name,
#                 'expiry_hours': 24,
#             })
#
#             send_mail(
#                 subject,
#                 message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [user.email],
#                 fail_silently=False,
#                 html_message=message
#             )
#
#             messages.success(self.request, _('تم إرسال رابط التفعيل. يرجى التحقق من بريدك الإلكتروني.'))
#         except User.DoesNotExist:
#             # لا نكشف وجود أو عدم وجود البريد الإلكتروني
#             messages.success(self.request, _('إذا كان البريد الإلكتروني صحيحاً، فسيتم إرسال رابط التفعيل.'))
#
#         return redirect('accounts:login')
#
#
# class CustomPasswordResetView(PasswordResetView):
#     """
#     عرض إعادة تعيين كلمة المرور
#     Custom password reset view
#     """
#     template_name = 'accounts/password_reset_form.html'
#     email_template_name = 'accounts/email/password_reset_email.html'
#     subject_template_name = 'accounts/email/password_reset_subject.txt'
#     form_class = CustomPasswordResetForm
#     success_url = reverse_lazy('accounts:password_reset_done')
#
#     @method_decorator(csrf_protect)
#     def dispatch(self, *args, **kwargs):
#         return super().dispatch(*args, **kwargs)
#
#     def form_valid(self, form):
#         # تعديل الطريقة الأصلية لاستخدام نظام الرموز الخاص بنا
#         email = form.cleaned_data['email']
#         try:
#             user = User.objects.get(email=email)
#             token = user.generate_password_reset_token()
#
#             current_site = get_current_site(self.request)
#             subject = _('إعادة تعيين كلمة المرور في {0}').format(current_site.name)
#             reset_link = self.request.build_absolute_uri(
#                 reverse('accounts:password_reset_confirm', kwargs={'token': token})
#             )
#
#             message = render_to_string('accounts/email/password_reset_email.html', {
#                 'user': user,
#                 'reset_link': reset_link,
#                 'site_name': current_site.name,
#                 'expiry_hours': 24,
#             })
#
#             send_mail(
#                 subject,
#                 message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [user.email],
#                 fail_silently=False,
#                 html_message=message
#             )
#         except User.DoesNotExist:
#             # لا نكشف وجود أو عدم وجود البريد الإلكتروني
#             pass
#
#         return super().form_valid(form)
#
#
# class CustomPasswordResetDoneView(PasswordResetDoneView):
#     """
#     عرض اكتمال طلب إعادة تعيين كلمة المرور
#     Custom password reset done view
#     """
#     template_name = 'accounts/password_reset_done.html'
#
#
# class CustomPasswordResetConfirmView(View):
#     """
#     عرض تأكيد إعادة تعيين كلمة المرور
#     Custom password reset confirm view
#     """
#     template_name = 'accounts/password_reset_confirm.html'
#
#     @method_decorator(sensitive_post_parameters())
#     @method_decorator(csrf_protect)
#     def dispatch(self, *args, **kwargs):
#         return super().dispatch(*args, **kwargs)
#
#     def get(self, request, token):
#         # البحث عن المستخدم بواسطة الرمز
#         user = get_object_or_404(User, password_reset_token=token)
#
#         # التحقق من صلاحية الرمز
#         if not user.verify_password_reset_token(token):
#             return redirect('accounts:password_reset')
#
#         form = CustomSetPasswordForm(user)
#         return render(request, self.template_name, {'form': form, 'token': token})
#
#     def post(self, request, token):
#         # البحث عن المستخدم بواسطة الرمز
#         user = get_object_or_404(User, password_reset_token=token)
#
#         # التحقق من صلاحية الرمز
#         if not user.verify_password_reset_token(token):
#             return redirect('accounts:password_reset')
#
#         form = CustomSetPasswordForm(user, request.POST)
#
#         if form.is_valid():
#             # تعيين كلمة المرور الجديدة
#             form.save()
#
#             # إلغاء رمز إعادة تعيين كلمة المرور
#             user.password_reset_token = None
#             user.password_reset_expires = None
#             user.save(update_fields=['password_reset_token', 'password_reset_expires'])
#
#             # تسجيل نشاط
#             UserActivity.objects.create(
#                 user=user,
#                 activity_type='password_reset',
#                 description=_('تم إعادة تعيين كلمة المرور'),
#                 ip_address=request.META.get('REMOTE_ADDR')
#             )
#
#             messages.success(request, _('تم إعادة تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول.'))
#             return redirect('accounts:login')
#
#         return render(request, self.template_name, {'form': form, 'token': token})
#
#
# class CustomPasswordResetCompleteView(PasswordResetCompleteView):
#     """
#     عرض اكتمال إعادة تعيين كلمة المرور
#     Custom password reset complete view
#     """
#     template_name = 'accounts/password_reset_complete.html'
#
#
# class LoginView(View):
#     """
#     عرض تسجيل الدخول - يتيح للمستخدمين تسجيل الدخول
#     Login view - allows users to log in
#     """
#     template_name = 'accounts/login.html'
#
#     @method_decorator(sensitive_post_parameters())
#     @method_decorator(csrf_protect)
#     def dispatch(self, request, *args, **kwargs):
#         # إذا كان المستخدم مسجل الدخول بالفعل، قم بتحويله إلى الصفحة الرئيسية
#         # If the user is already logged in, redirect to home page
#         if request.user.is_authenticated:
#             return redirect('core:home')
#
#         return super().dispatch(request, *args, **kwargs)
#
#     def get(self, request):
#         form = CustomAuthenticationForm()
#         return render(request, self.template_name, {'form': form})
#
#     def post(self, request):
#         form = CustomAuthenticationForm(request, data=request.POST)
#
#         if form.is_valid():
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password')
#             remember_me = form.cleaned_data.get('remember_me')
#
#             # محاولة تسجيل الدخول باستخدام اسم المستخدم أولاً
#             user = authenticate(username=username, password=password)
#
#             # إذا فشل، حاول استخدام البريد الإلكتروني
#             if user is None:
#                 try:
#                     user_obj = User.objects.get(email=username)
#                     user = authenticate(username=user_obj.username, password=password)
#                 except User.DoesNotExist:
#                     user = None
#
#             if user is not None:
#                 # التحقق مما إذا كان المستخدم نشطًا
#                 if not user.is_active:
#                     messages.error(request, _('حسابك غير نشط. يرجى الاتصال بالإدارة.'))
#                     return render(request, self.template_name, {'form': form})
#
#                 # التحقق مما إذا كان البريد الإلكتروني موثقًا
#                 if not user.is_verified:
#                     messages.warning(request, _('يرجى تفعيل حسابك أولاً. تحقق من بريدك الإلكتروني.'))
#                     return redirect('accounts:resend_verification')
#
#                 # تسجيل الدخول
#                 login(request, user)
#
#                 # ضبط مدة صلاحية الجلسة إذا تم تحديد "تذكرني"
#                 if not remember_me:
#                     request.session.set_expiry(0)  # تنتهي عند إغلاق المتصفح
#                 else:
#                     # تعيين فترة أطول (30 يومًا)
#                     request.session.set_expiry(60 * 60 * 24 * 30)
#
#                 # إنشاء سجل نشاط
#                 UserActivity.objects.create(
#                     user=user,
#                     activity_type='login',
#                     description=_('تسجيل الدخول'),
#                     ip_address=request.META.get('REMOTE_ADDR')
#                 )
#
#                 # التحقق مما إذا كان هناك عنوان URL للتحويل إليه
#                 next_url = request.GET.get('next')
#                 if next_url:
#                     return redirect(next_url)
#
#                 # توجيه المستخدمين المشرفين إلى لوحة التحكم
#                 if user.is_staff or user.is_superuser:
#                     return redirect('dashboard:index')
#
#                 return redirect('core:home')
#             else:
#                 messages.error(request, _('اسم المستخدم أو كلمة المرور غير صحيحة'))
#         else:
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, error)
#
#         return render(request, self.template_name, {'form': form})
#
#
# class LogoutView(View):
#     """
#     عرض تسجيل الخروج - يتيح للمستخدمين تسجيل الخروج
#     Logout view - allows users to log out
#     """
#     @method_decorator(login_required)
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)
#
#     def get(self, request):
#         if request.user.is_authenticated:
#             # إنشاء سجل نشاط - Create activity log
#             UserActivity.objects.create(
#                 user=request.user,
#                 activity_type='logout',
#                 description=_('تسجيل الخروج'),
#                 ip_address=request.META.get('REMOTE_ADDR')
#             )
#
#             # تسجيل الخروج
#             logout(request)
#             messages.success(request, _('تم تسجيل الخروج بنجاح'))
#
#         return redirect('core:home')
#
#
# class ProfileView(LoginRequiredMixin, UpdateView):
#     """
#     عرض الملف الشخصي - يتيح للمستخدمين عرض وتحديث معلوماتهم الشخصية
#     Profile view - allows users to view and update their personal information
#     """
#     model = User
#     template_name = 'accounts/profile.html'
#     form_class = UserProfileForm
#     success_url = reverse_lazy('accounts:profile')
#
#     def get_object(self):
#         return self.request.user
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         # إضافة نموذج الملف الشخصي الموسع
#         if hasattr(self.request.user, 'profile'):
#             profile = self.request.user.profile
#         else:
#             profile = UserProfile.objects.create(user=self.request.user)
#
#         if self.request.POST:
#             context['profile_form'] = ExtendedUserProfileForm(
#                 self.request.POST, instance=profile
#             )
#         else:
#             context['profile_form'] = ExtendedUserProfileForm(instance=profile)
#
#         # إضافة عناوين المستخدم
#         context['addresses'] = UserAddress.objects.filter(user=self.request.user)
#
#         # إضافة نموذج تغيير كلمة المرور
#         context['password_form'] = PasswordChangeForm(self.request.user)
#
#         # إضافة نموذج تفضيلات الإشعارات
#         context['notification_form'] = NotificationPreferencesForm(instance=profile)
#
#         return context
#
#     def form_valid(self, form):
#         # حفظ نموذج الملف الشخصي الأساسي
#         response = super().form_valid(form)
#
#         # حفظ نموذج الملف الشخصي الموسع
#         profile_form = ExtendedUserProfileForm(
#             self.request.POST, instance=self.request.user.profile
#         )
#         if profile_form.is_valid():
#             profile_form.save()
#
#         messages.success(self.request, _('تم تحديث الملف الشخصي بنجاح'))
#
#         # إنشاء سجل نشاط - Create activity log
#         UserActivity.objects.create(
#             user=self.request.user,
#             activity_type='profile_update',
#             description=_('تحديث الملف الشخصي'),
#             ip_address=self.request.META.get('REMOTE_ADDR')
#         )
#
#         return response
#
#
# class ChangePasswordView(LoginRequiredMixin, FormView):
#     """
#     عرض تغيير كلمة المرور - يتيح للمستخدمين تغيير كلمة المرور الخاصة بهم
#     Change password view - allows users to change their password
#     """
#     template_name = 'accounts/change_password.html'
#     form_class = PasswordChangeForm
#     success_url = reverse_lazy('accounts:profile')
#
#     @method_decorator(sensitive_post_parameters())
#     @method_decorator(csrf_protect)
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['user'] = self.request.user
#         return kwargs
#
#     def form_valid(self, form):
#         user = form.save()
#
#         # إنشاء سجل نشاط
#         UserActivity.objects.create(
#             user=self.request.user,
#             activity_type='password_change',
#             description=_('تم تغيير كلمة المرور'),
#             ip_address=self.request.META.get('REMOTE_ADDR')
#         )
#
#         messages.success(self.request, _('تم تغيير كلمة المرور بنجاح'))
#
#         # إعادة تسجيل الدخول للمستخدم
#         logout(self.request)
#         user = authenticate(
#             username=user.username,
#             password=form.cleaned_data['new_password1']
#         )
#         login(self.request, user)
#
#         return super().form_valid(form)
#
#
# class NotificationPreferencesView(LoginRequiredMixin, UpdateView):
#     """
#     عرض تفضيلات الإشعارات - يتيح للمستخدمين تحديث تفضيلات الإشعارات
#     Notification preferences view - allows users to update notification preferences
#     """
#     model = UserProfile
#     template_name = 'accounts/notification_preferences.html'
#     form_class = NotificationPreferencesForm
#     success_url = reverse_lazy('accounts:profile')
#
#     def get_object(self):
#         profile, created = UserProfile.objects.get_or_create(user=self.request.user)
#         return profile
#
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         messages.success(self.request, _('تم تحديث تفضيلات الإشعارات بنجاح'))
#         return response
#
#
# class AddressListView(LoginRequiredMixin, ListView):
#     """
#     عرض قائمة العناوين - يعرض قائمة عناوين المستخدم
#     Address list view - displays list of user addresses
#     """
#     model = UserAddress
#     template_name = 'accounts/address_list.html'
#     context_object_name = 'addresses'
#
#     def get_queryset(self):
#         return UserAddress.objects.filter(user=self.request.user)
#
#
# class AddressCreateView(LoginRequiredMixin, CreateView):
#     """
#     عرض إنشاء عنوان - يتيح للمستخدمين إضافة عنوان جديد
#     Address create view - allows users to add a new address
#     """
#     model = UserAddress
#     template_name = 'accounts/address_form.html'
#     form_class = UserAddressForm
#     success_url = reverse_lazy('accounts:address_list')
#
#     def form_valid(self, form):
#         form.instance.user = self.request.user
#         response = super().form_valid(form)
#         messages.success(self.request, _('تم إضافة العنوان بنجاح'))
#         return response
#
#
# class AddressUpdateView(LoginRequiredMixin, UpdateView):
#     """
#     عرض تحديث عنوان - يتيح للمستخدمين تحديث عنوان موجود
#     Address update view - allows users to update an existing address
#     """
#     model = UserAddress
#     template_name = 'accounts/address_form.html'
#     form_class = UserAddressForm
#     success_url = reverse_lazy('accounts:address_list')
#
#     def get_queryset(self):
#         return UserAddress.objects.filter(user=self.request.user)
#
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         messages.success(self.request, _('تم تحديث العنوان بنجاح'))
#         return response
#
#
# class AddressDeleteView(LoginRequiredMixin, DeleteView):
#     """
#     عرض حذف عنوان - يتيح للمستخدمين حذف عنوان موجود
#     Address delete view - allows users to delete an existing address
#     """
#     model = UserAddress
#     template_name = 'accounts/address_confirm_delete.html'
#     success_url = reverse_lazy('accounts:address_list')
#
#     def get_queryset(self):
#         return UserAddress.objects.filter(user=self.request.user)
#
#     def delete(self, request, *args, **kwargs):
#         response = super().delete(request, *args, **kwargs)
#         messages.success(self.request, _('تم حذف العنوان بنجاح'))
#         return response
#
#
# class OrderHistoryView(LoginRequiredMixin, ListView):
#     """
#     عرض سجل الطلبات - يعرض سجل طلبات المستخدم
#     Order history view - displays the user's order history
#     """
#     model = Order
#     template_name = 'accounts/order_history.html'
#     context_object_name = 'orders'
#     paginate_by = 10
#
#     def get_queryset(self):
#         return Order.objects.filter(user=self.request.user).order_by('-created_at')
#
#
# class OrderDetailView(LoginRequiredMixin, DetailView):
#     """
#     عرض تفاصيل الطلب - يعرض تفاصيل طلب معين
#     Order detail view - displays details of a specific order
#     """
#     model = Order
#     template_name = 'accounts/order_detail.html'
#     context_object_name = 'order'
#
#     def get_queryset(self):
#         # التأكد من أن المستخدم يمكنه فقط رؤية طلباته الخاصة
#         # Ensure the user can only see their own orders
#         return Order.objects.filter(user=self.request.user)
#
#
# # --------- مشاهدات لوحة التحكم للمشرفين ---------
# # --------- Admin Dashboard Views ---------
#
# class AdminDashboardView(StaffRequiredMixin, TemplateView):
#     """
#     عرض لوحة تحكم المشرفين - صفحة البداية للمشرفين
#     Admin dashboard view - landing page for administrators
#     """
#     template_name = 'accounts/admin/dashboard.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['total_users'] = User.objects.count()
#         context['active_users'] = User.objects.filter(is_active=True).count()
#         context['staff_users'] = User.objects.filter(is_staff=True).count()
#         context['verified_users'] = User.objects.filter(is_verified=True).count()
#         context['recent_users'] = User.objects.order_by('-date_joined')[:10]
#         context['recent_activities'] = UserActivity.objects.order_by('-timestamp')[:20]
#         return context
#
#
# class UserListView(StaffRequiredMixin, ListView):
#     """
#     عرض قائمة المستخدمين - يعرض قائمة المستخدمين للمشرفين
#     User list view - displays user list for administrators
#     """
#     model = User
#     template_name = 'accounts/admin/user_list.html'
#     context_object_name = 'users'
#     paginate_by = 20
#
#     def get_queryset(self):
#         queryset = User.objects.all().order_by('-date_joined')
#
#         # تطبيق الفلاتر
#         search = self.request.GET.get('search', '')
#         role = self.request.GET.get('role', '')
#         is_active = self.request.GET.get('is_active', '')
#         is_verified = self.request.GET.get('is_verified', '')
#
#         if search:
#             queryset = queryset.filter(
#                 Q(username__icontains=search) |
#                 Q(email__icontains=search) |
#                 Q(first_name__icontains=search) |
#                 Q(last_name__icontains=search)
#             )
#
#         if role:
#             if role == 'staff':
#                 queryset = queryset.filter(is_staff=True)
#             elif role == 'superuser':
#                 queryset = queryset.filter(is_superuser=True)
#             elif role == 'regular':
#                 queryset = queryset.filter(is_staff=False, is_superuser=False)
#             else:
#                 queryset = queryset.filter(role__name=role)
#
#         if is_active:
#             is_active_bool = is_active == 'true'
#             queryset = queryset.filter(is_active=is_active_bool)
#
#         if is_verified:
#             is_verified_bool = is_verified == 'true'
#             queryset = queryset.filter(is_verified=is_verified_bool)
#
#         return queryset
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['roles'] = Role.objects.all()
#
#         # تمرير معلمات البحث للسماح بالاحتفاظ بها أثناء التنقل بين الصفحات
#         context['current_search'] = self.request.GET.get('search', '')
#         context['current_role'] = self.request.GET.get('role', '')
#         context['current_is_active'] = self.request.GET.get('is_active', '')
#         context['current_is_verified'] = self.request.GET.get('is_verified', '')
#
#         return context
#
#
# class UserDetailView(StaffRequiredMixin, DetailView):
#     """
#     عرض تفاصيل المستخدم - يعرض تفاصيل مستخدم محدد للمشرفين
#     User detail view - displays specific user details for administrators
#     """
#     model = User
#     template_name = 'accounts/admin/user_detail.html'
#     context_object_name = 'user_obj'  # تجنب التضارب مع user الخاص بالـ request
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user_obj = self.get_object()
#
#         context['user_activities'] = UserActivity.objects.filter(user=user_obj).order_by('-timestamp')[:20]
#         context['user_orders'] = Order.objects.filter(user=user_obj).order_by('-created_at')[:10]
#         context['user_addresses'] = UserAddress.objects.filter(user=user_obj)
#
#         return context
#
#
# class UserCreateView(StaffRequiredMixin, CreateView):
#     """
#     عرض إنشاء مستخدم - يتيح للمشرفين إنشاء مستخدم جديد
#     User create view - allows administrators to create a new user
#     """
#     model = User
#     template_name = 'accounts/admin/user_form.html'
#     form_class = AdminUserManagementForm
#     success_url = reverse_lazy('accounts:admin_user_list')
#
#     def form_valid(self, form):
#         user = form.save(commit=False)
#
#         # إنشاء كلمة مرور عشوائية وآمنة
#         import secrets
#         import string
#         alphabet = string.ascii_letters + string.digits
#         password = ''.join(secrets.choice(alphabet) for i in range(12))
#
#         user.set_password(password)
#         user.save()
#
#         # حفظ المجموعات
#         if form.cleaned_data.get('groups'):
#             user.groups.set(form.cleaned_data['groups'])
#
#         # إنشاء سجل نشاط
#         UserActivity.objects.create(
#             user=user,
#             activity_type='account_created',
#             description=_('تم إنشاء الحساب بواسطة المشرف'),
#             ip_address=self.request.META.get('REMOTE_ADDR')
#         )
#
#         messages.success(self.request, _(f'تم إنشاء المستخدم بنجاح. كلمة المرور: {password}'))
#         return redirect(self.success_url)
#
#
# class UserUpdateView(StaffRequiredMixin, UpdateView):
#     """
#     عرض تحديث المستخدم - يتيح للمشرفين تحديث مستخدم موجود
#     User update view - allows administrators to update an existing user
#     """
#     model = User
#     template_name = 'accounts/admin/user_form.html'
#     form_class = AdminUserManagementForm
#
#     def get_success_url(self):
#         return reverse('accounts:admin_user_detail', kwargs={'pk': self.object.pk})
#
#     def form_valid(self, form):
#         user = form.save()
#
#         # حفظ المجموعات
#         if form.cleaned_data.get('groups'):
#             user.groups.set(form.cleaned_data['groups'])
#
#         # إنشاء سجل نشاط
#         UserActivity.objects.create(
#             user=user,
#             activity_type='account_updated',
#             description=_('تم تحديث الحساب بواسطة المشرف'),
#             ip_address=self.request.META.get('REMOTE_ADDR')
#         )
#
#         messages.success(self.request, _('تم تحديث المستخدم بنجاح'))
#         return redirect(self.get_success_url())
#
#
# class UserPasswordResetView(StaffRequiredMixin, View):
#     """
#     عرض إعادة تعيين كلمة مرور المستخدم - يتيح للمشرفين إعادة تعيين كلمة مرور مستخدم
#     User password reset view - allows administrators to reset a user's password
#     """
#     def post(self, request, pk):
#         user = get_object_or_404(User, pk=pk)
#
#         # إنشاء كلمة مرور عشوائية وآمنة
#         import secrets
#         import string
#         alphabet = string.ascii_letters + string.digits
#         password = ''.join(secrets.choice(alphabet) for i in range(12))
#
#         user.set_password(password)
#         user.save()
#
#         # إنشاء سجل نشاط
#         UserActivity.objects.create(
#             user=user,
#             activity_type='password_reset',
#             description=_('تم إعادة تعيين كلمة المرور بواسطة المشرف'),
#             ip_address=request.META.get('REMOTE_ADDR')
#         )
#
#         messages.success(request, _(f'تم إعادة تعيين كلمة المرور بنجاح. كلمة المرور الجديدة: {password}'))
#         return redirect('accounts:admin_user_detail', pk=pk)
#
#
# class UserActivateDeactivateView(StaffRequiredMixin, View):
#     """
#     عرض تفعيل/تعطيل المستخدم - يتيح للمشرفين تفعيل أو تعطيل حساب مستخدم
#     User activate/deactivate view - allows administrators to activate or deactivate a user account
#     """
#     def post(self, request, pk):
#         user = get_object_or_404(User, pk=pk)
#
#         # منع المستخدم من تعطيل حسابه الخاص
#         if user == request.user:
#             messages.error(request, _('لا يمكنك تعطيل حسابك الخاص'))
#             return redirect('accounts:admin_user_detail', pk=pk)
#
#         # تبديل حالة النشاط
#         user.is_active = not user.is_active
#         user.save()
#
#         # إنشاء سجل نشاط
#         activity_type = 'account_activated' if user.is_active else 'account_deactivated'
#         description = _('تم تفعيل الحساب') if user.is_active else _('تم تعطيل الحساب')
#
#         UserActivity.objects.create(
#             user=user,
#             activity_type=activity_type,
#             description=description,
#             ip_address=request.META.get('REMOTE_ADDR')
#         )
#
#         message = _('تم تفعيل المستخدم بنجاح') if user.is_active else _('تم تعطيل المستخدم بنجاح')
#         messages.success(request, message)
#
#         return redirect('accounts:admin_user_detail', pk=pk)
#
#
# class UserVerifyView(StaffRequiredMixin, View):
#     """
#     عرض تفعيل البريد الإلكتروني للمستخدم - يتيح للمشرفين تفعيل بريد مستخدم
#     User verify view - allows administrators to verify a user's email
#     """
#     def post(self, request, pk):
#         user = get_object_or_404(User, pk=pk)
#
#         user.is_verified = True
#         user.verification_token = None
#         user.verification_token_expires = None
#         user.save()
#
#         # إنشاء سجل نشاط
#         UserActivity.objects.create(
#             user=user,
#             activity_type='email_verified',
#             description=_('تم تفعيل البريد الإلكتروني بواسطة المشرف'),
#             ip_address=request.META.get('REMOTE_ADDR')
#         )
#
#         messages.success(request, _('تم تفعيل البريد الإلكتروني للمستخدم بنجاح'))
#         return redirect('accounts:admin_user_detail', pk=pk)
#
#
# class RoleListView(StaffRequiredMixin, ListView):
#     """
#     عرض قائمة الأدوار - يعرض قائمة الأدوار للمشرفين
#     Role list view - displays role list for administrators
#     """
#     model = Role
#     template_name = 'accounts/admin/role_list.html'
#     context_object_name = 'roles'
#
#
# class RoleCreateView(SuperUserRequiredMixin, CreateView):
#     """
#     عرض إنشاء دور - يتيح لمديري النظام إنشاء دور جديد
#     Role create view - allows superusers to create a new role
#     """
#     model = Role
#     template_name = 'accounts/admin/role_form.html'
#     form_class = RoleForm
#     success_url = reverse_lazy('accounts:admin_role_list')
#
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         messages.success(self.request, _('تم إنشاء الدور بنجاح'))
#         return response
#
#
# class RoleUpdateView(SuperUserRequiredMixin, UpdateView):
#     """
#     عرض تحديث دور - يتيح لمديري النظام تحديث دور موجود
#     Role update view - allows superusers to update an existing role
#     """
#     model = Role
#     template_name = 'accounts/admin/role_form.html'
#     form_class = RoleForm
#     success_url = reverse_lazy('accounts:admin_role_list')
#
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         messages.success(self.request, _('تم تحديث الدور بنجاح'))
#         return response
#
#
# class RoleDeleteView(SuperUserRequiredMixin, DeleteView):
#     """
#     عرض حذف دور - يتيح لمديري النظام حذف دور موجود
#     Role delete view - allows superusers to delete an existing role
#     """
#     model = Role
#     template_name = 'accounts/admin/role_confirm_delete.html'
#     success_url = reverse_lazy('accounts:admin_role_list')
#
#     def delete(self, request, *args, **kwargs):
#         try:
#             response = super().delete(request, *args, **kwargs)
#             messages.success(self.request, _('تم حذف الدور بنجاح'))
#             return response
#         except Exception as e:
#             messages.error(self.request, _('لا يمكن حذف الدور. يُرجى التأكد من عدم استخدامه من قبل أي مستخدم.'))
#             return redirect('accounts:admin_role_list')
#
#
# class UserActivityListView(StaffRequiredMixin, ListView):
#     """
#     عرض قائمة نشاطات المستخدمين - يعرض سجل نشاطات المستخدمين للمشرفين
#     User activity list view - displays user activity log for administrators
#     """
#     model = UserActivity
#     template_name = 'accounts/admin/user_activity_list.html'
#     context_object_name = 'activities'
#     paginate_by = 50
#
#     def get_queryset(self):
#         queryset = UserActivity.objects.all().order_by('-timestamp')
#
#         # تطبيق الفلاتر
#         user_id = self.request.GET.get('user_id', '')
#         activity_type = self.request.GET.get('activity_type', '')
#         date_from = self.request.GET.get('date_from', '')
#         date_to = self.request.GET.get('date_to', '')
#
#         if user_id:
#             queryset = queryset.filter(user_id=user_id)
#
#         if activity_type:
#             queryset = queryset.filter(activity_type=activity_type)
#
#         if date_from:
#             queryset = queryset.filter(timestamp__gte=date_from)
#
#         if date_to:
#             queryset = queryset.filter(timestamp__lte=date_to)
#
#         return queryset
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         # الحصول على قائمة أنواع النشاطات المميزة للفلترة
#         context['activity_types'] = UserActivity.objects.values_list(
#             'activity_type', flat=True
#         ).distinct()
#
#         # تمرير معلمات البحث
#         context['current_user_id'] = self.request.GET.get('user_id', '')
#         context['current_activity_type'] = self.request.GET.get('activity_type', '')
#         context['current_date_from'] = self.request.GET.get('date_from', '')
#         context['current_date_to'] = self.request.GET.get('date_to', '')
#
#         return context