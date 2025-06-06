# dashboard/views/reports.py
"""
عروض التقارير والإحصائيات - يتضمن كافة العروض المتعلقة بتقارير النظام المختلفة
"""

from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F, Max, Min
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from products.models import Product, Category, Brand, ProductVariant
from orders.models import Order, OrderItem
from payment.models import Payment, Refund, Transaction
from dashboard.mixins import DashboardAccessMixin

import csv
import xlwt
import json
from datetime import datetime, timedelta
from decimal import Decimal

User = get_user_model()


class ReportIndexView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    صفحة فهرس التقارير الرئيسية - تعرض روابط لمختلف أنواع التقارير المتاحة
    """
    template_name = 'dashboard/reports/index.html'
    permission_required = 'dashboard.view_reports'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة إحصائيات عامة للعرض في صفحة الفهرس
        context['total_orders'] = Order.objects.count()
        context['total_revenue'] = Order.objects.filter(
            status__in=['completed', 'delivered']
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        context['total_customers'] = User.objects.filter(
            is_staff=False, is_superuser=False
        ).count()

        context['total_products'] = Product.objects.filter(
            is_active=True, status='published'
        ).count()

        # روابط ووصف للتقارير المتاحة
        context['reports'] = [
            {
                'title': _('تقارير المبيعات'),
                'icon': 'shopping-cart',
                'description': _('عرض تفاصيل المبيعات والطلبات حسب الفترة الزمنية والمنتجات'),
                'url': 'dashboard:sales_report',
                'permission': 'dashboard.view_sales_report',
            },
            {
                'title': _('تقارير المنتجات'),
                'icon': 'package',
                'description': _('تحليل أداء المنتجات ومبيعاتها ومخزونها'),
                'url': 'dashboard:product_report',
                'permission': 'dashboard.view_product_report',
            },
            {
                'title': _('تقارير العملاء'),
                'icon': 'users',
                'description': _('تحليل بيانات العملاء وسلوكهم الشرائي'),
                'url': 'dashboard:customer_report',
                'permission': 'dashboard.view_customer_report',
            },
            {
                'title': _('تقارير المخزون'),
                'icon': 'layers',
                'description': _('متابعة حالة المخزون والمنتجات منخفضة المخزون'),
                'url': 'dashboard:inventory_report',
                'permission': 'dashboard.view_inventory_report',
            },
            {
                'title': _('تقارير الإيرادات'),
                'icon': 'dollar-sign',
                'description': _('تحليل الإيرادات والأرباح والمصروفات'),
                'url': 'dashboard:revenue_report',
                'permission': 'dashboard.view_revenue_report',
            },
            {
                'title': _('تقارير الضرائب'),
                'icon': 'file-text',
                'description': _('تقارير الضرائب والرسوم المحصلة'),
                'url': 'dashboard:tax_report',
                'permission': 'dashboard.view_tax_report',
            },
            {
                'title': _('تصدير التقارير'),
                'icon': 'download',
                'description': _('تصدير التقارير بتنسيقات مختلفة'),
                'url': 'dashboard:export_report',
                'permission': 'dashboard.export_reports',
            },
        ]

        # تحقق من صلاحيات المستخدم لعرض روابط التقارير المناسبة فقط
        user = self.request.user
        available_reports = []

        for report in context['reports']:
            if user.has_perm(report['permission']) or user.is_superuser:
                available_reports.append(report)

        context['available_reports'] = available_reports

        return context


class SalesReportView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    تقارير المبيعات - تحليل المبيعات حسب الفترة الزمنية والمنتجات
    """
    template_name = 'dashboard/reports/sales_report.html'
    permission_required = 'dashboard.view_sales_report'

    def get_date_range(self):
        """استخراج نطاق التاريخ من المعلمات المرسلة"""
        range_type = self.request.GET.get('range', 'week')
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if range_type == 'today':
            start_date = today
            end_date = today.replace(hour=23, minute=59, second=59)
        elif range_type == 'yesterday':
            start_date = today - timedelta(days=1)
            end_date = start_date.replace(hour=23, minute=59, second=59)
        elif range_type == 'week':
            # الأسبوع الحالي
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        elif range_type == 'month':
            # الشهر الحالي
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        elif range_type == 'year':
            # السنة الحالية
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59)
        elif range_type == 'custom':
            # نطاق مخصص
            try:
                start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)
                end_date = datetime.strptime(self.request.GET.get('end_date'), '%Y-%m-%d')
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
            except (ValueError, TypeError):
                # في حالة حدوث خطأ، استخدام الأسبوع الحالي كقيمة افتراضية
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        else:
            # القيمة الافتراضية هي الأسبوع الحالي
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)

        return start_date, end_date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على نطاق التاريخ
        start_date, end_date = self.get_date_range()
        context['start_date'] = start_date
        context['end_date'] = end_date
        context['range_type'] = self.request.GET.get('range', 'week')

        # استعلام الطلبات للفترة المحددة
        orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)

        # إضافة فلترة حسب الحالة إذا تم تحديدها
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            orders = orders.filter(status=status_filter)

        # الإحصائيات الأساسية
        context['total_orders'] = orders.count()
        context['total_revenue'] = orders.aggregate(total=Sum('grand_total'))['total'] or 0
        context['avg_order_value'] = orders.aggregate(avg=Avg('grand_total'))['avg'] or 0

        # تحليل المبيعات حسب الحالة
        status_stats = orders.values('status').annotate(
            count=Count('id'),
            total=Sum('grand_total')
        ).order_by('status')
        context['status_stats'] = status_stats

        # تحليل المبيعات اليومية
        daily_sales = orders.filter(
            status__in=['completed', 'delivered', 'shipped']
        ).values('created_at__date').annotate(
            date=F('created_at__date'),
            count=Count('id'),
            total=Sum('grand_total')
        ).order_by('date')
        context['daily_sales'] = daily_sales

        # أعلى المنتجات مبيعًا
        top_products = OrderItem.objects.filter(
            order__in=orders
        ).values('product_name').annotate(
            count=Sum('quantity'),
            total=Sum('total_price')
        ).order_by('-count')[:10]
        context['top_products'] = top_products

        # أعلى الفئات مبيعًا
        top_categories = OrderItem.objects.filter(
            order__in=orders
        ).values('product__category__name').annotate(
            count=Count('id'),
            total=Sum('total_price')
        ).order_by('-total')[:5]
        context['top_categories'] = top_categories

        # قائمة أحدث الطلبات
        context['recent_orders'] = orders.order_by('-created_at')[:20]

        # قائمة حالات الطلبات للفلترة
        context['order_statuses'] = dict(Order.STATUS_CHOICES)
        context['current_status'] = status_filter

        return context


