# dashboard/views/api.py
"""
واجهات برمجة التطبيقات (APIs) للوحة التحكم
توفر نقاط نهاية لتبادل البيانات بتنسيق JSON للاستخدام في طلبات AJAX وتحديث الواجهة بشكل ديناميكي
"""

from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg, F
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator

from dashboard.mixins import DashboardAccessMixin
from products.models import Product, Category, Brand, ProductVariant
from orders.models import Order, OrderItem
from payment.models import Payment, Refund
from cart.models import Cart
from dashboard.models import DashboardNotification, DashboardWidget

import json
from datetime import datetime, timedelta
from decimal import Decimal

User = get_user_model()


class DashboardStatsAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية لإحصائيات لوحة التحكم
    توفر البيانات الإحصائية الأساسية لعرضها في الصفحة الرئيسية للوحة التحكم
    """
    permission_required = 'dashboard.view_dashboard'

    def get(self, request, *args, **kwargs):
        # الفترة الزمنية للإحصائيات
        time_period = request.GET.get('period', 'today')

        # تحديد نطاق التاريخ بناءً على الفترة المطلوبة
        now = timezone.now()
        if time_period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif time_period == 'yesterday':
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(hour=23, minute=59, second=59)
        elif time_period == 'week':
            # الأسبوع الحالي
            start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif time_period == 'month':
            # الشهر الحالي
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif time_period == 'year':
            # السنة الحالية
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        else:
            # القيمة الافتراضية هي اليوم
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        # استعلامات الإحصائيات الأساسية

        # إحصائيات المبيعات
        orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        orders_count = orders.count()
        completed_orders = orders.filter(status__in=['completed', 'delivered'])
        completed_orders_count = completed_orders.count()
        total_revenue = completed_orders.aggregate(total=Sum('grand_total'))['total'] or 0

        # الطلبات حسب الحالة
        orders_by_status = list(orders.values('status').annotate(
            count=Count('id'),
            total=Sum('grand_total')
        ).order_by('status'))

        # تحويل قاموس حالات الطلبات لتحويل الرموز إلى نصوص
        status_dict = dict(Order.STATUS_CHOICES)
        for item in orders_by_status:
            item['status_display'] = status_dict.get(item['status'], item['status'])
            item['total'] = float(item['total']) if item['total'] else 0

        # إحصائيات المستخدمين
        new_users = User.objects.filter(
            date_joined__gte=start_date,
            date_joined__lte=end_date,
            is_staff=False,
            is_superuser=False
        ).count()

        total_users = User.objects.filter(is_staff=False, is_superuser=False).count()

        # إحصائيات المنتجات
        new_products = Product.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).count()

        total_products = Product.objects.count()
        out_of_stock_products = Product.objects.filter(stock_quantity__lte=0).count()

        # أكثر المنتجات مبيعاً خلال الفترة
        top_selling = OrderItem.objects.filter(
            order__in=completed_orders
        ).values('product_id', 'product_name').annotate(
            count=Sum('quantity'),
            revenue=Sum('total_price')
        ).order_by('-count')[:5]

        # تحويل الأرقام العشرية إلى قيم عادية لتسهيل تحويلها إلى JSON
        top_selling_list = []
        for item in top_selling:
            top_selling_list.append({
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'count': item['count'],
                'revenue': float(item['revenue']) if item['revenue'] else 0
            })

        # أحدث الطلبات
        recent_orders = list(orders.order_by('-created_at')[:5].values(
            'id', 'order_number', 'created_at', 'grand_total', 'status', 'full_name'
        ))

        # تحويل التواريخ والأرقام العشرية لتسهيل تحويلها إلى JSON
        for order in recent_orders:
            order['created_at'] = order['created_at'].strftime('%Y-%m-%d %H:%M')
            order['grand_total'] = float(order['grand_total'])
            order['status_display'] = status_dict.get(order['status'], order['status'])

        # تجميع البيانات في قاموس واحد
        data = {
            'time_period': time_period,
            'start_date': start_date.strftime('%Y-%m-%d %H:%M'),
            'end_date': end_date.strftime('%Y-%m-%d %H:%M'),
            'orders': {
                'total_count': orders_count,
                'completed_count': completed_orders_count,
                'total_revenue': float(total_revenue),
                'by_status': orders_by_status,
                'recent_orders': recent_orders
            },
            'users': {
                'new_users': new_users,
                'total_users': total_users
            },
            'products': {
                'new_products': new_products,
                'total_products': total_products,
                'out_of_stock': out_of_stock_products,
                'top_selling': top_selling_list
            }
        }

        return JsonResponse(data)


class ChartDataAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية لبيانات الرسوم البيانية
    توفر البيانات اللازمة لإنشاء الرسوم البيانية المختلفة في لوحة التحكم
    """
    permission_required = 'dashboard.view_dashboard'

    def get(self, request, *args, **kwargs):
        chart_type = request.GET.get('type', 'sales')
        time_period = request.GET.get('period', 'month')

        if chart_type == 'sales':
            return self.get_sales_chart_data(request, time_period)
        elif chart_type == 'users':
            return self.get_users_chart_data(request, time_period)
        elif chart_type == 'products':
            return self.get_products_chart_data(request)
        elif chart_type == 'categories':
            return self.get_categories_chart_data(request)
        elif chart_type == 'orders_status':
            return self.get_orders_status_chart_data(request, time_period)
        elif chart_type == 'payment_methods':
            return self.get_payment_methods_chart_data(request, time_period)
        else:
            return JsonResponse({'error': _('نوع الرسم البياني غير صالح')}, status=400)

    def get_date_range(self, time_period):
        """تحديد نطاق التاريخ بناءً على الفترة الزمنية"""
        now = timezone.now()

        if time_period == 'week':
            # الأسبوع الحالي
            start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            date_format = '%Y-%m-%d'  # تنسيق يومي
        elif time_period == 'month':
            # الشهر الحالي
            start_date = (now - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            date_format = '%Y-%m-%d'  # تنسيق يومي
        elif time_period == 'quarter':
            # الربع الحالي
            start_date = (now - timedelta(days=89)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            date_format = '%Y-%m-%d'  # تنسيق يومي
        elif time_period == 'year':
            # السنة الحالية
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            date_format = '%Y-%m'  # تنسيق شهري
        else:
            # القيمة الافتراضية هي الشهر الحالي
            start_date = (now - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            date_format = '%Y-%m-%d'  # تنسيق يومي

        return start_date, end_date, date_format

    def get_sales_chart_data(self, request, time_period):
        """بيانات مبيعات الرسم البياني"""
        start_date, end_date, date_format = self.get_date_range(time_period)

        # تحديد التجميع بناءً على الفترة الزمنية
        if time_period == 'year':
            # تجميع شهري
            orders_data = Order.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).annotate(
                date=F('created_at__month')
            ).values('date').annotate(
                count=Count('id'),
                revenue=Sum('grand_total')
            ).order_by('date')

            # تحويل رقم الشهر إلى اسم الشهر
            months = ['يناير', 'فبراير', 'مارس', 'إبريل', 'مايو', 'يونيو',
                      'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

            labels = []
            values = []

            for month_num in range(1, 13):
                month_data = next((item for item in orders_data if item['date'] == month_num), None)
                labels.append(months[month_num - 1])

                if month_data:
                    values.append(float(month_data['revenue']))
                else:
                    values.append(0)
        else:
            # تجميع يومي
            orders_data = Order.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            ).annotate(
                date=F('created_at__date')
            ).values('date').annotate(
                count=Count('id'),
                revenue=Sum('grand_total')
            ).order_by('date')

            # إنشاء قاموس بالتواريخ لملء الأيام الفارغة
            date_range = {}
            current_date = start_date.date()
            while current_date <= end_date.date():
                date_range[current_date] = 0
                current_date += timedelta(days=1)

            # ملء البيانات
            for item in orders_data:
                date_range[item['date']] = float(item['revenue'])

            # تحويل إلى قوائم للرسم البياني
            labels = [date.strftime(date_format) for date in date_range.keys()]
            values = list(date_range.values())

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': _('المبيعات'),
                'data': values,
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            }]
        })

    def get_users_chart_data(self, request, time_period):
        """بيانات المستخدمين للرسم البياني"""
        start_date, end_date, date_format = self.get_date_range(time_period)

        # تحديد التجميع بناءً على الفترة الزمنية
        if time_period == 'year':
            # تجميع شهري
            users_data = User.objects.filter(
                date_joined__gte=start_date,
                date_joined__lte=end_date,
                is_staff=False,
                is_superuser=False
            ).annotate(
                month=F('date_joined__month')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')

            # تحويل رقم الشهر إلى اسم الشهر
            months = ['يناير', 'فبراير', 'مارس', 'إبريل', 'مايو', 'يونيو',
                      'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

            labels = []
            values = []

            for month_num in range(1, 13):
                month_data = next((item for item in users_data if item['month'] == month_num), None)
                labels.append(months[month_num - 1])

                if month_data:
                    values.append(month_data['count'])
                else:
                    values.append(0)
        else:
            # تجميع يومي
            users_data = User.objects.filter(
                date_joined__gte=start_date,
                date_joined__lte=end_date,
                is_staff=False,
                is_superuser=False
            ).annotate(
                date=F('date_joined__date')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            # إنشاء قاموس بالتواريخ لملء الأيام الفارغة
            date_range = {}
            current_date = start_date.date()
            while current_date <= end_date.date():
                date_range[current_date] = 0
                current_date += timedelta(days=1)

            # ملء البيانات
            for item in users_data:
                date_range[item['date']] = item['count']

            # تحويل إلى قوائم للرسم البياني
            labels = [date.strftime(date_format) for date in date_range.keys()]
            values = list(date_range.values())

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': _('المستخدمين الجدد'),
                'data': values,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            }]
        })

    def get_products_chart_data(self, request):
        """بيانات المنتجات الأكثر مبيعاً للرسم البياني"""
        # أكثر المنتجات مبيعاً
        top_products = OrderItem.objects.values('product_name').annotate(
            count=Sum('quantity')
        ).order_by('-count')[:10]

        labels = [item['product_name'] for item in top_products]
        values = [item['count'] for item in top_products]

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': _('المنتجات الأكثر مبيعاً'),
                'data': values,
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)',
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)'
                ],
                'borderColor': [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                'borderWidth': 1
            }]
        })

    def get_categories_chart_data(self, request):
        """بيانات الفئات الأكثر مبيعاً للرسم البياني"""
        # الفئات الأكثر مبيعاً
        top_categories = OrderItem.objects.filter(
            product__isnull=False
        ).values('product__category__name').annotate(
            count=Count('id'),
            total=Sum('total_price')
        ).order_by('-total')[:8]

        labels = [item['product__category__name'] or _('غير مصنف') for item in top_categories]
        values = [float(item['total']) for item in top_categories]

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': _('المبيعات حسب الفئة'),
                'data': values,
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)',
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)'
                ],
                'borderColor': [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)'
                ],
                'borderWidth': 1
            }]
        })

    def get_orders_status_chart_data(self, request, time_period):
        """بيانات حالات الطلبات للرسم البياني"""
        start_date, end_date, date_format = self.get_date_range(time_period)

        # توزيع الطلبات حسب الحالة
        orders_status = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).values('status').annotate(
            count=Count('id')
        ).order_by('status')

        # تحويل قاموس حالات الطلبات
        status_dict = dict(Order.STATUS_CHOICES)

        labels = [status_dict.get(item['status'], item['status']) for item in orders_status]
        values = [item['count'] for item in orders_status]

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': _('الطلبات حسب الحالة'),
                'data': values,
                'backgroundColor': [
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                'borderColor': [
                    'rgba(255, 206, 86, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                'borderWidth': 1
            }]
        })

    def get_payment_methods_chart_data(self, request, time_period):
        """بيانات طرق الدفع للرسم البياني"""
        start_date, end_date, date_format = self.get_date_range(time_period)

        # توزيع الطلبات حسب طريقة الدفع
        payment_methods = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status__in=['completed', 'delivered']
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('grand_total')
        ).order_by('-total')

        labels = [item['payment_method'] or _('غير محدد') for item in payment_methods]
        values = [float(item['total']) for item in payment_methods]

        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': _('المبيعات حسب طريقة الدفع'),
                'data': values,
                'backgroundColor': [
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                'borderColor': [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                'borderWidth': 1
            }]
        })


class UserAutocompleteAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية للبحث عن المستخدمين
    تستخدم للبحث السريع عن المستخدمين أثناء الكتابة
    """
    permission_required = 'dashboard.view_user'

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        limit = int(request.GET.get('limit', 10))

        if not query or len(query) < 2:
            return JsonResponse({'results': []})

        # البحث في المستخدمين
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        ).order_by('username')[:limit]

        results = []
        for user in users:
            results.append({
                'id': str(user.id),
                'text': f"{user.username} ({user.get_full_name() or user.email})",
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'avatar': user.avatar.url if user.avatar else None
            })

        return JsonResponse({'results': results})


class ProductAutocompleteAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية للبحث عن المنتجات
    تستخدم للبحث السريع عن المنتجات أثناء الكتابة
    """
    permission_required = 'dashboard.view_product'

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        limit = int(request.GET.get('limit', 10))
        include_variants = request.GET.get('include_variants', 'false') == 'true'

        if not query or len(query) < 2:
            return JsonResponse({'results': []})

        # البحث في المنتجات
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query)
        ).order_by('name')[:limit]

        results = []
        for product in products:
            product_data = {
                'id': str(product.id),
                'text': f"{product.name} ({product.sku})",
                'name': product.name,
                'sku': product.sku,
                'price': float(product.base_price),
                'stock': product.stock_quantity,
                'image': product.default_image.image.url if product.default_image else None,
                'category': product.category.name if product.category else None,
                'is_variant': False
            }
            results.append(product_data)

            # إضافة متغيرات المنتج إذا كان مطلوباً
            if include_variants:
                variants = ProductVariant.objects.filter(product=product)
                for variant in variants:
                    variant_data = {
                        'id': str(variant.id),
                        'text': f"{product.name} - {variant.name} ({variant.sku})",
                        'name': f"{product.name} - {variant.name}",
                        'sku': variant.sku,
                        'price': float(variant.base_price or product.base_price),
                        'stock': variant.stock_quantity,
                        'image': variant.images.first().image.url if variant.images.exists() else (
                            product.default_image.image.url if product.default_image else None),
                        'category': product.category.name if product.category else None,
                        'is_variant': True,
                        'product_id': str(product.id),
                        'variant_name': variant.name
                    }
                    results.append(variant_data)

        return JsonResponse({'results': results})


class OrderAutocompleteAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية للبحث عن الطلبات
    تستخدم للبحث السريع عن الطلبات أثناء الكتابة
    """
    permission_required = 'dashboard.view_order'

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        limit = int(request.GET.get('limit', 10))

        if not query or len(query) < 2:
            return JsonResponse({'results': []})

        # البحث في الطلبات
        orders = Order.objects.filter(
            Q(order_number__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        ).order_by('-created_at')[:limit]

        results = []
        for order in orders:
            results.append({
                'id': str(order.id),
                'text': f"{order.order_number} - {order.full_name}",
                'order_number': order.order_number,
                'full_name': order.full_name,
                'email': order.email,
                'date': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'total': float(order.grand_total),
                'status': order.status,
                'status_display': order.get_status_display(),
                'payment_status': order.payment_status,
                'payment_status_display': order.get_payment_status_display()
            })

        return JsonResponse({'results': results})


class NotificationAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية لإدارة الإشعارات
    تتيح الحصول على الإشعارات وتحديثها وتعليمها كمقروءة
    """

    def get(self, request, *args, **kwargs):
        """الحصول على قائمة الإشعارات"""
        limit = int(request.GET.get('limit', 10))

        # استعلام الإشعارات للمستخدم الحالي
        notifications = DashboardNotification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:limit]

        results = []
        for notification in notifications:
            results.append({
                'id': str(notification.id),
                'title': notification.title,
                'message': notification.message,
                'date': notification.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_read': notification.is_read,
                'notification_type': notification.notification_type,
                'icon': notification.get_icon(),
                'url': notification.url
            })

        # عدد الإشعارات غير المقروءة
        unread_count = DashboardNotification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        return JsonResponse({
            'notifications': results,
            'unread_count': unread_count
        })

    def post(self, request, *args, **kwargs):
        """تعليم الإشعارات كمقروءة"""
        try:
            data = json.loads(request.body)
            notification_ids = data.get('notification_ids', [])
            mark_all = data.get('mark_all', False)

            if mark_all:
                # تعليم جميع الإشعارات كمقروءة
                DashboardNotification.objects.filter(
                    user=request.user,
                    is_read=False
                ).update(is_read=True, read_at=timezone.now())

                return JsonResponse({
                    'success': True,
                    'message': _('تم تعليم جميع الإشعارات كمقروءة بنجاح'),
                    'unread_count': 0
                })

            elif notification_ids:
                # تعليم إشعارات محددة كمقروءة
                DashboardNotification.objects.filter(
                    user=request.user,
                    id__in=notification_ids,
                    is_read=False
                ).update(is_read=True, read_at=timezone.now())

                # حساب عدد الإشعارات غير المقروءة
                unread_count = DashboardNotification.objects.filter(
                    user=request.user,
                    is_read=False
                ).count()

                return JsonResponse({
                    'success': True,
                    'message': _('تم تعليم الإشعارات المحددة كمقروءة بنجاح'),
                    'unread_count': unread_count
                })

            return JsonResponse({
                'success': False,
                'message': _('لم يتم تحديد أي إشعارات')
            }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': _('بيانات غير صالحة')
            }, status=400)


class OrderStatusUpdateAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية لتحديث حالة الطلب
    تتيح تحديث حالة الطلب وحالة الدفع بسرعة
    """
    permission_required = 'orders.change_order'

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            status = data.get('status')
            payment_status = data.get('payment_status')
            notes = data.get('notes', '')

            if not order_id or (not status and not payment_status):
                return JsonResponse({
                    'success': False,
                    'message': _('البيانات المطلوبة غير مكتملة')
                }, status=400)

            # الحصول على الطلب
            order = get_object_or_404(Order, pk=order_id)

            # تحديث الحالة إذا تم تحديدها
            if status:
                old_status = order.status
                order.status = status

                # إذا تم تحديث الحالة إلى "تم التسليم" أو "مكتمل"، تحديث تاريخ الإكمال
                if status in ['delivered', 'completed'] and old_status not in ['delivered', 'completed']:
                    order.completed_at = timezone.now()

            # تحديث حالة الدفع إذا تم تحديدها
            if payment_status:
                order.payment_status = payment_status

            # إضافة ملاحظات إذا تم تحديدها
            if notes:
                order.notes = f"{order.notes}\n{timezone.now().strftime('%Y-%m-%d %H:%M')} - {notes}" if order.notes else notes

            # حفظ التغييرات
            order.save()

            # إرجاع البيانات المحدثة
            return JsonResponse({
                'success': True,
                'message': _('تم تحديث حالة الطلب بنجاح'),
                'order': {
                    'id': str(order.id),
                    'order_number': order.order_number,
                    'status': order.status,
                    'status_display': order.get_status_display(),
                    'payment_status': order.payment_status,
                    'payment_status_display': order.get_payment_status_display()
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': _('بيانات غير صالحة')
            }, status=400)
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('الطلب غير موجود')
            }, status=404)


class ProductStockUpdateAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية لتحديث مخزون المنتج
    تتيح تحديث كمية المخزون للمنتج أو المتغير بسرعة
    """
    permission_required = 'products.change_product'

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            variant_id = data.get('variant_id')
            stock_quantity = data.get('stock_quantity')

            if (not product_id and not variant_id) or stock_quantity is None:
                return JsonResponse({
                    'success': False,
                    'message': _('البيانات المطلوبة غير مكتملة')
                }, status=400)

            # تحويل الكمية إلى عدد صحيح
            try:
                stock_quantity = int(stock_quantity)
                if stock_quantity < 0:
                    raise ValueError(_('الكمية يجب أن تكون أكبر من أو تساوي الصفر'))
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=400)

            # تحديث المخزون
            if variant_id:
                # تحديث مخزون المتغير
                variant = get_object_or_404(ProductVariant, pk=variant_id)
                variant.stock_quantity = stock_quantity
                variant.save()

                return JsonResponse({
                    'success': True,
                    'message': _('تم تحديث مخزون المتغير بنجاح'),
                    'variant': {
                        'id': str(variant.id),
                        'product_id': str(variant.product.id),
                        'name': variant.name,
                        'sku': variant.sku,
                        'stock_quantity': variant.stock_quantity
                    }
                })
            else:
                # تحديث مخزون المنتج
                product = get_object_or_404(Product, pk=product_id)
                product.stock_quantity = stock_quantity

                # تحديث حالة المخزون بناءً على الكمية
                if stock_quantity <= 0:
                    product.stock_status = 'out_of_stock'
                elif stock_quantity <= product.min_stock_level:
                    product.stock_status = 'in_stock'  # لكن سيظهر كمخزون منخفض
                else:
                    product.stock_status = 'in_stock'

                product.save()

                return JsonResponse({
                    'success': True,
                    'message': _('تم تحديث مخزون المنتج بنجاح'),
                    'product': {
                        'id': str(product.id),
                        'name': product.name,
                        'sku': product.sku,
                        'stock_quantity': product.stock_quantity,
                        'stock_status': product.stock_status,
                        'stock_status_display': product.get_stock_status_display()
                    }
                })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': _('بيانات غير صالحة')
            }, status=400)
        except (Product.DoesNotExist, ProductVariant.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': _('المنتج أو المتغير غير موجود')
            }, status=404)


