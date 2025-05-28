from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .models import Order, OrderItem

class ThankYouView(TemplateView):
    """
    عرض صفحة الشكر - يعرض صفحة الشكر بعد إتمام الطلب بنجاح
    Thank you view - displays the thank you page after successful order completion
    """
    template_name = 'orders/thank_you.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order_id = self.kwargs.get('order_id')
        if order_id:
            try:
                # الحصول على الطلب - Get the order
                order = Order.objects.get(id=order_id)

                # التحقق من أن الطلب ينتمي إلى المستخدم الحالي إذا كان مسجل الدخول
                # Check that the order belongs to the current user if logged in
                if self.request.user.is_authenticated:
                    if order.user and order.user != self.request.user:
                        order = None

                context['order'] = order
            except Order.DoesNotExist:
                context['order'] = None

        return context

class OrderListView(LoginRequiredMixin, ListView):
    """
    عرض قائمة الطلبات - يعرض قائمة طلبات المستخدم
    Order list view - displays a list of user orders
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # الحصول على طلبات المستخدم الحالي فقط - Get only current user's orders
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    عرض تفاصيل الطلب - يعرض تفاصيل طلب معين
    Order detail view - displays details of a specific order
    """
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        # الحصول على طلبات المستخدم الحالي فقط - Get only current user's orders
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على عناصر الطلب - Get order items
        context['order_items'] = self.object.items.all()

        return context

class TrackOrderView(TemplateView):
    """
    عرض تتبع الطلب - يتيح للمستخدمين تتبع حالة طلباتهم باستخدام رقم الطلب
    Track order view - allows users to track their order status using the order number
    """
    template_name = 'orders/track_order.html'

    def get(self, request):
        # التحقق مما إذا تم تقديم رقم الطلب - Check if order number is provided
        order_number = request.GET.get('order_number')
        email = request.GET.get('email')

        order = None

        if order_number and email:
            # البحث عن الطلب - Search for the order
            try:
                order = Order.objects.get(order_number=order_number, email=email)
            except Order.DoesNotExist:
                messages.error(request, _('لم يتم العثور على الطلب. يرجى التحقق من رقم الطلب والبريد الإلكتروني.'))

        return render(request, self.template_name, {'order': order})

    def post(self, request):
        # الحصول على رقم الطلب والبريد الإلكتروني - Get order number and email
        order_number = request.POST.get('order_number')
        email = request.POST.get('email')

        if not order_number or not email:
            messages.error(request, _('يرجى إدخال رقم الطلب والبريد الإلكتروني.'))
            return render(request, self.template_name)

        # البحث عن الطلب - Search for the order
        try:
            order = Order.objects.get(order_number=order_number, email=email)

            # إرجاع النموذج مع معلومات الطلب - Return template with order info
            return render(request, self.template_name, {'order': order})
        except Order.DoesNotExist:
            messages.error(request, _('لم يتم العثور على الطلب. يرجى التحقق من رقم الطلب والبريد الإلكتروني.'))
            return render(request, self.template_name)