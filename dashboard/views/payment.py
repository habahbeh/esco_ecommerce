# dashboard/views/payment.py
"""
عروض إدارة المدفوعات والمعاملات المالية
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator

from payment.models import Transaction, Payment, Refund
from orders.models import Order
from dashboard.forms.payment import PaymentRefundForm, PaymentTransactionForm, PaymentForm
from dashboard.mixins import DashboardAccessMixin, AjaxableResponseMixin

import json
from decimal import Decimal


class TransactionListView(DashboardAccessMixin, ListView):
    """عرض قائمة المعاملات المالية"""
    model = Transaction
    template_name = 'dashboard/payment/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    permission_required = 'payment.view_transaction'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'order')

        # البحث
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(reference_number__icontains=search_query) |
                Q(gateway_transaction_id__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(order__order_number__icontains=search_query)
            )

        # الفلترة
        transaction_type = self.request.GET.get('transaction_type', '')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        payment_gateway = self.request.GET.get('payment_gateway', '')
        if payment_gateway:
            queryset = queryset.filter(payment_gateway=payment_gateway)

        # فلترة التاريخ
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)

        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        # الترتيب
        sort_by = self.request.GET.get('sort_by', '-created_at')
        queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات المعاملات
        context['total_transactions'] = Transaction.objects.count()
        context['completed_transactions'] = Transaction.objects.filter(status='completed').count()
        context['failed_transactions'] = Transaction.objects.filter(status='failed').count()
        context['total_amount'] = Transaction.objects.filter(status='completed').aggregate(Sum('amount'))[
                                      'amount__sum'] or 0

        # قائمة أنواع المعاملات
        context['transaction_types'] = dict(Transaction.TRANSACTION_TYPES)
        context['transaction_statuses'] = dict(Transaction.TRANSACTION_STATUS)

        # معلومات التصفية والبحث
        context['search_query'] = self.request.GET.get('search', '')
        context['current_type'] = self.request.GET.get('transaction_type', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_gateway'] = self.request.GET.get('payment_gateway', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')

        # بوابات الدفع المتاحة
        context['payment_gateways'] = Transaction.objects.values_list('payment_gateway', flat=True).distinct()

        return context

class TransactionDetailView(DashboardAccessMixin, DetailView):
    """عرض تفاصيل المعاملة المالية"""
    model = Transaction
    template_name = 'dashboard/payment/transaction_detail.html'
    context_object_name = 'transaction'
    permission_required = 'payment.view_transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحضار المعاملات المرتبطة
        transaction = self.get_object()

        # الدفع المرتبط (إن وجد)
        context['payment'] = getattr(transaction, 'payment', None)

        # طلب استرداد مرتبط (إن وجد)
        context['refund'] = getattr(transaction, 'refund', None)

        # المعاملات المرتبطة بنفس الطلب
        if transaction.order:
            context['related_transactions'] = Transaction.objects.filter(
                order=transaction.order
            ).exclude(pk=transaction.pk).order_by('-created_at')

        # تنسيق بيانات استجابة البوابة
        if transaction.gateway_response:
            try:
                context['formatted_response'] = json.dumps(transaction.gateway_response, indent=4, ensure_ascii=False)
            except:
                context['formatted_response'] = str(transaction.gateway_response)

        return context


class UpdateTransactionStatusView(DashboardAccessMixin, UpdateView):
    model = Transaction
    template_name = 'dashboard/payment/transaction_status_update.html'
    fields = ['status', 'notes']
    context_object_name = 'transaction'
    permission_required = 'payment.change_transaction'

    def get_success_url(self):
        return reverse_lazy('dashboard:transaction_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        transaction = form.save(commit=False)
        old_status = Transaction.objects.get(pk=transaction.pk).status
        new_status = form.cleaned_data['status']

        # إذا تم تغيير الحالة إلى 'مكتملة'، تحديث تاريخ الإكمال
        if new_status == 'completed' and old_status != 'completed':
            transaction.completed_at = timezone.now()

            # تحديث حالة الدفع المرتبط إذا وجد
            payment = getattr(transaction, 'payment', None)
            if payment:
                payment.status = 'paid'
                payment.paid_at = transaction.completed_at
                payment.save()

            # تحديث حالة الطلب المرتبط إذا وجد
            if transaction.order:
                transaction.order.payment_status = 'paid'
                transaction.order.save(update_fields=['payment_status'])

        transaction.save()
        messages.success(self.request, _('تم تحديث حالة المعاملة بنجاح'))
        return super().form_valid(form)


class TransactionCreateView(DashboardAccessMixin, CreateView):
    """إنشاء معاملة مالية جديدة"""
    model = Transaction
    template_name = 'dashboard/payment/transaction_form.html'
    form_class = PaymentTransactionForm
    permission_required = 'payment.add_transaction'

    def get_success_url(self):
        return reverse_lazy('dashboard:transaction_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # إضافة الطلب إلى الدالة إذا تم تمريره
        order_id = self.request.GET.get('order_id')
        if order_id:
            kwargs['order'] = get_object_or_404(Order, pk=order_id)

        return kwargs

    def form_valid(self, form):
        transaction = form.save(commit=False)

        # توليد رقم مرجع إذا لم يتم تحديده
        if not transaction.reference_number:
            transaction.reference_number = transaction.generate_reference_number()

        # تسجيل معلومات المستخدم
        transaction.ip_address = self.request.META.get('REMOTE_ADDR', '')
        transaction.user_agent = self.request.META.get('HTTP_USER_AGENT', '')

        # إذا كانت الحالة مكتملة، تعيين تاريخ الإكمال
        if transaction.status == 'completed':
            transaction.completed_at = timezone.now()

        transaction.save()
        messages.success(self.request, _('تم إنشاء المعاملة المالية بنجاح'))
        return super().form_valid(form)


class PaymentListView(DashboardAccessMixin, ListView):
    """عرض قائمة المدفوعات"""
    model = Payment
    template_name = 'dashboard/payment/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    permission_required = 'payment.view_payment'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'order', 'transaction')

        # البحث
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(gateway_payment_id__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(order__order_number__icontains=search_query)
            )

        # الفلترة
        payment_method = self.request.GET.get('payment_method', '')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        # فلترة التاريخ
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)

        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        # الترتيب
        sort_by = self.request.GET.get('sort_by', '-created_at')
        queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات المدفوعات
        context['total_payments'] = Payment.objects.count()
        context['paid_payments'] = Payment.objects.filter(status='paid').count()
        context['pending_payments'] = Payment.objects.filter(status='pending').count()
        context['total_amount'] = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0

        # قائمة طرق الدفع والحالات
        context['payment_methods'] = dict(Payment.PAYMENT_METHODS)
        context['payment_statuses'] = dict(Payment.PAYMENT_STATUS)

        # معلومات التصفية والبحث
        context['search_query'] = self.request.GET.get('search', '')
        context['current_method'] = self.request.GET.get('payment_method', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')

        return context


class PaymentDetailView(DashboardAccessMixin, DetailView):
    """عرض تفاصيل عملية الدفع"""
    model = Payment
    template_name = 'dashboard/payment/payment_detail.html'
    context_object_name = 'payment'
    permission_required = 'payment.view_payment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        payment = self.get_object()

        # المعاملة المرتبطة
        context['transaction'] = payment.transaction

        # الطلب المرتبط
        context['order'] = payment.order

        # عمليات استرداد المبلغ
        context['refunds'] = payment.refunds.all().order_by('-created_at')

        # حساب المبلغ المسترد الإجمالي
        total_refunded = payment.refunds.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_refunded'] = total_refunded

        # المبلغ المتبقي القابل للاسترداد
        context['refundable_amount'] = max(0, payment.amount - total_refunded)

        # تنسيق بيانات استجابة البوابة
        if payment.gateway_response:
            try:
                context['formatted_response'] = json.dumps(payment.gateway_response, indent=4, ensure_ascii=False)
            except:
                context['formatted_response'] = str(payment.gateway_response)

        return context


class PaymentUpdateStatusView(DashboardAccessMixin, UpdateView):
    """تحديث حالة عملية الدفع"""
    model = Payment
    template_name = 'dashboard/payment/payment_status_update.html'
    fields = ['status', 'notes']
    context_object_name = 'payment'
    permission_required = 'payment.change_payment'

    def get_success_url(self):
        return reverse_lazy('dashboard:payment_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        payment = form.save(commit=False)
        old_status = Payment.objects.get(pk=payment.pk).status
        new_status = form.cleaned_data['status']

        # إذا تم تغيير الحالة إلى 'مدفوع'، تحديث تاريخ الدفع
        if new_status == 'paid' and old_status != 'paid':
            payment.paid_at = timezone.now()

            # تحديث حالة المعاملة المرتبطة
            if payment.transaction:
                payment.transaction.status = 'completed'
                payment.transaction.completed_at = payment.paid_at
                payment.transaction.save()

            # تحديث حالة الطلب
            if payment.order:
                payment.order.payment_status = 'paid'
                payment.order.save(update_fields=['payment_status'])

            # إنشاء معاملة مالية إذا لم تكن موجودة
            if not payment.transaction:
                payment.create_transaction()

        payment.save()
        messages.success(self.request, _('تم تحديث حالة الدفع بنجاح'))
        return super().form_valid(form)


class PaymentCreateView( DashboardAccessMixin, CreateView):
    """إنشاء عملية دفع جديدة"""
    model = Payment
    template_name = 'dashboard/payment/payment_form.html'
    form_class = PaymentForm
    permission_required = 'payment.add_payment'

    def get_success_url(self):
        return reverse_lazy('dashboard:payment_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # إضافة الطلب إلى الدالة إذا تم تمريره
        order_id = self.request.GET.get('order_id')
        if order_id:
            kwargs['order'] = get_object_or_404(Order, pk=order_id)

        return kwargs

    def form_valid(self, form):
        payment = form.save(commit=False)

        # تسجيل معلومات المستخدم
        payment.ip_address = self.request.META.get('REMOTE_ADDR', '')

        # إذا كانت الحالة مدفوع، تعيين تاريخ الدفع
        if payment.status == 'paid':
            payment.paid_at = timezone.now()

        payment.save()

        # إنشاء معاملة مالية مرتبطة
        payment.create_transaction()

        messages.success(self.request, _('تم إنشاء عملية الدفع بنجاح'))
        return super().form_valid(form)


class RefundListView( DashboardAccessMixin, ListView):
    """عرض قائمة طلبات استرداد المبالغ"""
    model = Refund
    template_name = 'dashboard/payment/refund_list.html'
    context_object_name = 'refunds'
    paginate_by = 20
    permission_required = 'payment.view_refund'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'payment', 'order')

        # البحث
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(gateway_refund_id__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(order__order_number__icontains=search_query)
            )

        # الفلترة
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        reason = self.request.GET.get('reason', '')
        if reason:
            queryset = queryset.filter(reason=reason)

        # فلترة التاريخ
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)

        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        # الترتيب
        sort_by = self.request.GET.get('sort_by', '-created_at')
        queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات طلبات الاسترداد
        context['total_refunds'] = Refund.objects.count()
        context['completed_refunds'] = Refund.objects.filter(status='completed').count()
        context['pending_refunds'] = Refund.objects.filter(status='pending').count()
        context['total_amount'] = Refund.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0

        # قائمة أسباب الاسترداد والحالات
        context['refund_reasons'] = dict(Refund.REFUND_REASONS)
        context['refund_statuses'] = dict(Refund.REFUND_STATUS)

        # معلومات التصفية والبحث
        context['search_query'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_reason'] = self.request.GET.get('reason', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')

        return context


class RefundDetailView( DashboardAccessMixin, DetailView):
    """عرض تفاصيل طلب استرداد المبلغ"""
    model = Refund
    template_name = 'dashboard/payment/refund_detail.html'
    context_object_name = 'refund'
    permission_required = 'payment.view_refund'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        refund = self.get_object()

        # الدفع المرتبط
        context['payment'] = refund.payment

        # الطلب المرتبط
        context['order'] = refund.order

        # المعاملة المرتبطة
        context['transaction'] = refund.transaction

        # تنسيق بيانات استجابة البوابة
        if refund.gateway_response:
            try:
                context['formatted_response'] = json.dumps(refund.gateway_response, indent=4, ensure_ascii=False)
            except:
                context['formatted_response'] = str(refund.gateway_response)

        return context


class RefundCreateView(DashboardAccessMixin, CreateView):
    """إنشاء طلب استرداد مبلغ جديد"""
    model = Refund
    template_name = 'dashboard/payment/refund_form.html'
    form_class = PaymentRefundForm
    permission_required = 'payment.add_refund'

    def get_success_url(self):
        return reverse_lazy('dashboard:refund_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # إضافة معلومات الدفع إلى النموذج
        payment_id = self.kwargs.get('payment_id')
        if payment_id:
            kwargs['payment'] = get_object_or_404(Payment, pk=payment_id)

        # إضافة المستخدم الحالي
        kwargs['user'] = self.request.user

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة معلومات الدفع المرتبط
        payment_id = self.kwargs.get('payment_id')
        if payment_id:
            payment = get_object_or_404(Payment, pk=payment_id)
            context['payment'] = payment

            # المبلغ المسترد بالفعل
            total_refunded = payment.refunds.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
            context['total_refunded'] = total_refunded

            # المبلغ المتبقي القابل للاسترداد
            context['refundable_amount'] = max(0, payment.amount - total_refunded)

        return context

    def form_valid(self, form):
        refund = form.save(commit=False)

        # تسجيل المستخدم الذي قام بطلب الاسترداد
        refund.requested_by = self.request.user

        refund.save()

        # إنشاء معاملة مالية للاسترداد
        refund.create_transaction()

        messages.success(self.request, _('تم إنشاء طلب استرداد المبلغ بنجاح'))
        return super().form_valid(form)


class RefundUpdateStatusView(DashboardAccessMixin, UpdateView):
    """تحديث حالة طلب استرداد المبلغ"""
    model = Refund
    template_name = 'dashboard/payment/refund_status_update.html'
    fields = ['status', 'admin_notes']
    context_object_name = 'refund'
    permission_required = 'payment.change_refund'

    def get_success_url(self):
        return reverse_lazy('dashboard:refund_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        refund = form.save(commit=False)
        old_status = Refund.objects.get(pk=refund.pk).status
        new_status = form.cleaned_data['status']

        # إذا تم تغيير الحالة إلى 'مكتمل'، تحديث تاريخ الإكمال
        if new_status == 'completed' and old_status != 'completed':
            refund.completed_at = timezone.now()
            refund.processed_by = self.request.user

            # تحديث حالة المعاملة المرتبطة
            if refund.transaction:
                refund.transaction.status = 'completed'
                refund.transaction.completed_at = refund.completed_at
                refund.transaction.save()

            # تحديث حالة الدفع المرتبط
            if refund.payment:
                # التحقق مما إذا كان الاسترداد كاملاً أو جزئياً
                total_refunded = Refund.objects.filter(
                    payment=refund.payment,
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or 0

                if total_refunded + refund.amount >= refund.payment.amount:
                    refund.payment.status = 'refunded'
                else:
                    refund.payment.status = 'partially_refunded'

                refund.payment.save(update_fields=['status'])

            # تحديث حالة الطلب إذا كان الاسترداد كاملاً
            if refund.order and refund.amount >= refund.payment.amount:
                refund.order.payment_status = 'refunded'
                refund.order.save(update_fields=['payment_status'])

        refund.save()
        messages.success(self.request, _('تم تحديث حالة طلب الاسترداد بنجاح'))
        return super().form_valid(form)


class PaymentDashboardView(DashboardAccessMixin, TemplateView):
    """لوحة معلومات المدفوعات والإحصائيات"""
    template_name = 'dashboard/payment/dashboard.html'
    permission_required = 'payment.view_payment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات المدفوعات
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timezone.timedelta(days=1)
        last_week = today - timezone.timedelta(days=7)
        last_month = today - timezone.timedelta(days=30)

        # المدفوعات حسب الفترة
        context['today_payments'] = Payment.objects.filter(
            created_at__gte=today
        ).aggregate(
            count=Count('id'),
            amount=Sum('amount')
        )

        context['today_payments']['amount'] = context['today_payments']['amount'] or 0

        context['yesterday_payments'] = Payment.objects.filter(
            created_at__gte=yesterday,
            created_at__lt=today
        ).aggregate(
            count=Count('id'),
            amount=Sum('amount')
        )

        context['yesterday_payments']['amount'] = context['yesterday_payments']['amount'] or 0

        context['weekly_payments'] = Payment.objects.filter(
            created_at__gte=last_week
        ).aggregate(
            count=Count('id'),
            amount=Sum('amount')
        )

        context['weekly_payments']['amount'] = context['weekly_payments']['amount'] or 0

        context['monthly_payments'] = Payment.objects.filter(
            created_at__gte=last_month
        ).aggregate(
            count=Count('id'),
            amount=Sum('amount')
        )

        context['monthly_payments']['amount'] = context['monthly_payments']['amount'] or 0

        # المدفوعات حسب طرق الدفع
        payment_methods_data = Payment.objects.filter(
            status='paid'
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total')

        context['payment_methods_data'] = payment_methods_data
        context['payment_methods_dict'] = dict(Payment.PAYMENT_METHODS)

        # أحدث المدفوعات
        context['recent_payments'] = Payment.objects.select_related(
            'user', 'order'
        ).order_by('-created_at')[:10]

        # أحدث طلبات الاسترداد
        context['recent_refunds'] = Refund.objects.select_related(
            'user', 'payment', 'order'
        ).order_by('-created_at')[:10]

        return context


class PaymentAPIView(DashboardAccessMixin, View):
    """واجهة برمجية للحصول على بيانات المدفوعات للرسوم البيانية"""
    permission_required = 'payment.view_payment'

    def get(self, request, *args, **kwargs):
        chart_type = request.GET.get('chart', 'daily')

        if chart_type == 'daily':
            # إحصائيات يومية للأيام الـ 30 الماضية
            end_date = timezone.now().replace(hour=23, minute=59, second=59)
            start_date = end_date - timezone.timedelta(days=29)

            # تهيئة مصفوفة البيانات
            dates = []
            data = {
                'dates': [],
                'payments': [],
                'refunds': []
            }

            # توليد التواريخ
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')

                # إحصائيات المدفوعات
                payments_amount = Payment.objects.filter(
                    created_at__date=current_date.date(),
                    status='paid'
                ).aggregate(total=Sum('amount'))['total'] or 0

                # إحصائيات الاسترداد
                refunds_amount = Refund.objects.filter(
                    created_at__date=current_date.date(),
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or 0

                # إضافة البيانات
                data['dates'].append(date_str)
                data['payments'].append(float(payments_amount))
                data['refunds'].append(float(refunds_amount))

                # الانتقال إلى اليوم التالي
                current_date += timezone.timedelta(days=1)

            return JsonResponse(data)

        elif chart_type == 'monthly':
            # إحصائيات شهرية للأشهر الـ 12 الماضية
            today = timezone.now()

            # تهيئة مصفوفة البيانات
            data = {
                'months': [],
                'payments': [],
                'refunds': []
            }

            # توليد الأشهر
            for i in range(11, -1, -1):
                # حساب الشهر
                month_date = today.replace(day=1) - timezone.timedelta(days=i * 30)
                month_str = month_date.strftime('%Y-%m')
                month_name = month_date.strftime('%b %Y')

                # حساب اليوم الأول والأخير من الشهر
                first_day = month_date.replace(day=1)
                if month_date.month == 12:
                    last_day = month_date.replace(year=month_date.year + 1, month=1, day=1) - timezone.timedelta(days=1)
                else:
                    last_day = month_date.replace(month=month_date.month + 1, day=1) - timezone.timedelta(days=1)

                # إحصائيات المدفوعات
                payments_amount = Payment.objects.filter(
                    created_at__gte=first_day,
                    created_at__lte=last_day,
                    status='paid'
                ).aggregate(total=Sum('amount'))['total'] or 0

                # إحصائيات الاسترداد
                refunds_amount = Refund.objects.filter(
                    created_at__gte=first_day,
                    created_at__lte=last_day,
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or 0

                # إضافة البيانات
                data['months'].append(month_name)
                data['payments'].append(float(payments_amount))
                data['refunds'].append(float(refunds_amount))

            return JsonResponse(data)

        elif chart_type == 'payment_methods':
            # إحصائيات طرق الدفع
            payment_methods = Payment.objects.filter(
                status='paid'
            ).values('payment_method').annotate(
                total=Sum('amount')
            ).order_by('-total')

            data = {
                'labels': [],
                'data': []
            }

            payment_methods_dict = dict(Payment.PAYMENT_METHODS)

            for method in payment_methods:
                method_name = payment_methods_dict.get(method['payment_method'], method['payment_method'])
                data['labels'].append(method_name)
                data['data'].append(float(method['total']))

            return JsonResponse(data)

        # في حالة عدم تحديد نوع الرسم البياني، إرجاع بيانات فارغة
        return JsonResponse({})