class ProductReportView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    تقارير المنتجات - تحليل أداء المنتجات ومبيعاتها ومخزونها
    """
    template_name = 'dashboard/reports/product_report.html'
    permission_required = 'dashboard.view_product_report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على نطاق التاريخ (الشهر الحالي افتراضيًا)
        today = timezone.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # تغيير نطاق التاريخ إذا تم تحديده
        date_range = self.request.GET.get('range', 'month')
        if date_range == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        elif date_range == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59)
        elif date_range == 'custom':
            try:
                start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)
                end_date = datetime.strptime(self.request.GET.get('end_date'), '%Y-%m-%d')
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
            except (ValueError, TypeError):
                pass

        context['start_date'] = start_date
        context['end_date'] = end_date
        context['range_type'] = date_range

        # فلترة حسب الفئة
        category_id = self.request.GET.get('category', '')
        category_filter = None
        if category_id:
            try:
                category_filter = Category.objects.get(id=category_id)
            except (Category.DoesNotExist, ValueError):
                pass
        context['category_filter'] = category_filter

        # قائمة الفئات للفلترة
        context['categories'] = Category.objects.filter(is_active=True)

        # استعلام المنتجات
        products = Product.objects.filter(is_active=True)
        if category_filter:
            products = products.filter(category=category_filter)

        # الإحصائيات الأساسية
        context['total_products'] = products.count()
        context['active_products'] = products.filter(status='published').count()
        context['out_of_stock'] = products.filter(stock_quantity__lte=0).count()
        context['low_stock'] = products.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F('min_stock_level')
        ).count()

        # أكثر المنتجات مشاهدة
        context['most_viewed'] = products.order_by('-views_count')[:10]

        # أكثر المنتجات مبيعًا
        context['best_sellers'] = products.order_by('-sales_count')[:10]

        # استعلام المبيعات للفترة المحددة
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status__in=['completed', 'delivered', 'shipped']
        )

        # أعلى المنتجات مبيعًا خلال الفترة
        top_selling = OrderItem.objects.filter(
            order__in=orders
        ).values('product_id', 'product_name').annotate(
            count=Sum('quantity'),
            revenue=Sum('total_price')
        ).order_by('-count')[:10]
        context['top_selling'] = top_selling

        # المنتجات التي لم تباع
        sold_product_ids = OrderItem.objects.filter(
            order__in=orders
        ).values_list('product_id', flat=True).distinct()
        context['unsold_products'] = products.exclude(
            id__in=sold_product_ids
        ).order_by('name')[:20]

        # المنتجات التي تحتاج إلى تجديد المخزون
        context['needs_restocking'] = products.filter(
            stock_quantity__lte=F('min_stock_level')
        ).order_by('stock_quantity')[:20]

        return context


class CustomerReportView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    تقارير العملاء - تحليل بيانات العملاء وسلوكهم الشرائي
    """
    template_name = 'dashboard/reports/customer_report.html'
    permission_required = 'dashboard.view_customer_report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الإحصائيات الأساسية
        customers = User.objects.filter(is_staff=False, is_superuser=False)

        context['total_customers'] = customers.count()
        context['verified_customers'] = customers.filter(is_verified=True).count()
        context['customers_with_orders'] = User.objects.filter(
            orders__isnull=False
        ).distinct().count()

        # العملاء حسب تاريخ التسجيل
        today = timezone.now()

        context['new_today'] = customers.filter(
            date_joined__date=today.date()
        ).count()

        context['new_this_week'] = customers.filter(
            date_joined__gte=today - timedelta(days=7)
        ).count()

        context['new_this_month'] = customers.filter(
            date_joined__gte=today.replace(day=1)
        ).count()

        # أفضل العملاء (الأكثر إنفاقًا)
        top_customers = customers.annotate(
            total_spent=Sum('orders__grand_total'),
            orders_count=Count('orders')
        ).filter(
            total_spent__isnull=False
        ).order_by('-total_spent')[:20]

        context['top_customers'] = top_customers

        # العملاء الأكثر نشاطًا (الأكثر طلبات)
        most_active = customers.annotate(
            orders_count=Count('orders')
        ).filter(
            orders_count__gt=0
        ).order_by('-orders_count')[:20]

        context['most_active'] = most_active

        # العملاء الجدد
        context['new_customers'] = customers.order_by('-date_joined')[:20]

        # العملاء غير النشطين (لم يقوموا بالشراء منذ فترة)
        threshold_date = today - timedelta(days=90)  # 3 أشهر
        inactive_customers = customers.filter(
            Q(orders__isnull=True) |
            Q(orders__created_at__lt=threshold_date)
        ).distinct()

        context['inactive_customers_count'] = inactive_customers.count()
        context['inactive_customers'] = inactive_customers.order_by('date_joined')[:20]

        # متوسط قيمة الطلب حسب العميل
        context['avg_order_value'] = Order.objects.filter(
            status__in=['completed', 'delivered']
        ).aggregate(avg=Avg('grand_total'))['avg'] or 0

        # توزيع العملاء حسب الدولة
        countries = customers.exclude(country='').values('country').annotate(
            count=Count('id')
        ).order_by('-count')

        context['customer_countries'] = countries

        return context


