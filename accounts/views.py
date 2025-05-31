from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, DetailView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from .models import User, UserActivity
from orders.models import Order

class RegisterView(CreateView):
    """
    عرض التسجيل - يتيح للمستخدمين التسجيل في الموقع
    Register view - allows users to register on the site
    """
    model = User
    template_name = 'accounts/register.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'password']
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        # تعيين كلمة المرور بشكل آمن - Set password securely
        user = form.save(commit=False)
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()

        # إنشاء سجل نشاط - Create activity log
        UserActivity.objects.create(
            user=user,
            activity_type='registration',
            description=_('تم التسجيل في الموقع'),
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

        messages.success(self.request, _('تم التسجيل بنجاح، يمكنك الآن تسجيل الدخول.'))
        return super().form_valid(form)

class LoginView(View):
    """
    عرض تسجيل الدخول - يتيح للمستخدمين تسجيل الدخول
    Login view - allows users to log in
    """
    template_name = 'accounts/login.html'

    def get(self, request):
        # إذا كان المستخدم مسجل الدخول بالفعل، قم بتحويله إلى الصفحة الرئيسية
        # If the user is already logged in, redirect to home page
        if request.user.is_authenticated:
            return redirect('core:home')

        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)

            # إنشاء سجل نشاط - Create activity log
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                description=_('تسجيل الدخول'),
                ip_address=request.META.get('REMOTE_ADDR')
            )

            # التحقق مما إذا كان هناك عنوان URL للتحويل إليه - Check if there's a redirect URL
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            return redirect('core:home')
        else:
            messages.error(request, _('اسم المستخدم أو كلمة المرور غير صحيحة'))
            return render(request, self.template_name)

class LogoutView(View):
    """
    عرض تسجيل الخروج - يتيح للمستخدمين تسجيل الخروج
    Logout view - allows users to log out
    """
    def get(self, request):
        if request.user.is_authenticated:
            # إنشاء سجل نشاط - Create activity log
            UserActivity.objects.create(
                user=request.user,
                activity_type='logout',
                description=_('تسجيل الخروج'),
                ip_address=request.META.get('REMOTE_ADDR')
            )

            logout(request)

        return redirect('core:home')

class ProfileView(LoginRequiredMixin, UpdateView):
    """
    عرض الملف الشخصي - يتيح للمستخدمين عرض وتحديث معلوماتهم الشخصية
    Profile view - allows users to view and update their personal information
    """
    model = User
    template_name = 'accounts/profile.html'
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'avatar', 'address']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث الملف الشخصي بنجاح'))

        # إنشاء سجل نشاط - Create activity log
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='profile_update',
            description=_('تحديث الملف الشخصي'),
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

        return super().form_valid(form)

class OrderHistoryView(LoginRequiredMixin, ListView):
    """
    عرض سجل الطلبات - يعرض سجل طلبات المستخدم
    Order history view - displays the user's order history
    """
    model = Order
    template_name = 'accounts/order_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    عرض تفاصيل الطلب - يعرض تفاصيل طلب معين
    Order detail view - displays details of a specific order
    """
    model = Order
    template_name = 'accounts/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        # التأكد من أن المستخدم يمكنه فقط رؤية طلباته الخاصة
        # Ensure the user can only see their own orders
        return Order.objects.filter(user=self.request.user)