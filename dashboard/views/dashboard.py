# views/dashboard.py
# العروض الرئيسية للوحة التحكم

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import datetime, timedelta

from accounts.models import User
from products.models import Product, Category, Brand
from orders.models import Order
from cart.models import Cart
from dashboard.forms.accounts import DashboardLoginForm  # استخدام نموذج تسجيل الدخول من accounts
from django.utils.translation import gettext as _


# دالة مساعدة للتحقق من صلاحيات الوصول للوحة التحكم
def has_dashboard_access(user):
    """التحقق من صلاحيات المستخدم للوصول للوحة التحكم"""
    return user.is_authenticated and (user.is_staff or user.is_superuser or (
            hasattr(user, 'can_access_dashboard') and user.can_access_dashboard()))


class DashboardAccessMixin:
    """Mixin للتحقق من صلاحيات الوصول للوحة التحكم"""

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # التحقق من الصلاحيات
        if request.user.is_superuser or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        # التحقق من وجود أي صلاحية على الأقل للدخول للوحة التحكم
        dashboard_permissions = [
            # صلاحيات المنتجات
            'products.view_product', 'products.add_product', 'products.change_product', 'products.delete_product',
            'products.view_category', 'products.view_brand',

            # صلاحيات الطلبات
            'orders.view_order',

            # صلاحيات المستخدمين
            'accounts.view_user',

            # صلاحيات الإعدادات
            'dashboard.view_settings',
        ]

        # إذا كان لدى المستخدم أي من هذه الصلاحيات، اسمح له بالدخول
        for perm in dashboard_permissions:
            if request.user.has_perm(perm):
                return super().dispatch(request, *args, **kwargs)

        # إذا لم يكن لديه أي صلاحية، حوّله لصفحة رفض الوصول
        return redirect('dashboard:dashboard_access_denied')