class InventoryReportView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    تقارير المخزون - متابعة حالة المخزون والمنتجات منخفضة المخزون
    """
    template_name = 'dashboard/reports/inventory_report.html'
    permission_required = 'dashboard.view_inventory_report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # فلترة حسب الفئة
        category_id = self.request.GET.get('category', '')
        category_filter = None
        if category_id:
            try:
                category_filter = Category.objects.get(id=category_id)
            except (Category.DoesNotExist, ValueError):
                pass

        # فلترة حسب العلامة التجارية
        brand_id = self.request.GET.get('brand', '')
        brand_filter = None
        if brand_id:
            try:
                brand_filter = Brand.objects.get(id=brand_id)
            except (Brand.DoesNotExist, ValueError):
                pass

        # استعلام المنتجات
        products = Product.objects.filter(is_active=True)

        if category_filter:
            products = products.filter(category=category_filter)

        if brand_filter:
            products = products.filter(brand=brand_filter)

        # فلترة حسب حالة المخزون
        stock_status = self.request.GET.get('stock_status', '')
        if stock_status == 'out_of_stock':
            products = products.filter(stock_quantity__lte=0)
        elif stock_status == 'low_stock':
            products = products.filter(
                stock_quantity__gt=0,
                stock_quantity__lte=F('min_stock_level')
            )
        elif stock_status == 'in_stock':
            products = products.filter(
                stock_quantity__gt=F('min_stock_level')
            )

        # الإحصائيات الأساسية
        context['total_products'] = products.count()
        context['out_of_stock_count'] = products.filter(stock_quantity__lte=0).count()
        context['low_stock_count'] = products.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F('min_stock_level')
        ).count()
        context['in_stock_count'] = products.filter(
            stock_quantity__gt=F('min_stock_level')
        ).count()

        # قيمة المخزون الإجمالية
        inventory_value = products.annotate(
            value=F('stock_quantity') * F('base_price')
        ).aggregate(total=Sum('value'))['total'] or 0
        context['inventory_value'] = inventory_value

        # قائمة المنتجات للعرض
        paginate_by = 50
        context['products'] = products.order_by('category__name', 'name')[:paginate_by]

        # المنتجات المنخفضة المخزون
        context['low_stock_products'] = products.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F('min_stock_level')
        ).order_by('stock_quantity')[:20]

        # المنتجات المنتهية من المخزون
        context['out_of_stock_products'] = products.filter(
            stock_quantity__lte=0
        ).order_by('name')[:20]

        # المنتجات الأكثر دورانًا (الأكثر مبيعًا بالنسبة للمخزون)
        top_selling = products.filter(
            stock_quantity__gt=0
        ).annotate(
            turnover_ratio=F('sales_count') / F('stock_quantity')
        ).order_by('-turnover_ratio')[:20]
        context['top_selling'] = top_selling

        # قوائم للفلترة
        context['categories'] = Category.objects.filter(is_active=True)
        context['brands'] = Brand.objects.filter(is_active=True)
        context['current_category'] = category_filter
        context['current_brand'] = brand_filter
        context['current_stock_status'] = stock_status

        return context


class RevenueReportView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    تقارير الإيرادات - تحليل الإيرادات والأرباح والمصروفات
    """
    template_name = 'dashboard/reports/revenue_report.html'
    permission_required = 'dashboard.view_revenue_report'

    def get_date_range(self):
        """استخراج نطاق التاريخ من المعلمات المرسلة"""
        range_type = self.request.GET.get('range', 'month')
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if range_type == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        elif range_type == 'month':
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        elif range_type == 'quarter':
            quarter_month = (today.month - 1) // 3 * 3 + 1
            start_date = today.replace(month=quarter_month, day=1)
            if quarter_month + 3 > 12:
                end_date = today.replace(year=today.year + 1, month=(quarter_month + 3) % 12, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=quarter_month + 3, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        elif range_type == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59)
        elif range_type == 'custom':
            try:
                start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)
                end_date = datetime.strptime(self.request.GET.get('end_date'), '%Y-%m-%d')
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
            except (ValueError, TypeError):
                # في حالة حدوث خطأ، استخدام الشهر الحالي كقيمة افتراضية
                start_date = today.replace(day=1)
                if today.month == 12:
                    end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59)
        else:
            # القيمة الافتراضية هي الشهر الحالي
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)

        return start_date, end_date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على نطاق التاريخ
        start_date, end_date = self.get_date_range()
        context['start_date'] = start_date
        context['end_date'] = end_date
        context['range_type'] = self.request.GET.get('range', 'month')

        # استعلام الطلبات للفترة المحددة
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # إجمالي الإيرادات (جميع الطلبات)
        total_revenue = orders.aggregate(total=Sum('grand_total'))['total'] or 0
        context['total_revenue'] = total_revenue

        # إيرادات الطلبات المكتملة
        completed_revenue = orders.filter(
            status__in=['completed', 'delivered']
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        context['completed_revenue'] = completed_revenue

        # عدد الطلبات
        context['total_orders'] = orders.count()
        context['completed_orders'] = orders.filter(
            status__in=['completed', 'delivered']
        ).count()

        # متوسط قيمة الطلب
        context['avg_order_value'] = (completed_revenue / context['completed_orders']) if context[
                                                                                              'completed_orders'] > 0 else 0

        # تحليل المبيعات حسب طرق الدفع
        payment_methods = orders.filter(
            status__in=['completed', 'delivered']
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('grand_total')
        ).order_by('-total')
        context['payment_methods'] = payment_methods

        # تحليل المبيعات حسب اليوم
        daily_revenue = orders.filter(
            status__in=['completed', 'delivered']
        ).values('created_at__date').annotate(
            date=F('created_at__date'),
            count=Count('id'),
            total=Sum('grand_total')
        ).order_by('date')
        context['daily_revenue'] = daily_revenue

        # تكاليف الشحن
        shipping_revenue = orders.filter(
            status__in=['completed', 'delivered']
        ).aggregate(total=Sum('shipping_cost'))['total'] or 0
        context['shipping_revenue'] = shipping_revenue

        # الضرائب المحصلة
        tax_revenue = orders.filter(
            status__in=['completed', 'delivered']
        ).aggregate(total=Sum('tax_amount'))['total'] or 0
        context['tax_revenue'] = tax_revenue

        # الخصومات
        discount_total = orders.filter(
            status__in=['completed', 'delivered']
        ).aggregate(total=Sum('discount_amount'))['total'] or 0
        context['discount_total'] = discount_total

        # المبالغ المستردة
        refunds = Refund.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status='completed'
        )
        refund_amount = refunds.aggregate(total=Sum('amount'))['total'] or 0
        context['refund_amount'] = refund_amount

        # صافي الإيرادات بعد الاستردادات
        context['net_revenue'] = completed_revenue - refund_amount

        # معدل استرداد الأموال
        context['refund_rate'] = (refund_amount / completed_revenue * 100) if completed_revenue > 0 else 0

        # الإيرادات حسب الفئة
        category_revenue = OrderItem.objects.filter(
            order__in=orders.filter(status__in=['completed', 'delivered']),
            product__isnull=False
        ).values('product__category__name').annotate(
            count=Count('id'),
            total=Sum('total_price')
        ).order_by('-total')
        context['category_revenue'] = category_revenue

        return context


