import json
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from dashboard.mixins import DashboardAccessMixin
from chatbot.models import LeadRequest, LeadComment


class LeadRequestListView(DashboardAccessMixin, View):
    template_name = 'dashboard/lead_requests/lead_request_list.html'

    def get(self, request):
        leads = LeadRequest.objects.all().select_related('assigned_to', 'conversation')

        query = request.GET.get('q', '').strip()
        if query:
            leads = leads.filter(
                Q(customer_name__icontains=query) |
                Q(customer_phone__icontains=query) |
                Q(product_interest__icontains=query) |
                Q(customer_address__icontains=query)
            )

        status_filter = request.GET.get('status', '')
        if status_filter:
            leads = leads.filter(status=status_filter)

        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            leads = leads.filter(created_at__date__gte=date_from)
        if date_to:
            leads = leads.filter(created_at__date__lte=date_to)

        status_counts = dict(
            LeadRequest.objects.values_list('status').annotate(c=Count('id')).values_list('status', 'c')
        )
        total_count = LeadRequest.objects.count()

        page = int(request.GET.get('page', 1))
        per_page = 20
        total = leads.count()
        leads_page = leads[(page - 1) * per_page:page * per_page]

        context = {
            'leads': leads_page,
            'query': query,
            'status_filter': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'status_choices': LeadRequest.STATUS_CHOICES,
            'status_counts': status_counts,
            'status_counts_json': json.dumps(status_counts),
            'total_count': total_count,
            'page': page,
            'total_pages': (total + per_page - 1) // per_page,
            'total': total,
            'page_title': _('طلبات العملاء'),
            'current_page': 'lead_requests',
        }
        return render(request, self.template_name, context)


class LeadRequestDetailView(DashboardAccessMixin, View):
    template_name = 'dashboard/lead_requests/lead_request_detail.html'

    def get(self, request, lead_id):
        lead = get_object_or_404(LeadRequest.objects.select_related('assigned_to', 'conversation'), pk=lead_id)
        comments = lead.comments.select_related('user').order_by('-created_at')
        chat_messages = []
        if lead.conversation:
            chat_messages = lead.conversation.messages.all().order_by('created_at')

        context = {
            'lead': lead,
            'comments': comments,
            'chat_messages': chat_messages,
            'status_choices': LeadRequest.STATUS_CHOICES,
            'page_title': f'{_("طلب عميل")} #{lead.id}',
            'current_page': 'lead_requests',
        }
        return render(request, self.template_name, context)


class LeadRequestUpdateStatusView(DashboardAccessMixin, View):
    def post(self, request, lead_id):
        lead = get_object_or_404(LeadRequest, pk=lead_id)
        new_status = request.POST.get('status', '')
        comment_text = request.POST.get('comment', '').strip()

        valid_statuses = [s[0] for s in LeadRequest.STATUS_CHOICES]
        if new_status not in valid_statuses:
            messages.error(request, _('حالة غير صالحة'))
            return redirect('dashboard:lead_request_detail', lead_id=lead.id)

        old_status = lead.status
        lead.status = new_status
        lead.save()

        if comment_text or old_status != new_status:
            LeadComment.objects.create(
                lead=lead,
                user=request.user,
                content=comment_text or _('تم تغيير الحالة'),
                old_status=old_status,
                new_status=new_status,
            )

        messages.success(request, _('تم تحديث حالة الطلب'))
        return redirect('dashboard:lead_request_detail', lead_id=lead.id)


class LeadRequestAddCommentView(DashboardAccessMixin, View):
    def post(self, request, lead_id):
        lead = get_object_or_404(LeadRequest, pk=lead_id)
        comment_text = request.POST.get('comment', '').strip()

        if not comment_text:
            messages.error(request, _('يرجى كتابة تعليق'))
            return redirect('dashboard:lead_request_detail', lead_id=lead.id)

        LeadComment.objects.create(
            lead=lead,
            user=request.user,
            content=comment_text,
        )

        messages.success(request, _('تم إضافة التعليق'))
        return redirect('dashboard:lead_request_detail', lead_id=lead.id)


class LeadRequestAssignView(DashboardAccessMixin, View):
    def post(self, request, lead_id):
        lead = get_object_or_404(LeadRequest, pk=lead_id)
        lead.assigned_to = request.user
        lead.save()

        LeadComment.objects.create(
            lead=lead,
            user=request.user,
            content=_('تم تعيين الطلب لي'),
        )

        messages.success(request, _('تم تعيين الطلب لك'))
        return redirect('dashboard:lead_request_detail', lead_id=lead.id)
