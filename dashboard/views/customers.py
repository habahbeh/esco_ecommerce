import csv
import json
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Sum, Count, Max
from django.utils import timezone
from datetime import timedelta

from dashboard.views.dashboard import DashboardAccessMixin
from accounts.models import User
from orders.models import Order


class CustomerListView(DashboardAccessMixin, View):
    template_name = 'dashboard/customers/customer_list.html'

    def get(self, request):
        customers = User.objects.annotate(
            orders_count=Count('orders'),
            total_spent_calc=Sum('orders__grand_total'),
            last_order_date=Max('orders__created_at'),
        ).filter(orders_count__gt=0).order_by('-last_order_date')

        query = request.GET.get('q', '').strip()
        if query:
            customers = customers.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone_number__icontains=query) |
                Q(username__icontains=query)
            )

        city_filter = request.GET.get('city', '').strip()
        if city_filter:
            customers = customers.filter(city__icontains=city_filter)

        sort = request.GET.get('sort', '-last_order_date')
        allowed_sorts = {
            'name': 'first_name',
            '-name': '-first_name',
            'orders': 'orders_count',
            '-orders': '-orders_count',
            'spent': 'total_spent_calc',
            '-spent': '-total_spent_calc',
            'date': 'last_order_date',
            '-date': '-last_order_date',
            'joined': 'date_joined',
            '-joined': '-date_joined',
        }
        order_by = allowed_sorts.get(sort, '-last_order_date')
        customers = customers.order_by(order_by)

        page = int(request.GET.get('page', 1))
        per_page = 25
        total = customers.count()
        customers_page = customers[(page - 1) * per_page:page * per_page]

        total_customers = User.objects.annotate(oc=Count('orders')).filter(oc__gt=0).count()
        new_this_month = User.objects.annotate(oc=Count('orders')).filter(
            oc__gt=0,
            date_joined__date__gte=timezone.now().date().replace(day=1),
        ).count()

        context = {
            'customers': customers_page,
            'query': query,
            'city_filter': city_filter,
            'sort': sort,
            'page': page,
            'total_pages': (total + per_page - 1) // per_page,
            'total': total,
            'total_customers': total_customers,
            'new_this_month': new_this_month,
            'page_title': _('إدارة العملاء'),
            'current_page': 'customers',
        }
        return render(request, self.template_name, context)


class CustomerDetailView(DashboardAccessMixin, View):
    template_name = 'dashboard/customers/customer_detail.html'

    def get(self, request, customer_id):
        customer = get_object_or_404(User, pk=customer_id)
        orders = Order.objects.filter(user=customer).order_by('-created_at')
        total_spent = orders.aggregate(total=Sum('grand_total'))['total'] or 0
        orders_count = orders.count()

        context = {
            'customer': customer,
            'orders': orders[:20],
            'total_spent': total_spent,
            'orders_count': orders_count,
            'page_title': customer.get_full_name(),
            'current_page': 'customers',
        }
        return render(request, self.template_name, context)


class CustomerExportView(DashboardAccessMixin, View):
    def get(self, request):
        customers = User.objects.annotate(
            orders_count=Count('orders'),
            total_spent_calc=Sum('orders__grand_total'),
        ).filter(orders_count__gt=0).order_by('-date_joined')

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="customers.csv"'
        response.write('﻿')

        writer = csv.writer(response)
        writer.writerow([
            str(_('الاسم')),
            str(_('البريد الإلكتروني')),
            str(_('رقم الهاتف')),
            str(_('المدينة')),
            str(_('عدد الطلبات')),
            str(_('إجمالي المشتريات')),
            str(_('تاريخ التسجيل')),
        ])

        for c in customers:
            writer.writerow([
                c.get_full_name(),
                c.email,
                c.phone_number,
                c.city,
                c.orders_count,
                c.total_spent_calc or 0,
                c.date_joined.strftime('%Y-%m-%d'),
            ])

        return response