class TaxReportView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    تقارير الضرائب - تقارير الضرائب والرسوم المحصلة
    """
    template_name = 'dashboard/reports/tax_report.html'
    permission_required = 'dashboard.view_tax_report'

    def get_date_range(self):
        """استخراج نطاق التاريخ من المعلمات المرسلة"""
        range_type = self.request.GET.get('range', 'month')
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if range_type == 'month':
            # الشهر الحالي
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        elif range_type == 'quarter':
            # الربع الحالي
            quarter_month = (today.month - 1) // 3 * 3 + 1
            start_date = today.replace(month=quarter_month, day=1)
            if quarter_month + 3 > 12:
                end_date = today.replace(year=today.year + 1, month=(quarter_month + 3) % 12, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=quarter_month + 3, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        elif range_type == 'year':
            # السنة الحالية
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31, hour=23, minute=59, second=59)
        elif range_type == 'custom':
            # نطاق مخصص
            try:
                start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d')
                start_date = timezone.make_aware(start_date)
                end_date = datetime.strptime(self.request.GET.get('end_date'), '%Y-%m-%d')
                end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
            except (ValueError, TypeError):
                # في حالة حدوث خطأ، استخدام الشهر الحالي كقيمة افتراضية
                start_date = today.replace(day=1)
                if today.month == 12:
                    end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59)
        else:
            # القيمة الافتراضية هي الشهر الحالي
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)

        return start_date, end_date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على نطاق التاريخ
        start_date, end_date = self.get_date_range()
        context['start_date'] = start_date
        context['end_date'] = end_date
        context['range_type'] = self.request.GET.get('range', 'month')

        # استعلام الطلبات المكتملة للفترة المحددة
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status__in=['completed', 'delivered', 'shipped']
        )

        # إحصائيات الضرائب الإجمالية
        total_sales = orders.aggregate(total=Sum('grand_total'))['total'] or 0
        total_tax = orders.aggregate(total=Sum('tax_amount'))['total'] or 0

        context['total_sales'] = total_sales
        context['total_tax'] = total_tax
        context['average_tax_rate'] = (total_tax / (total_sales - total_tax) * 100) if (
                                                                                                   total_sales - total_tax) > 0 else 0

        # الضرائب حسب اليوم
        daily_tax = orders.values('created_at__date').annotate(
            date=F('created_at__date'),
            sales=Sum('grand_total'),
            tax=Sum('tax_amount')
        ).order_by('date')

        context['daily_tax'] = daily_tax

        # الضرائب حسب البلد/المنطقة
        country_tax = orders.values('shipping_country').annotate(
            country=F('shipping_country'),
            count=Count('id'),
            sales=Sum('grand_total'),
            tax=Sum('tax_amount')
        ).order_by('-tax')

        context['country_tax'] = country_tax

        # الضرائب حسب فئة المنتج
        # هذا يتطلب استعلامًا أكثر تعقيدًا لأن الضرائب مرتبطة بالطلب وليس بالمنتجات المنفردة
        # سنقوم بتقريب نسبة الضريبة من إجمالي المبيعات وتطبيقها على كل فئة

        tax_rate = total_tax / total_sales if total_sales > 0 else 0

        category_sales = OrderItem.objects.filter(
            order__in=orders
        ).values('product__category__name').annotate(
            category=F('product__category__name'),
            sales=Sum('total_price')
        ).order_by('-sales')

        for category in category_sales:
            category['estimated_tax'] = category['sales'] * tax_rate

        context['category_tax'] = category_sales

        # عرض أحدث الطلبات مع الضرائب
        context['recent_orders'] = orders.order_by('-created_at')[:20]

        return context


class ExportReportView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    تصدير التقارير - واجهة لتصدير مختلف التقارير بتنسيقات متعددة
    """
    template_name = 'dashboard/reports/export_report.html'
    permission_required = 'dashboard.export_reports'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # قائمة التقارير المتاحة للتصدير
        context['available_reports'] = [
            {
                'id': 'sales',
                'name': _('تقرير المبيعات'),
                'description': _('تصدير بيانات المبيعات والطلبات'),
                'formats': ['csv', 'excel', 'json'],
            },
            {
                'id': 'products',
                'name': _('تقرير المنتجات'),
                'description': _('تصدير بيانات المنتجات والمخزون'),
                'formats': ['csv', 'excel', 'json'],
            },
            {
                'id': 'customers',
                'name': _('تقرير العملاء'),
                'description': _('تصدير بيانات العملاء وإحصائيات المبيعات'),
                'formats': ['csv', 'excel', 'json'],
            },
            {
                'id': 'inventory',
                'name': _('تقرير المخزون'),
                'description': _('تصدير بيانات المخزون الحالي والمنتجات منخفضة المخزون'),
                'formats': ['csv', 'excel', 'json'],
            },
            {
                'id': 'revenue',
                'name': _('تقرير الإيرادات'),
                'description': _('تصدير بيانات الإيرادات والأرباح والمصروفات'),
                'formats': ['csv', 'excel', 'json'],
            },
            {
                'id': 'tax',
                'name': _('تقرير الضرائب'),
                'description': _('تصدير بيانات الضرائب والرسوم المحصلة'),
                'formats': ['csv', 'excel', 'json'],
            },
        ]

        # الحصول على التاريخ الافتراضي (الشهر الحالي)
        today = timezone.now()
        start_date = today.replace(day=1).date()

        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        end_date = end_date.date()

        context['default_start_date'] = start_date
        context['default_end_date'] = end_date

        return context