class DashboardHomeView(DashboardAccessMixin, View):

    def _safe_change(self, current, previous):
        if previous and previous > 0:
            return round(((current - previous) / previous) * 100, 1)
        return 0

    def get(self, request):
        today = timezone.now().date()
        now = timezone.now()

        completed_statuses = ['confirmed', 'processing', 'closed']

        # --- Users ---
        total_users = User.objects.count()
        staff_count = User.objects.filter(is_staff=True).count()
        new_users_month = User.objects.filter(date_joined__date__gte=today - timedelta(days=30)).count()

        # --- Products ---
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        active_products_percent = round((active_products / total_products * 100), 1) if total_products else 0

        in_stock_count = Product.objects.filter(is_active=True, stock_quantity__gt=5).count()
        low_stock_count = Product.objects.filter(is_active=True, stock_quantity__gt=0, stock_quantity__lte=5).count()
        out_of_stock_count = Product.objects.filter(is_active=True, stock_quantity=0).count()
        stock_total = in_stock_count + low_stock_count + out_of_stock_count or 1
        in_stock_percent = round(in_stock_count / stock_total * 100, 1)
        low_stock_percent = round(low_stock_count / stock_total * 100, 1)
        out_of_stock_percent = round(out_of_stock_count / stock_total * 100, 1)

        # --- Orders ---
        total_orders = Order.objects.count()
        recent_orders = Order.objects.filter(created_at__date__gte=today - timedelta(days=30)).count()
        prev_month_orders = Order.objects.filter(
            created_at__date__gte=today - timedelta(days=60),
            created_at__date__lt=today - timedelta(days=30),
        ).count()
        recent_orders_change = self._safe_change(recent_orders, prev_month_orders)

        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        shipped_orders = Order.objects.filter(status='confirmed').count()
        delivered_orders = Order.objects.filter(status='closed').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()

        # --- Total Sales ---
        total_sales = Order.objects.filter(
            status__in=completed_statuses
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        # --- Monthly sales + change ---
        this_month_start = today.replace(day=1)
        monthly_sales = Order.objects.filter(
            created_at__date__gte=this_month_start,
            status__in=completed_statuses,
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        prev_month_end = this_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        prev_monthly_sales = Order.objects.filter(
            created_at__date__gte=prev_month_start,
            created_at__date__lte=prev_month_end,
            status__in=completed_statuses,
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        monthly_sales_change = self._safe_change(float(monthly_sales), float(prev_monthly_sales))

        # --- Daily revenue + change ---
        daily_revenue = Order.objects.filter(
            created_at__date=today,
            status__in=completed_statuses,
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        yesterday_revenue = Order.objects.filter(
            created_at__date=today - timedelta(days=1),
            status__in=completed_statuses,
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        daily_revenue_change = self._safe_change(float(daily_revenue), float(yesterday_revenue))

        # --- Weekly revenue + change ---
        week_start = today - timedelta(days=today.weekday())
        weekly_revenue = Order.objects.filter(
            created_at__date__gte=week_start,
            status__in=completed_statuses,
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        prev_week_start = week_start - timedelta(days=7)
        prev_weekly_revenue = Order.objects.filter(
            created_at__date__gte=prev_week_start,
            created_at__date__lt=week_start,
            status__in=completed_statuses,
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        weekly_revenue_change = self._safe_change(float(weekly_revenue), float(prev_weekly_revenue))

        monthly_revenue = monthly_sales
        monthly_revenue_change = monthly_sales_change

        # --- Average order value + change ---
        avg_data = Order.objects.filter(
            created_at__date__gte=this_month_start,
            status__in=completed_statuses,
        ).aggregate(avg=Avg('grand_total'))
        average_order_value = avg_data['avg'] or 0

        prev_avg_data = Order.objects.filter(
            created_at__date__gte=prev_month_start,
            created_at__date__lte=prev_month_end,
            status__in=completed_statuses,
        ).aggregate(avg=Avg('grand_total'))
        prev_avg = prev_avg_data['avg'] or 0
        average_order_change = self._safe_change(float(average_order_value), float(prev_avg))

        # --- Lead requests ---
        from chatbot.models import LeadRequest
        pending_leads = LeadRequest.objects.filter(status='pending').count()

        # --- Top data ---
        latest_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
        latest_users = User.objects.order_by('-date_joined')[:5]
        top_products = Product.objects.filter(is_active=True).order_by('-sales_count')[:5]

        # --- Today's orders ---
        today_orders = Order.objects.filter(created_at__date=today).count()

        # --- Low stock products ---
        low_stock_products = Product.objects.filter(
            is_active=True, stock_quantity__gt=0, stock_quantity__lte=5
        ).order_by('stock_quantity')[:5]

        # --- Recent lead requests ---
        recent_leads = LeadRequest.objects.select_related('assigned_to').order_by('-created_at')[:5]
        total_leads = LeadRequest.objects.count()
        leads_this_week = LeadRequest.objects.filter(created_at__date__gte=today - timedelta(days=7)).count()

        # --- Lead requests by status ---
        lead_pending = LeadRequest.objects.filter(status='pending').count()
        lead_contacted = LeadRequest.objects.filter(status='contacted').count()
        lead_in_progress = LeadRequest.objects.filter(status='in_progress').count()
        lead_completed = LeadRequest.objects.filter(status='completed').count()
        lead_cancelled = LeadRequest.objects.filter(status='cancelled').count()

        # --- New users chart: last 7 days ---
        new_users_labels = []
        new_users_data = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            count = User.objects.filter(date_joined__date=d).count()
            new_users_labels.append(d.strftime('%m/%d'))
            new_users_data.append(count)

        # --- Chart data: last 6 months ---
        labels = []
        sales_data = []
        orders_data = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            m_start = datetime(y, m, 1).date()
            m_end = datetime(y + (1 if m == 12 else 0), (m % 12) + 1, 1).date() - timedelta(days=1)
            m_sales = Order.objects.filter(
                created_at__date__gte=m_start,
                created_at__date__lte=m_end,
                status__in=completed_statuses,
            ).aggregate(total=Sum('grand_total'))['total'] or 0
            m_orders = Order.objects.filter(
                created_at__date__gte=m_start,
                created_at__date__lte=m_end,
            ).count()
            labels.append(m_start.strftime('%b'))
            sales_data.append(float(m_sales))
            orders_data.append(m_orders)

        context = {
            'total_users': total_users,
            'staff_count': staff_count,
            'new_users_month': new_users_month,
            'total_products': total_products,
            'active_products': active_products,
            'active_products_percent': active_products_percent,
            'total_orders': total_orders,
            'recent_orders': recent_orders,
            'recent_orders_change': recent_orders_change,
            'total_sales': total_sales,
            'monthly_sales': monthly_sales,
            'monthly_sales_change': monthly_sales_change,
            'daily_revenue': daily_revenue,
            'daily_revenue_change': daily_revenue_change,
            'weekly_revenue': weekly_revenue,
            'weekly_revenue_change': weekly_revenue_change,
            'monthly_revenue': monthly_revenue,
            'monthly_revenue_change': monthly_revenue_change,
            'average_order_value': average_order_value,
            'average_order_change': average_order_change,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'shipped_orders': shipped_orders,
            'delivered_orders': delivered_orders,
            'cancelled_orders': cancelled_orders,
            'in_stock_count': in_stock_count,
            'in_stock_percent': in_stock_percent,
            'low_stock_count': low_stock_count,
            'low_stock_percent': low_stock_percent,
            'out_of_stock_count': out_of_stock_count,
            'out_of_stock_percent': out_of_stock_percent,
            'pending_leads': pending_leads,
            'latest_orders': latest_orders,
            'latest_users': latest_users,
            'top_products': top_products,
            'today_orders': today_orders,
            'low_stock_products': low_stock_products,
            'recent_leads': recent_leads,
            'total_leads': total_leads,
            'leads_this_week': leads_this_week,
            'lead_pending': lead_pending,
            'lead_contacted': lead_contacted,
            'lead_in_progress': lead_in_progress,
            'lead_completed': lead_completed,
            'lead_cancelled': lead_cancelled,
            'new_users_labels': new_users_labels,
            'new_users_data': new_users_data,
            'labels': labels,
            'sales_data': sales_data,
            'orders_data': orders_data,
        }

        return render(request, 'dashboard/index.html', context)


# صفحة تسجيل الدخول للوحة التحكم
def dashboard_login(request):
    """عرض صفحة تسجيل الدخول للوحة التحكم"""
    if request.user.is_authenticated:
        if has_dashboard_access(request.user):
            return redirect('dashboard:dashboard_home')
        else:
            return redirect('dashboard:dashboard_access_denied')

    # استخراج عنوان التوجيه بعد تسجيل الدخول
    next_url = request.GET.get('next', '')

    # معالجة نموذج تسجيل الدخول
    if request.method == 'POST':
        form = DashboardLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me', False)

            # محاولة تسجيل الدخول
            user = authenticate(username=username, password=password)
            if user is not None:
                # التحقق من صلاحية الوصول للوحة التحكم
                if has_dashboard_access(user):
                    login(request, user)

                    # تعيين مدة انتهاء الجلسة إذا لم يتم اختيار "تذكرني"
                    if not remember_me:
                        request.session.set_expiry(0)  # تنتهي الجلسة عند إغلاق المتصفح
                    else:
                        # تعيين مدة طويلة للجلسة (2 أسبوع)
                        request.session.set_expiry(1209600)

                    # التوجيه بعد تسجيل الدخول
                    redirect_url = request.POST.get('next', '')
                    if redirect_url and redirect_url.startswith('/dashboard/'):
                        return redirect(redirect_url)
                    else:
                        return redirect('dashboard:dashboard_home')
                else:
                    # المستخدم ليس لديه صلاحية الوصول للوحة التحكم
                    messages.error(request, _('ليس لديك صلاحية الوصول إلى لوحة التحكم.'))
                    return redirect('dashboard:dashboard_access_denied')
            else:
                # فشل تسجيل الدخول
                messages.error(request, _('اسم المستخدم أو كلمة المرور غير صحيحة.'))
    else:
        # إنشاء نموذج فارغ
        form = DashboardLoginForm()

    # تمرير المتغيرات إلى القالب
    context = {
        'form': form,
        'next_url': next_url
    }

    return render(request, 'dashboard/auth/login.html', context)

# صفحة رفض الوصول
def dashboard_access_denied(request):
    """عرض صفحة رفض الوصول للوحة التحكم"""
    return render(request, 'dashboard/auth/access_denied.html')


# في dashboard/views/dashboard.py
def dashboard_logout(request):
    logout(request)
    messages.success(request, _('تم تسجيل الخروج بنجاح'))
    return redirect('dashboard:dashboard_login')