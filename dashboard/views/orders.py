# views/orders.py
# عروض إدارة الطلبات

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
import json
import csv
from decimal import Decimal
from datetime import datetime, timedelta
from orders.models import Order, OrderItem
from accounts.models import User, UserAddress
from products.models import Product, ProductVariant
from .dashboard import DashboardAccessMixin
from django.core.mail import send_mail
from django.conf import settings
from django.utils.decorators import method_decorator
from dashboard.decorators import permission_required

# ========================= قائمة الطلبات =========================

@method_decorator(permission_required('orders.view_order'), name='dispatch')
class OrderListView(DashboardAccessMixin, View):
    """عرض قائمة الطلبات مع البحث والتصفية"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        status_filter = request.GET.get('status', '')
        payment_filter = request.GET.get('payment_status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # قائمة الطلبات مع استعلام مُحسّن
        orders = Order.objects.select_related('user').order_by('-created_at')

        # تطبيق البحث
        if query:
            orders = orders.filter(
                Q(order_number__icontains=query) |
                Q(full_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )

        # تطبيق التصفية حسب الحالة
        if status_filter:
            orders = orders.filter(status=status_filter)

        # تطبيق التصفية حسب حالة الدفع
        if payment_filter:
            orders = orders.filter(payment_status=payment_filter)

        # تطبيق التصفية حسب التاريخ
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                orders = orders.filter(created_at__date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                orders = orders.filter(created_at__date__lte=date_to)
            except ValueError:
                pass

        # التصفح الجزئي
        paginator = Paginator(orders, 20)  # 20 طلب في كل صفحة
        page = request.GET.get('page', 1)
        orders_page = paginator.get_page(page)

        # الإحصائيات
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        confirmed_orders = Order.objects.filter(status='confirmed').count()
        closed_orders = Order.objects.filter(status='closed').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()

        # إجمالي المبيعات (فقط للطلبات المؤكدة والمغلقة)
        total_sales = Order.objects.filter(
            status__in=['confirmed', 'closed']
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        # مبيعات اليوم
        today = timezone.now().date()
        today_sales = Order.objects.filter(
            created_at__date=today
        ).aggregate(total=Sum('grand_total'))['total'] or 0

        stats = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'confirmed_orders': confirmed_orders,
            'closed_orders': closed_orders,
            'cancelled_orders': cancelled_orders,
            'total_sales': total_sales,
            'today_sales': today_sales
        }

        context = {
            'orders': orders_page,
            'query': query,
            'status_filter': status_filter,
            'payment_filter': payment_filter,
            'date_from': date_from,
            'date_to': date_to,
            'stats': stats,
            'status_choices': Order.STATUS_CHOICES,
            'payment_status_choices': Order.PAYMENT_STATUS_CHOICES
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/orders/orders_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': orders_page.has_next(),
                'has_prev': orders_page.has_previous(),
                'page': orders_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/orders/order_list.html', context)


# ========================= تفاصيل الطلب =========================
@method_decorator(permission_required('orders.view_order'), name='dispatch')
class OrderDetailView(DashboardAccessMixin, View):
    """عرض تفاصيل الطلب"""

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        # جلب عناصر الطلب
        order_items = order.items.all().select_related('product', 'variant')

        # حساب الإحصائيات
        order_stats = {
            'item_count': order_items.count(),
            'items_total': order_items.aggregate(total=Sum('total_price'))['total'] or 0,
        }

        # سجل الطلب (الأحداث)
        # في بيئة حقيقية، قد تكون هناك جداول منفصلة لسجل الأحداث
        order_log = []

        # تحويل العناوين إلى تنسيق قابل للقراءة
        shipping_address = {
            'address': order.shipping_address,
            'city': order.shipping_city,
            'state': order.shipping_state,
            'country': order.shipping_country,
            'postal_code': order.shipping_postal_code,
        }

        # معلومات المستخدم (إذا كان موجودًا)
        user_info = None
        if order.user:
            user = order.user
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone_number,
                'orders_count': user.orders.count(),
                'total_spent': user.total_spent,
            }

        # معلومات الدفع
        payment_info = {
            'method': order.payment_method,
            'status': order.payment_status,
            'id': order.payment_id,
        }

        # جلب المدفوعات المرتبطة (إذا كانت موجودة)
        payments = []
        if hasattr(order, 'payments'):
            payments = order.payments.all().order_by('-created_at')

        context = {
            'order': order,
            'order_items': order_items,
            'order_stats': order_stats,
            'shipping_address': shipping_address,
            'user_info': user_info,
            'payment_info': payment_info,
            'payments': payments,
            'order_log': order_log,
            'status_choices': Order.STATUS_CHOICES,
            'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
            'MEDIA_URL': settings.MEDIA_URL,
        }

        return render(request, 'dashboard/orders/order_detail.html', context)


# ========================= تحديث حالة الطلب =========================

@method_decorator(permission_required('orders.change_order'), name='dispatch')
class OrderUpdateStatusView(DashboardAccessMixin, View):
    """تحديث حالة الطلب"""

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        new_status = request.POST.get('status')
        if not new_status or new_status not in dict(Order.STATUS_CHOICES):
            messages.error(request, 'الرجاء تحديد حالة صحيحة')
            return redirect('dashboard:dashboard_order_detail', order_id=order.id)

        # تحديث الحالة
        old_status = order.status
        order.status = new_status

        # إضافة ملاحظات إذا وجدت
        status_notes = request.POST.get('status_notes', '')
        if status_notes:
            order.notes = f"{order.notes}\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] تغيير الحالة من {old_status} إلى {new_status}: {status_notes}"

        # تحديث تاريخ التحديث
        order.updated_at = timezone.now()

        # إجراءات إضافية حسب نوع التغيير
        if new_status == 'confirmed' and old_status == 'pending':
            # تأكيد الطلب بعد التحقق من وصل الدفع
            # تحديث حالة الدفع أيضاً
            order.payment_status = 'paid'

            # إرسال إشعار للعميل
            notify_customer = request.POST.get('notify_customer') == 'on'
            if notify_customer:
                self.send_order_status_email(order, 'confirmed')

        elif new_status == 'closed' and old_status == 'confirmed':
            # إغلاق الطلب للتوصيل - الدفع يبقى كما هو
            pass

        elif new_status == 'cancelled':
            # إذا كان الإلغاء بسبب مشكلة في الدفع، نحدث حالة الدفع
            payment_issue = request.POST.get('payment_issue') == 'on'
            if payment_issue:
                order.payment_status = 'failed'

            # إلغاء الطلب وإعادة المخزون إذا لزم الأمر
            if old_status in ['confirmed', 'closed']:
                # إعادة المخزون فقط إذا كان الطلب مؤكداً سابقاً
                for item in order.items.all():
                    if hasattr(item, 'product') and item.product and item.product.track_inventory:
                        product = item.product
                        product.stock_quantity += item.quantity
                        product.save()

                        # إذا كان هناك متغير
                        if hasattr(item, 'variant') and item.variant and item.variant.track_inventory:
                            variant = item.variant
                            variant.stock_quantity += item.quantity
                            variant.save()

            # إرسال إشعار بالإلغاء إذا كان الخيار مفعلاً
            notify_customer = request.POST.get('notify_customer') == 'on'
            if notify_customer:
                self.send_order_status_email(order, 'cancelled')

        # حفظ التغييرات
        order.save()

        messages.success(request, f'تم تحديث حالة الطلب إلى {dict(Order.STATUS_CHOICES)[new_status]}')
        return redirect('dashboard:dashboard_order_detail', order_id=order.id)

    def send_order_status_email(self, order, status):
        """إرسال بريد إلكتروني للعميل عند تغيير حالة الطلب"""
        subject = f'تحديث حالة الطلب #{order.order_number}'

        # تحديد الرسالة حسب الحالة
        if status == 'confirmed':
            message_title = 'تم تأكيد طلبك'
            message_content = 'نود إعلامك أن طلبك قد تم تأكيده بعد التحقق من الدفع. سنقوم بالتواصل معك قريباً لإكمال عملية التوصيل.'
        elif status == 'closed':
            message_title = 'طلبك جاهز للتوصيل'
            message_content = 'نود إعلامك أن طلبك جاهز للتوصيل وسيتم تسليمه قريباً.'
        elif status == 'cancelled':
            message_title = 'تم إلغاء طلبك'
            message_content = 'نأسف لإعلامك أنه تم إلغاء طلبك. يرجى التواصل مع خدمة العملاء للمزيد من المعلومات.'
        else:
            # لا نرسل بريداً لحالات أخرى
            return

        # إعداد رسالة البريد
        plain_message = f"""
        {message_title}

        {message_content}

        رقم الطلب: {order.order_number}
        الإجمالي: {order.grand_total} د.أ

        شكراً لثقتكم بنا.
        فريق خدمة العملاء
        """

        # استخدام قيمة افتراضية إذا لم يكن الإعداد موجوداً
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

        # إرسال البريد
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[order.email],
            fail_silently=True
        )

# ========================= تحديث حالة الدفع =========================

@method_decorator(permission_required('orders.change_order'), name='dispatch')
class OrderUpdatePaymentStatusView(DashboardAccessMixin, View):
    """تحديث حالة دفع الطلب"""

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        new_payment_status = request.POST.get('payment_status')
        if not new_payment_status or new_payment_status not in dict(Order.PAYMENT_STATUS_CHOICES):
            messages.error(request, 'الرجاء تحديد حالة دفع صحيحة')
            return redirect('dashboard:dashboard_order_detail', order_id=order.id)

        # تحديث حالة الدفع
        old_payment_status = order.payment_status
        order.payment_status = new_payment_status

        # إضافة ملاحظات إذا وجدت
        payment_notes = request.POST.get('payment_notes', '')
        if payment_notes:
            order.notes = f"{order.notes}\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] تغيير حالة الدفع من {old_payment_status} إلى {new_payment_status}: {payment_notes}"

        # تحديث تاريخ التحديث
        order.updated_at = timezone.now()

        # حفظ التغييرات
        order.save()

        messages.success(request, f'تم تحديث حالة الدفع إلى {dict(Order.PAYMENT_STATUS_CHOICES)[new_payment_status]}')
        return redirect('dashboard:dashboard_order_detail', order_id=order.id)


# ========================= إلغاء الطلب =========================

@method_decorator(permission_required('orders.change_order'), name='dispatch')
class OrderCancelView(DashboardAccessMixin, View):
    """إلغاء الطلب"""

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        # التحقق من إمكانية إلغاء الطلب
        if order.status in ['delivered', 'refunded', 'cancelled']:
            messages.error(request, 'لا يمكن إلغاء هذا الطلب في حالته الحالية')
            return redirect('dashboard:dashboard_order_detail', order_id=order.id)

        # إلغاء الطلب
        old_status = order.status
        order.status = 'cancelled'

        # إضافة ملاحظات إذا وجدت
        cancel_reason = request.POST.get('cancel_reason', '')
        if cancel_reason:
            order.notes = f"{order.notes}\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] تم إلغاء الطلب: {cancel_reason}"

        # تحديث تاريخ التحديث
        order.updated_at = timezone.now()

        # حفظ التغييرات
        order.save()

        # إعادة المخزون
        for item in order.items.all():
            if hasattr(item, 'product') and item.product:
                product = item.product
                if product.track_inventory:
                    product.stock_quantity += item.quantity
                    product.save()

                # إذا كان هناك متغير
                if hasattr(item, 'variant') and item.variant:
                    variant = item.variant
                    if variant.track_inventory:
                        variant.stock_quantity += item.quantity
                        variant.save()

        messages.success(request, 'تم إلغاء الطلب بنجاح')
        return redirect('dashboard:dashboard_order_detail', order_id=order.id)


# ========================= طباعة الطلب =========================

@method_decorator(permission_required('orders.view_order'), name='dispatch')
class OrderPrintView(DashboardAccessMixin, View):
    """طباعة تفاصيل الطلب وتحديث الحالة إلى 'إغلاق الطلب'"""

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        # تحديث حالة الطلب إلى "مغلق" إذا كان مؤكداً
        if order.status == 'confirmed':
            order.status = 'closed'
            order.notes = f"{order.notes}\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] تم إغلاق الطلب للتوصيل"
            order.save()

        # جلب عناصر الطلب
        order_items = order.items.all().select_related('product', 'variant')


        # تحويل العناوين إلى تنسيق قابل للقراءة
        shipping_address = {
            'address': order.shipping_address,
            'city': order.shipping_city,
            'state': order.shipping_state,
            'country': order.shipping_country,
            'postal_code': order.shipping_postal_code,
        }

        context = {
            'order': order,
            'order_items': order_items,
            'shipping_address': shipping_address,
        }

        return render(request, 'dashboard/orders/order_print.html', context)

# ========================= إنشاء طلب جديد =========================

@method_decorator(permission_required('orders.add_order'), name='dispatch')
class OrderCreateView(DashboardAccessMixin, View):
    """إنشاء طلب جديد من لوحة التحكم"""

    def get(self, request):
        # جلب قائمة المستخدمين
        users = User.objects.all().order_by('username')

        # جلب قائمة المنتجات
        products = Product.objects.filter(is_active=True, status='published').order_by('name')

        context = {
            'users': users,
            'products': products,
            'status_choices': Order.STATUS_CHOICES,
            'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
        }

        return render(request, 'dashboard/orders/order_create.html', context)

    def post(self, request):
        # جمع البيانات من النموذج
        user_id = request.POST.get('user_id')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        # عنوان الشحن
        shipping_address = request.POST.get('shipping_address')
        shipping_city = request.POST.get('shipping_city')
        shipping_state = request.POST.get('shipping_state')
        shipping_country = request.POST.get('shipping_country')
        shipping_postal_code = request.POST.get('shipping_postal_code')

        # حالة الطلب والدفع
        status = request.POST.get('status', 'pending')
        payment_status = request.POST.get('payment_status', 'pending')
        payment_method = request.POST.get('payment_method', '')

        # ملاحظات
        notes = request.POST.get('notes', '')

        # التحقق من البيانات المطلوبة
        if not full_name or not email or not shipping_address:
            messages.error(request, 'الرجاء ملء جميع الحقول المطلوبة')
            return redirect('dashboard_order_create')

        try:
            # إنشاء الطلب
            order = Order()

            # تعيين المستخدم إذا تم تحديده
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    order.user = user
                except User.DoesNotExist:
                    pass

            # تعيين بيانات العميل
            order.full_name = full_name
            order.email = email
            order.phone = phone

            # تعيين عنوان الشحن
            order.shipping_address = shipping_address
            order.shipping_city = shipping_city
            order.shipping_state = shipping_state
            order.shipping_country = shipping_country
            order.shipping_postal_code = shipping_postal_code

            # تعيين حالة الطلب والدفع
            order.status = status
            order.payment_status = payment_status
            order.payment_method = payment_method
            order.notes = notes

            # حفظ الطلب (سيتم توليد رقم الطلب تلقائيًا)
            order.total_price = Decimal('0.00')
            order.grand_total = Decimal('0.00')
            order.save()

            # إضافة عناصر الطلب
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            variants = request.POST.getlist('variant_id[]')

            if not product_ids:
                messages.error(request, 'يجب إضافة منتج واحد على الأقل إلى الطلب')
                order.delete()
                return redirect('dashboard_order_create')

            total_price = Decimal('0.00')

            for i in range(len(product_ids)):
                if i < len(quantities) and quantities[i]:
                    product_id = product_ids[i]
                    quantity = int(quantities[i])
                    variant_id = variants[i] if i < len(variants) and variants[i] else None

                    try:
                        product = Product.objects.get(id=product_id)

                        # جلب المتغير إذا كان موجودًا
                        variant = None
                        if variant_id:
                            try:
                                variant = ProductVariant.objects.get(id=variant_id, product=product)
                            except ProductVariant.DoesNotExist:
                                pass

                        # حساب السعر
                        unit_price = variant.current_price if variant else product.current_price
                        item_total = unit_price * quantity

                        # إنشاء عنصر الطلب
                        order_item = OrderItem.objects.create(
                            order=order,
                            product=product,
                            variant=variant,
                            product_name=product.name,
                            variant_name=variant.name if variant else '',
                            quantity=quantity,
                            unit_price=unit_price,
                            total_price=item_total
                        )

                        # تحديث إجمالي الطلب
                        total_price += item_total

                    except Product.DoesNotExist:
                        pass

            # حساب تكلفة الشحن والضرائب
            shipping_cost = Decimal(request.POST.get('shipping_cost', '0.00') or '0.00')
            tax_amount = Decimal(request.POST.get('tax_amount', '0.00') or '0.00')
            discount_amount = Decimal(request.POST.get('discount_amount', '0.00') or '0.00')

            # تحديث إجماليات الطلب
            order.total_price = total_price
            order.shipping_cost = shipping_cost
            order.tax_amount = tax_amount
            order.discount_amount = discount_amount
            order.grand_total = total_price + shipping_cost + tax_amount - discount_amount
            order.save()

            messages.success(request, f'تم إنشاء الطلب بنجاح برقم {order.order_number}')
            return redirect('dashboard:dashboard_order_detail', order_id=order.id)

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إنشاء الطلب: {str(e)}')
            return redirect('dashboard:dashboard_order_create')


# ========================= إحصائيات وتقارير الطلبات =========================

@method_decorator(permission_required('orders.view_order'), name='dispatch')
class OrderReportsView(DashboardAccessMixin, View):
    """عرض تقارير وإحصائيات الطلبات"""

    def get(self, request):
        report_type = request.GET.get('report_type', 'sales_overview')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # تحديد الفترة الزمنية الافتراضية (آخر 30 يوم)
        today = timezone.now().date()
        default_date_from = today - timedelta(days=30)
        default_date_to = today

        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                date_from = default_date_from
        else:
            date_from = default_date_from

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                date_to = default_date_to
        else:
            date_to = default_date_to

        # تقرير المبيعات العام
        if report_type == 'sales_overview':
            # إجمالي المبيعات في الفترة المحددة
            total_sales = Order.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).aggregate(
                total_orders=Count('id'),
                revenue=Sum('grand_total'),
                avg_order_value=Avg('grand_total')
            )

            # المبيعات حسب الحالة
            sales_by_status = Order.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).values('status').annotate(
                count=Count('id'),
                total=Sum('grand_total')
            ).order_by('status')

            # المبيعات حسب طريقة الدفع
            sales_by_payment = Order.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).values('payment_method').annotate(
                count=Count('id'),
                total=Sum('grand_total')
            ).order_by('-total')

            # المبيعات اليومية للرسم البياني
            daily_sales = []
            current_date = date_from
            while current_date <= date_to:
                day_sales = Order.objects.filter(
                    created_at__date=current_date
                ).aggregate(
                    count=Count('id'),
                    total=Sum('grand_total')
                )

                daily_sales.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'count': day_sales['count'] or 0,
                    'total': float(day_sales['total'] or 0)
                })

                current_date += timedelta(days=1)

            report_data = {
                'total_sales': total_sales,
                'sales_by_status': sales_by_status,
                'sales_by_payment': sales_by_payment,
                'daily_sales': daily_sales
            }

        # تقرير أفضل المنتجات مبيعًا
        elif report_type == 'top_products':
            # أفضل المنتجات مبيعًا
            top_products = OrderItem.objects.filter(
                order__created_at__date__gte=date_from,
                order__created_at__date__lte=date_to
            ).values('product_id', 'product_name').annotate(
                quantity_sold=Sum('quantity'),
                revenue=Sum('total_price')
            ).order_by('-quantity_sold')[:20]

            report_data = {
                'top_products': top_products
            }

        # تقرير أفضل العملاء
        elif report_type == 'top_customers':
            # أفضل العملاء
            top_customers = Order.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to,
                user__isnull=False
            ).values('user__id', 'user__username', 'user__email').annotate(
                orders_count=Count('id'),
                total_spent=Sum('grand_total')
            ).order_by('-total_spent')[:20]

            report_data = {
                'top_customers': top_customers
            }

        else:
            report_data = {}

        context = {
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
            'report_data': report_data
        }

        return render(request, 'dashboard/orders/order_reports.html', context)


# ========================= تصدير الطلبات =========================

@method_decorator(permission_required('orders.view_order'), name='dispatch')
class OrderExportView(DashboardAccessMixin, View):
    """تصدير الطلبات إلى ملفات CSV"""

    def get(self, request):
        format_type = request.GET.get('format', 'csv')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        status_filter = request.GET.get('status', '')

        # تحديد الفترة الزمنية
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                date_from = timezone.make_aware(datetime.combine(date_from, datetime.min.time()))
            except ValueError:
                date_from = None
        else:
            date_from = None

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                date_to = timezone.make_aware(datetime.combine(date_to, datetime.max.time()))
            except ValueError:
                date_to = None
        else:
            date_to = None

        # جلب الطلبات
        orders = Order.objects.all().order_by('-created_at')

        if date_from:
            orders = orders.filter(created_at__gte=date_from)

        if date_to:
            orders = orders.filter(created_at__lte=date_to)

        if status_filter:
            orders = orders.filter(status=status_filter)

        # تصدير بتنسيق CSV
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response[
                'Content-Disposition'] = f'attachment; filename="orders_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

            writer = csv.writer(response)

            # كتابة رأس الجدول
            writer.writerow([
                'Order Number', 'Date', 'Customer', 'Email', 'Status', 'Payment Status',
                'Total Items', 'Subtotal', 'Shipping', 'Tax', 'Discount', 'Grand Total'
            ])

            # كتابة بيانات الطلبات
            for order in orders:
                writer.writerow([
                    order.order_number,
                    order.created_at.strftime('%Y-%m-%d %H:%M'),
                    order.full_name,
                    order.email,
                    order.get_status_display(),
                    order.get_payment_status_display(),
                    order.items.aggregate(total=Sum('quantity'))['total'] or 0,
                    order.total_price,
                    order.shipping_cost,
                    order.tax_amount,
                    order.discount_amount,
                    order.grand_total
                ])

            return response

        else:
            # تنسيقات أخرى يمكن دعمها مستقبلاً (مثل Excel, PDF)
            messages.error(request, 'تنسيق التصدير غير مدعوم')
            return redirect('dashboard_orders')


# ========================= البحث عن الطلبات =========================

@method_decorator(permission_required('orders.view_order'), name='dispatch')
def order_search(request):
    """بحث سريع عن الطلبات (للاستخدام مع AJAX)"""

    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'غير مصرح لك بالوصول'}, status=403)

    query = request.GET.get('q', '')
    if not query or len(query) < 3:
        return JsonResponse({'results': []})

    # البحث في الطلبات
    orders = Order.objects.filter(
        Q(order_number__icontains=query) |
        Q(full_name__icontains=query) |
        Q(email__icontains=query) |
        Q(phone__icontains=query)
    ).order_by('-created_at')[:10]

    results = []
    for order in orders:
        results.append({
            'id': str(order.id),
            'order_number': order.order_number,
            'customer': order.full_name,
            'date': order.created_at.strftime('%Y-%m-%d'),
            'status': order.get_status_display(),
            'total': float(order.grand_total),
            'url': f'/dashboard/orders/{order.id}/'
        })

    return JsonResponse({'results': results})


# ========================= لوحة معلومات الطلبات =========================

@method_decorator(permission_required('orders.view_order'), name='dispatch')
class OrderDashboardView(DashboardAccessMixin, View):
    """لوحة معلومات الطلبات"""

    def get(self, request):
        # الإحصائيات العامة
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)

        # إحصائيات اليوم
        today_stats = Order.objects.filter(created_at__date=today).aggregate(
            count=Count('id'),
            revenue=Sum('grand_total'),
            avg_value=Avg('grand_total')
        )

        # إحصائيات الأمس
        yesterday_stats = Order.objects.filter(created_at__date=yesterday).aggregate(
            count=Count('id'),
            revenue=Sum('grand_total'),
            avg_value=Avg('grand_total')
        )

        # إحصائيات الشهر الحالي
        this_month_stats = Order.objects.filter(
            created_at__date__gte=this_month_start,
            created_at__date__lte=today
        ).aggregate(
            count=Count('id'),
            revenue=Sum('grand_total'),
            avg_value=Avg('grand_total')
        )

        # إحصائيات الشهر الماضي
        last_month_stats = Order.objects.filter(
            created_at__date__gte=last_month_start,
            created_at__date__lte=last_month_end
        ).aggregate(
            count=Count('id'),
            revenue=Sum('grand_total'),
            avg_value=Avg('grand_total')
        )

        # حساب التغيير (نسبة مئوية)
        def calculate_percentage_change(current, previous):
            if not previous or previous == 0:
                return 100 if current else 0
            return ((current - previous) / previous) * 100

        today_revenue = today_stats['revenue'] or 0
        yesterday_revenue = yesterday_stats['revenue'] or 0
        this_month_revenue = this_month_stats['revenue'] or 0
        last_month_revenue = last_month_stats['revenue'] or 0

        revenue_change_daily = calculate_percentage_change(today_revenue, yesterday_revenue)
        revenue_change_monthly = calculate_percentage_change(this_month_revenue, last_month_revenue)

        # مبيعات آخر 7 أيام
        last_7_days = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_stats = Order.objects.filter(created_at__date=day).aggregate(
                count=Count('id'),
                revenue=Sum('grand_total')
            )

            last_7_days.append({
                'date': day.strftime('%Y-%m-%d'),
                'day': day.strftime('%a'),
                'count': day_stats['count'] or 0,
                'revenue': float(day_stats['revenue'] or 0)
            })

        # أحدث الطلبات
        latest_orders = Order.objects.all().order_by('-created_at')[:10]

        # أعلى المنتجات مبيعًا (هذا الشهر)
        top_products = OrderItem.objects.filter(
            order__created_at__date__gte=this_month_start,
            order__created_at__date__lte=today
        ).values('product_id', 'product_name').annotate(
            quantity=Sum('quantity'),
            revenue=Sum('total_price')
        ).order_by('-quantity')[:5]

        context = {
            'today_stats': today_stats,
            'yesterday_stats': yesterday_stats,
            'this_month_stats': this_month_stats,
            'last_month_stats': last_month_stats,
            'revenue_change_daily': revenue_change_daily,
            'revenue_change_monthly': revenue_change_monthly,
            'last_7_days': last_7_days,
            'latest_orders': latest_orders,
            'top_products': top_products,
        }

        return render(request, 'dashboard/orders/order_dashboard.html', context)


@method_decorator(permission_required('orders.view_order'), name='dispatch')
class DeliveryOrdersReportView(DashboardAccessMixin, View):
    """عرض تقرير الطلبات المؤكدة المنتظرة التوصيل"""

    def get(self, request):
        # جلب الطلبات المؤكدة التي لم يتم إغلاقها بعد
        confirmed_orders = Order.objects.filter(
            status='confirmed',  # فقط الطلبات المؤكدة
            payment_status='paid'  # والمدفوعة
        ).order_by('-created_at')

        # البحث والتصفية
        query = request.GET.get('q', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # تطبيق البحث
        if query:
            confirmed_orders = confirmed_orders.filter(
                Q(order_number__icontains=query) |
                Q(full_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )

        # تطبيق التصفية حسب التاريخ
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                confirmed_orders = confirmed_orders.filter(created_at__date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                confirmed_orders = confirmed_orders.filter(created_at__date__lte=date_to)
            except ValueError:
                pass

        # التصفح الجزئي
        paginator = Paginator(confirmed_orders, 20)  # 20 طلب في كل صفحة
        page = request.GET.get('page', 1)
        orders_page = paginator.get_page(page)

        # إحصائيات
        stats = {
            'total_orders': confirmed_orders.count(),
            'total_value': confirmed_orders.aggregate(total=Sum('grand_total'))['total'] or 0,
        }

        context = {
            'orders': orders_page,
            'query': query,
            'date_from': date_from,
            'date_to': date_to,
            'stats': stats,
        }

        return render(request, 'dashboard/orders/delivery_orders_report.html', context)