class ExportReportDataView(LoginRequiredMixin, DashboardAccessMixin, View):
    """
    واجهة برمجية لتصدير البيانات بتنسيقات مختلفة
    """
    permission_required = 'dashboard.export_reports'

    def get(self, request, *args, **kwargs):
        report_type = request.GET.get('report', '')
        export_format = request.GET.get('format', 'csv')

        # الحصول على نطاق التاريخ
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
            end_date = timezone.make_aware(end_date.replace(hour=23, minute=59, second=59))
        except (ValueError, TypeError):
            # استخدام الشهر الحالي كقيمة افتراضية
            today = timezone.now()
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59)

        # التحقق من صلاحية الوصول إلى نوع التقرير
        if report_type not in ['sales', 'products', 'customers', 'inventory', 'revenue', 'tax']:
            return HttpResponse(_('نوع التقرير غير صالح'), status=400)

        # التحقق من صلاحية تنسيق التصدير
        if export_format not in ['csv', 'excel', 'json']:
            return HttpResponse(_('تنسيق التصدير غير صالح'), status=400)

        # استدعاء دالة التصدير المناسبة
        if report_type == 'sales':
            return self.export_sales_report(start_date, end_date, export_format)
        elif report_type == 'products':
            return self.export_products_report(start_date, end_date, export_format)
        elif report_type == 'customers':
            return self.export_customers_report(start_date, end_date, export_format)
        elif report_type == 'inventory':
            return self.export_inventory_report(export_format)
        elif report_type == 'revenue':
            return self.export_revenue_report(start_date, end_date, export_format)
        elif report_type == 'tax':
            return self.export_tax_report(start_date, end_date, export_format)

        return HttpResponse(_('خطأ في التصدير'), status=400)

    def export_sales_report(self, start_date, end_date, export_format):
        """تصدير تقرير المبيعات"""
        # استعلام الطلبات للفترة المحددة
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('user')

        # تحديد اسم الملف
        filename = f"sales_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"

        # إعداد البيانات للتصدير
        data = []
        for order in orders:
            data.append({
                'order_number': order.order_number,
                'date': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'customer': order.user.get_full_name() if order.user else order.full_name,
                'email': order.email,
                'status': order.get_status_display(),
                'payment_status': order.get_payment_status_display(),
                'items_count': order.items.count(),
                'subtotal': float(order.total_price),
                'shipping': float(order.shipping_cost),
                'tax': float(order.tax_amount),
                'discount': float(order.discount_amount),
                'total': float(order.grand_total),
                'payment_method': order.payment_method,
                'country': order.shipping_country,
                'city': order.shipping_city,
            })

        # تصدير البيانات بالتنسيق المطلوب
        if export_format == 'csv':
            return self.export_as_csv(data, filename)
        elif export_format == 'excel':
            return self.export_as_excel(data, filename, _('تقرير المبيعات'))
        elif export_format == 'json':
            return self.export_as_json(data, filename)

    def export_products_report(self, start_date, end_date, export_format):
        """تصدير تقرير المنتجات"""
        # استعلام المنتجات
        products = Product.objects.filter(is_active=True).select_related('category', 'brand')

        # تحديد اسم الملف
        filename = f"products_report_{timezone.now().strftime('%Y%m%d')}"

        # إعداد البيانات للتصدير
        data = []
        for product in products:
            # حساب المبيعات خلال الفترة المحددة
            sales_in_period = OrderItem.objects.filter(
                product_id=str(product.id),
                order__created_at__gte=start_date,
                order__created_at__lte=end_date,
                order__status__in=['completed', 'delivered', 'shipped']
            ).aggregate(
                quantity=Sum('quantity'),
                revenue=Sum('total_price')
            )

            sales_quantity = sales_in_period['quantity'] or 0
            sales_revenue = sales_in_period['revenue'] or 0

            data.append({
                'id': str(product.id),
                'sku': product.sku,
                'name': product.name,
                'category': product.category.name if product.category else '',
                'brand': product.brand.name if product.brand else '',
                'price': float(product.base_price),
                'current_price': float(product.current_price),
                'stock_quantity': product.stock_quantity,
                'status': product.get_status_display(),
                'sales_count': product.sales_count,
                'views_count': product.views_count,
                'period_sales_quantity': sales_quantity,
                'period_sales_revenue': float(sales_revenue),
                'created_at': product.created_at.strftime('%Y-%m-%d'),
                'is_active': 'نعم' if product.is_active else 'لا',
            })

        # تصدير البيانات بالتنسيق المطلوب
        if export_format == 'csv':
            return self.export_as_csv(data, filename)
        elif export_format == 'excel':
            return self.export_as_excel(data, filename, _('تقرير المنتجات'))
        elif export_format == 'json':
            return self.export_as_json(data, filename)

    def export_customers_report(self, start_date, end_date, export_format):
        """تصدير تقرير العملاء"""
        # استعلام المستخدمين (العملاء)
        customers = User.objects.filter(
            is_staff=False, is_superuser=False
        )

        # تحديد اسم الملف
        filename = f"customers_report_{timezone.now().strftime('%Y%m%d')}"

        # إعداد البيانات للتصدير
        data = []
        for customer in customers:
            # حساب إحصائيات الطلبات خلال الفترة المحددة
            period_orders = Order.objects.filter(
                user=customer,
                created_at__gte=start_date,
                created_at__lte=end_date
            )

            completed_orders = period_orders.filter(
                status__in=['completed', 'delivered']
            )

            period_orders_count = period_orders.count()
            period_orders_total = completed_orders.aggregate(
                total=Sum('grand_total')
            )['total'] or 0

            # حساب إجمالي الطلبات لجميع الفترات
            all_orders = Order.objects.filter(user=customer)
            all_completed_orders = all_orders.filter(
                status__in=['completed', 'delivered']
            )

            total_orders_count = all_orders.count()
            total_orders_amount = all_completed_orders.aggregate(
                total=Sum('grand_total')
            )['total'] or 0

            data.append({
                'id': str(customer.id),
                'username': customer.username,
                'full_name': customer.get_full_name(),
                'email': customer.email,
                'phone': customer.phone_number,
                'date_joined': customer.date_joined.strftime('%Y-%m-%d'),
                'is_active': 'نعم' if customer.is_active else 'لا',
                'is_verified': 'نعم' if getattr(customer, 'is_verified', False) else 'لا',
                'period_orders_count': period_orders_count,
                'period_orders_total': float(period_orders_total),
                'total_orders_count': total_orders_count,
                'total_orders_amount': float(total_orders_amount),
                'country': customer.country,
                'city': customer.city,
                'last_order_date': all_orders.order_by('-created_at').first().created_at.strftime(
                    '%Y-%m-%d') if all_orders.exists() else '',
            })

        # تصدير البيانات بالتنسيق المطلوب
        if export_format == 'csv':
            return self.export_as_csv(data, filename)
        elif export_format == 'excel':
            return self.export_as_excel(data, filename, _('تقرير العملاء'))
        elif export_format == 'json':
            return self.export_as_json(data, filename)

    def export_inventory_report(self, export_format):
        """تصدير تقرير المخزون"""
        # استعلام المنتجات
        products = Product.objects.filter(is_active=True).select_related('category', 'brand')

        # تحديد اسم الملف
        filename = f"inventory_report_{timezone.now().strftime('%Y%m%d')}"

        # إعداد البيانات للتصدير
        data = []
        for product in products:
            # حساب قيمة المخزون
            inventory_value = product.stock_quantity * product.base_price

            data.append({
                'id': str(product.id),
                'sku': product.sku,
                'name': product.name,
                'category': product.category.name if product.category else '',
                'brand': product.brand.name if product.brand else '',
                'stock_quantity': product.stock_quantity,
                'reserved_quantity': product.reserved_quantity,
                'available_quantity': product.available_quantity,
                'min_stock_level': product.min_stock_level,
                'status': product.get_stock_status_display(),
                'unit_price': float(product.base_price),
                'inventory_value': float(inventory_value),
                'low_stock': 'نعم' if product.low_stock else 'لا',
                'in_stock': 'نعم' if product.in_stock else 'لا',
            })

            # إضافة معلومات المتغيرات إذا كانت متوفرة
            for variant in product.variants.filter(is_active=True):
                variant_value = variant.stock_quantity * (variant.base_price or product.base_price)

                data.append({
                    'id': str(variant.id),
                    'sku': variant.sku,
                    'name': f"{product.name} - {variant.name}",
                    'category': product.category.name if product.category else '',
                    'brand': product.brand.name if product.brand else '',
                    'stock_quantity': variant.stock_quantity,
                    'reserved_quantity': variant.reserved_quantity,
                    'available_quantity': variant.available_quantity,
                    'min_stock_level': product.min_stock_level,
                    'status': 'متوفر' if variant.is_in_stock else 'غير متوفر',
                    'unit_price': float(variant.base_price or product.base_price),
                    'inventory_value': float(variant_value),
                    'low_stock': 'نعم' if variant.stock_quantity <= product.min_stock_level else 'لا',
                    'in_stock': 'نعم' if variant.is_in_stock else 'لا',
                    'is_variant': 'نعم',
                    'parent_product': product.name,
                })

        # تصدير البيانات بالتنسيق المطلوب
        if export_format == 'csv':
            return self.export_as_csv(data, filename)
        elif export_format == 'excel':
            return self.export_as_excel(data, filename, _('تقرير المخزون'))
        elif export_format == 'json':
            return self.export_as_json(data, filename)

    def export_revenue_report(self, start_date, end_date, export_format):
        """تصدير تقرير الإيرادات"""
        # استعلام الطلبات للفترة المحددة
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status__in=['completed', 'delivered', 'shipped']
        ).select_related('user')

        # تحديد اسم الملف
        filename = f"revenue_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"

        # إعداد البيانات حسب اليوم
        daily_data = []

        # إنشاء قاموس بالتواريخ لتسهيل تجميع البيانات
        date_range = {}
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_range[current_date] = {
                'date': current_date.strftime('%Y-%m-%d'),
                'orders_count': 0,
                'subtotal': 0,
                'shipping': 0,
                'tax': 0,
                'discount': 0,
                'total': 0,
                'refunds': 0,
                'net_revenue': 0,
            }
            current_date += timedelta(days=1)

        # تجميع بيانات الطلبات حسب اليوم
        for order in orders:
            order_date = order.created_at.date()
            if order_date in date_range:
                date_range[order_date]['orders_count'] += 1
                date_range[order_date]['subtotal'] += float(order.total_price)
                date_range[order_date]['shipping'] += float(order.shipping_cost)
                date_range[order_date]['tax'] += float(order.tax_amount)
                date_range[order_date]['discount'] += float(order.discount_amount)
                date_range[order_date]['total'] += float(order.grand_total)

        # إضافة بيانات المبالغ المستردة
        refunds = Refund.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status='completed'
        )

        for refund in refunds:
            refund_date = refund.created_at.date()
            if refund_date in date_range:
                date_range[refund_date]['refunds'] += float(refund.amount)

        # حساب صافي الإيرادات وتجميع البيانات
        for date, data in date_range.items():
            data['net_revenue'] = data['total'] - data['refunds']
            daily_data.append(data)

        # ترتيب البيانات حسب التاريخ
        daily_data.sort(key=lambda x: x['date'])

        # تصدير البيانات بالتنسيق المطلوب
        if export_format == 'csv':
            return self.export_as_csv(daily_data, filename)
        elif export_format == 'excel':
            return self.export_as_excel(daily_data, filename, _('تقرير الإيرادات'))
        elif export_format == 'json':
            return self.export_as_json(daily_data, filename)

    def export_tax_report(self, start_date, end_date, export_format):
        """تصدير تقرير الضرائب"""
        # استعلام الطلبات للفترة المحددة
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status__in=['completed', 'delivered', 'shipped']
        )

        # تحديد اسم الملف
        filename = f"tax_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"

        # إعداد البيانات حسب اليوم
        daily_data = []

        # إنشاء قاموس بالتواريخ لتسهيل تجميع البيانات
        date_range = {}
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_range[current_date] = {
                'date': current_date.strftime('%Y-%m-%d'),
                'orders_count': 0,
                'subtotal': 0,
                'tax': 0,
                'total': 0,
                'tax_rate': 0,
            }
            current_date += timedelta(days=1)

        # تجميع بيانات الطلبات حسب اليوم
        for order in orders:
            order_date = order.created_at.date()
            if order_date in date_range:
                date_range[order_date]['orders_count'] += 1
                date_range[order_date]['subtotal'] += float(order.total_price)
                date_range[order_date]['tax'] += float(order.tax_amount)
                date_range[order_date]['total'] += float(order.grand_total)

        # حساب نسبة الضريبة وتجميع البيانات
        for date, data in date_range.items():
            if data['subtotal'] > 0:
                data['tax_rate'] = (data['tax'] / data['subtotal']) * 100
            daily_data.append(data)

        # ترتيب البيانات حسب التاريخ
        daily_data.sort(key=lambda x: x['date'])

        # تصدير البيانات بالتنسيق المطلوب
        if export_format == 'csv':
            return self.export_as_csv(daily_data, filename)
        elif export_format == 'excel':
            return self.export_as_excel(daily_data, filename, _('تقرير الضرائب'))
        elif export_format == 'json':
            return self.export_as_json(daily_data, filename)

    def export_as_csv(self, data, filename):
        """تصدير البيانات بتنسيق CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'

        if not data:
            # إرجاع ملف فارغ إذا كانت البيانات فارغة
            writer = csv.writer(response)
            writer.writerow(['لا توجد بيانات'])
            return response

        # كتابة رؤوس الأعمدة (مفاتيح القاموس الأول)
        writer = csv.writer(response)
        headers = list(data[0].keys())
        writer.writerow(headers)

        # كتابة الصفوف
        for row in data:
            writer.writerow([row.get(header, '') for header in headers])

        return response

    def export_as_excel(self, data, filename, sheet_name):
        """تصدير البيانات بتنسيق Excel"""
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xls"'

        # إنشاء ملف Excel
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet(sheet_name)

        # تنسيق الرؤوس
        header_style = xlwt.XFStyle()
        header_font = xlwt.Font()
        header_font.bold = True
        header_style.font = header_font

        if not data:
            # كتابة رسالة إذا كانت البيانات فارغة
            ws.write(0, 0, 'لا توجد بيانات', header_style)
            wb.save(response)
            return response

        # كتابة رؤوس الأعمدة
        headers = list(data[0].keys())
        for col_idx, header in enumerate(headers):
            ws.write(0, col_idx, header, header_style)

        # كتابة الصفوف
        for row_idx, row in enumerate(data, 1):
            for col_idx, header in enumerate(headers):
                ws.write(row_idx, col_idx, row.get(header, ''))

        wb.save(response)
        return response

    def export_as_json(self, data, filename):
        """تصدير البيانات بتنسيق JSON"""
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}.json"'

        # تحويل القيم العشرية إلى نص لتجنب مشاكل التسلسل
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)

        json.dump(data, response, default=decimal_default, ensure_ascii=False, indent=4)
        return response