class DashboardWidgetDataAPIView( DashboardAccessMixin, View):
    """
    واجهة برمجية لبيانات ودجات لوحة التحكم
    توفر البيانات اللازمة لعرض ودجات لوحة التحكم المختلفة
    """

    def get(self, request, *args, **kwargs):
        widget_name = request.GET.get('widget', '')

        if not widget_name:
            return JsonResponse({
                'success': False,
                'message': _('لم يتم تحديد الودجة')
            }, status=400)

        # استدعاء الدالة المناسبة بناءً على اسم الودجة
        if widget_name == 'recent_orders':
            return self.get_recent_orders_data(request)
        elif widget_name == 'low_stock_products':
            return self.get_low_stock_products_data(request)
        elif widget_name == 'sales_summary':
            return self.get_sales_summary_data(request)
        elif widget_name == 'top_customers':
            return self.get_top_customers_data(request)
        elif widget_name == 'latest_reviews':
            return self.get_latest_reviews_data(request)
        elif widget_name == 'orders_by_status':
            return self.get_orders_by_status_data(request)
        else:
            return JsonResponse({
                'success': False,
                'message': _('الودجة غير موجودة')
            }, status=404)

    def get_recent_orders_data(self, request):
        """بيانات أحدث الطلبات"""
        limit = int(request.GET.get('limit', 5))

        # أحدث الطلبات
        recent_orders = Order.objects.order_by('-created_at')[:limit]

        orders_data = []
        for order in recent_orders:
            orders_data.append({
                'id': str(order.id),
                'order_number': order.order_number,
                'full_name': order.full_name,
                'email': order.email,
                'date': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'total': float(order.grand_total),
                'status': order.status,
                'status_display': order.get_status_display(),
                'payment_status': order.payment_status,
                'payment_status_display': order.get_payment_status_display()
            })

        return JsonResponse({
            'success': True,
            'orders': orders_data
        })

    def get_low_stock_products_data(self, request):
        """بيانات المنتجات منخفضة المخزون"""
        limit = int(request.GET.get('limit', 5))

        # المنتجات منخفضة المخزون
        low_stock_products = Product.objects.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F('min_stock_level')
        ).order_by('stock_quantity')[:limit]

        products_data = []
        for product in low_stock_products:
            products_data.append({
                'id': str(product.id),
                'name': product.name,
                'sku': product.sku,
                'stock_quantity': product.stock_quantity,
                'min_stock_level': product.min_stock_level,
                'image': product.default_image.image.url if product.default_image else None,
                'category': product.category.name if product.category else None,
                'price': float(product.base_price)
            })

        # المنتجات المنتهية من المخزون
        out_of_stock_count = Product.objects.filter(stock_quantity__lte=0).count()

        return JsonResponse({
            'success': True,
            'low_stock_products': products_data,
            'out_of_stock_count': out_of_stock_count,
            'low_stock_count': Product.objects.filter(
                stock_quantity__gt=0,
                stock_quantity__lte=F('min_stock_level')
            ).count()
        })

    def get_sales_summary_data(self, request):
        """بيانات ملخص المبيعات"""
        # المبيعات حسب الفترة الزمنية
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # إحصائيات اليوم
        today_orders = Order.objects.filter(
            created_at__gte=today,
            status__in=['completed', 'delivered']
        )
        today_revenue = today_orders.aggregate(total=Sum('grand_total'))['total'] or 0
        today_orders_count = today_orders.count()

        # إحصائيات الأمس
        yesterday_orders = Order.objects.filter(
            created_at__gte=yesterday,
            created_at__lt=today,
            status__in=['completed', 'delivered']
        )
        yesterday_revenue = yesterday_orders.aggregate(total=Sum('grand_total'))['total'] or 0
        yesterday_orders_count = yesterday_orders.count()

        # إحصائيات الأسبوع الحالي
        week_orders = Order.objects.filter(
            created_at__gte=start_of_week,
            status__in=['completed', 'delivered']
        )
        week_revenue = week_orders.aggregate(total=Sum('grand_total'))['total'] or 0
        week_orders_count = week_orders.count()

        # إحصائيات الشهر الحالي
        month_orders = Order.objects.filter(
            created_at__gte=start_of_month,
            status__in=['completed', 'delivered']
        )
        month_revenue = month_orders.aggregate(total=Sum('grand_total'))['total'] or 0
        month_orders_count = month_orders.count()

        return JsonResponse({
            'success': True,
            'today': {
                'revenue': float(today_revenue),
                'orders_count': today_orders_count
            },
            'yesterday': {
                'revenue': float(yesterday_revenue),
                'orders_count': yesterday_orders_count
            },
            'week': {
                'revenue': float(week_revenue),
                'orders_count': week_orders_count
            },
            'month': {
                'revenue': float(month_revenue),
                'orders_count': month_orders_count
            }
        })

    def get_top_customers_data(self, request):
        """بيانات أفضل العملاء"""
        limit = int(request.GET.get('limit', 5))

        # أفضل العملاء (الأكثر إنفاقاً)
        top_customers = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).annotate(
            total_spent=Sum('orders__grand_total', filter=Q(orders__status__in=['completed', 'delivered'])),
            orders_count=Count('orders')
        ).filter(
            total_spent__isnull=False
        ).order_by('-total_spent')[:limit]

        customers_data = []
        for customer in top_customers:
            customers_data.append({
                'id': str(customer.id),
                'username': customer.username,
                'full_name': customer.get_full_name(),
                'email': customer.email,
                'total_spent': float(customer.total_spent) if customer.total_spent else 0,
                'orders_count': customer.orders_count,
                'avatar': customer.avatar.url if customer.avatar else None,
                'date_joined': customer.date_joined.strftime('%Y-%m-%d')
            })

        return JsonResponse({
            'success': True,
            'top_customers': customers_data
        })

    def get_latest_reviews_data(self, request):
        """بيانات أحدث التقييمات"""
        from products.models import ProductReview
        limit = int(request.GET.get('limit', 5))

        # أحدث التقييمات
        latest_reviews = ProductReview.objects.select_related(
            'product', 'user'
        ).order_by('-created_at')[:limit]

        reviews_data = []
        for review in latest_reviews:
            reviews_data.append({
                'id': str(review.id),
                'product_id': str(review.product.id),
                'product_name': review.product.name,
                'user_id': str(review.user.id),
                'user_name': review.user.get_full_name() or review.user.username,
                'rating': review.rating,
                'title': review.title,
                'content': review.content[:100] + '...' if len(review.content) > 100 else review.content,
                'date': review.created_at.strftime('%Y-%m-%d'),
                'is_approved': review.is_approved
            })

        return JsonResponse({
            'success': True,
            'latest_reviews': reviews_data,
            'pending_reviews': ProductReview.objects.filter(is_approved=False).count()
        })

    def get_orders_by_status_data(self, request):
        """بيانات الطلبات حسب الحالة"""
        # توزيع الطلبات حسب الحالة
        orders_by_status = Order.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')

        # تحويل قاموس حالات الطلبات
        status_dict = dict(Order.STATUS_CHOICES)

        status_data = []
        for item in orders_by_status:
            status_data.append({
                'status': item['status'],
                'status_display': status_dict.get(item['status'], item['status']),
                'count': item['count']
            })

        return JsonResponse({
            'success': True,
            'orders_by_status': status_data,
            'total_orders': Order.objects.count()
        })