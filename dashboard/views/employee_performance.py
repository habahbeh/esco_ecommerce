from django.views import View
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from dashboard.views.dashboard import DashboardAccessMixin
from dashboard.mixins import SuperuserRequiredMixin
from accounts.models import User, UserActivity


class EmployeePerformanceListView(SuperuserRequiredMixin, View):
    template_name = 'dashboard/employees/performance_list.html'

    def get(self, request):
        employees = User.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True)
        ).order_by('-last_activity')

        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        date_filter = {}
        if date_from:
            date_filter['timestamp__date__gte'] = date_from
        if date_to:
            date_filter['timestamp__date__lte'] = date_to

        employee_stats = []
        for emp in employees:
            activities = UserActivity.objects.filter(user=emp, **date_filter)
            stats = {
                'employee': emp,
                'total_activities': activities.count(),
                'products_added': activities.filter(activity_type='product_create').count(),
                'products_updated': activities.filter(activity_type='product_update').count(),
                'marketing': activities.filter(activity_type__startswith='marketing').count(),
                'seo': activities.filter(activity_type__startswith='seo').count(),
                'articles': activities.filter(activity_type__startswith='blog').count(),
                'events': activities.filter(activity_type__startswith='event').count(),
                'newsletters': activities.filter(activity_type__startswith='newsletter').count(),
                'orders': activities.filter(activity_type__startswith='order').count(),
            }
            employee_stats.append(stats)

        employee_stats.sort(key=lambda x: x['total_activities'], reverse=True)

        context = {
            'employee_stats': employee_stats,
            'date_from': date_from,
            'date_to': date_to,
            'page_title': _('أداء الموظفين'),
            'current_page': 'employee_performance',
        }
        return render(request, self.template_name, context)


class EmployeePerformanceDetailView(SuperuserRequiredMixin, View):
    template_name = 'dashboard/employees/performance_detail.html'

    def get(self, request, user_id):
        employee = get_object_or_404(User, pk=user_id)

        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        activities = UserActivity.objects.filter(user=employee)
        if date_from:
            activities = activities.filter(timestamp__date__gte=date_from)
        if date_to:
            activities = activities.filter(timestamp__date__lte=date_to)

        category_counts = {
            'product_create': activities.filter(activity_type='product_create').count(),
            'product_update': activities.filter(activity_type='product_update').count(),
            'marketing': activities.filter(activity_type__startswith='marketing').count(),
            'seo': activities.filter(activity_type__startswith='seo').count(),
            'blog': activities.filter(activity_type__startswith='blog').count(),
            'event': activities.filter(activity_type__startswith='event').count(),
            'newsletter': activities.filter(activity_type__startswith='newsletter').count(),
            'order': activities.filter(activity_type__startswith='order').count(),
        }

        recent_activities = activities.order_by('-timestamp')[:50]

        today = timezone.now().date()
        daily_data = []
        daily_labels = []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            count = activities.filter(timestamp__date=d).count()
            daily_data.append(count)
            daily_labels.append(d.strftime('%m/%d'))

        context = {
            'employee': employee,
            'category_counts': category_counts,
            'recent_activities': recent_activities,
            'total_activities': activities.count(),
            'daily_data': daily_data,
            'daily_labels': daily_labels,
            'date_from': date_from,
            'date_to': date_to,
            'page_title': f'{_("أداء")} - {employee.get_full_name()}',
            'current_page': 'employee_performance',
        }
        return render(request, self.template_name, context)
