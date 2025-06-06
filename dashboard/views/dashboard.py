# views/dashboard.py
# العروض الرئيسية للوحة التحكم

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from accounts.models import User
from products.models import Product, Category, Brand
from orders.models import Order
from cart.models import Cart


# دالة مساعدة للتحقق من صلاحيات الوصول للوحة التحكم
def has_dashboard_access(user):
    """التحقق من صلاحيات المستخدم للوصول للوحة التحكم"""
    return user.is_authenticated and (user.is_staff or user.is_superuser or (
                hasattr(user, 'can_access_dashboard') and user.can_access_dashboard()))


# Mixin للتحقق من صلاحيات الوصول للوحة التحكم
class DashboardAccessMixin:
    """Mixin للتحقق من صلاحيات الوصول للوحة التحكم"""

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not has_dashboard_access(request.user):
            return redirect('dashboard_login')
        return super().dispatch(request, *args, **kwargs)


# الصفحة الرئيسية للوحة التحكم
class DashboardHomeView(DashboardAccessMixin, View):
    """عرض الصفحة الرئيسية للوحة التحكم"""

    def get(self, request):
        # الإحصائيات العامة
        today = timezone.now().date()
        last_month = today - timedelta(days=30)

        # إحصائيات المستخدمين
        total_users = User.objects.count()
        new_users_month = User.objects.filter(date_joined__gte=last_month).count()

        # إحصائيات المنتجات
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()

        # إحصائيات الطلبات
        total_orders = Order.objects.count()
        recent_orders = Order.objects.filter(created_at__gte=last_month).count()

        # إجمالي المبيعات
        total_sales = Order.objects.filter(
            status__in=['delivered', 'shipped']
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        # مبيعات الشهر الحالي
        monthly_sales = Order.objects.filter(
            created_at__gte=last_month,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        # أحدث الطلبات
        latest_orders = Order.objects.order_by('-created_at')[:5]

        # أحدث المستخدمين
        latest_users = User.objects.order_by('-date_joined')[:5]

        # أكثر المنتجات مبيعاً
        top_products = Product.objects.order_by('-sales_count')[:5]

        # بيانات للرسوم البيانية - المبيعات الشهرية
        last_6_months = []
        labels = []
        sales_data = []

        for i in range(5, -1, -1):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1

            month_start = datetime(year, month, 1).date()
            if month == 12:
                month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)

            month_sales = Order.objects.filter(
                created_at__date__gte=month_start,
                created_at__date__lte=month_end,
                status__in=['delivered', 'shipped', 'processing']
            ).aggregate(total=Sum('grand_total'))['total'] or 0

            last_6_months.append({
                'month': month_start.strftime('%B'),
                'sales': month_sales
            })
            labels.append(month_start.strftime('%b'))
            sales_data.append(float(month_sales))

        context = {
            'total_users': total_users,
            'new_users_month': new_users_month,
            'total_products': total_products,
            'active_products': active_products,
            'total_orders': total_orders,
            'recent_orders': recent_orders,
            'total_sales': total_sales,
            'monthly_sales': monthly_sales,
            'latest_orders': latest_orders,
            'latest_users': latest_users,
            'top_products': top_products,
            'labels': labels,
            'sales_data': sales_data,
        }

        return render(request, 'dashboard/index.html', context)


# صفحة تسجيل الدخول للوحة التحكم
def dashboard_login(request):
    """عرض صفحة تسجيل الدخول للوحة التحكم"""
    if request.user.is_authenticated:
        if has_dashboard_access(request.user):
            return redirect('dashboard_home')
        else:
            return redirect('dashboard_access_denied')

    return render(request, 'dashboard/login.html')


# صفحة رفض الوصول
def dashboard_access_denied(request):
    """عرض صفحة رفض الوصول للوحة التحكم"""
    return render(request, 'dashboard/access_denied.html')