# views/checkout.py
# عروض إدارة عمليات الدفع

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db.models import Q, Count, Sum, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta

from checkout.models import CheckoutSession, ShippingMethod, PaymentMethod, Coupon, CouponUsage
from orders.models import Order
from .dashboard import DashboardAccessMixin


# ========================= جلسات الدفع =========================

class CheckoutSessionListView(DashboardAccessMixin, View):
    """عرض قائمة جلسات الدفع"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        status_filter = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # قائمة جلسات الدفع
        sessions = CheckoutSession.objects.select_related('user', 'order').order_by('-created_at')

        # تطبيق البحث
        if query:
            sessions = sessions.filter(
                Q(email__icontains=query) |
                Q(phone_number__icontains=query) |
                Q(user__username__icontains=query) |
                Q(order__order_number__icontains=query)
            )

        # تطبيق التصفية حسب الحالة
        if status_filter == 'completed':
            sessions = sessions.filter(is_completed=True)
        elif status_filter == 'incomplete':
            sessions = sessions.filter(is_completed=False)
        elif status_filter == 'expired':
            sessions = sessions.filter(expires_at__lt=timezone.now())

        # تطبيق التصفية حسب التاريخ
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                sessions = sessions.filter(created_at__date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                sessions = sessions.filter(created_at__date__lte=date_to)
            except ValueError:
                pass

        # التصفح الجزئي
        paginator = Paginator(sessions, 20)  # 20 جلسة في كل صفحة
        page = request.GET.get('page', 1)
        sessions_page = paginator.get_page(page)

        # الإحصائيات
        stats = {
            'total': CheckoutSession.objects.count(),
            'completed': CheckoutSession.objects.filter(is_completed=True).count(),
            'incomplete': CheckoutSession.objects.filter(is_completed=False).count(),
            'expired': CheckoutSession.objects.filter(expires_at__lt=timezone.now(), is_completed=False).count(),
            'conversion_rate': self.get_conversion_rate(),
        }

        context = {
            'sessions': sessions_page,
            'query': query,
            'status_filter': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'stats': stats,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/checkout/sessions_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': sessions_page.has_next(),
                'has_prev': sessions_page.has_previous(),
                'page': sessions_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/checkout/session_list.html', context)

    def get_conversion_rate(self):
        """حساب معدل التحويل (نسبة الجلسات المكتملة)"""
        total = CheckoutSession.objects.count()
        completed = CheckoutSession.objects.filter(is_completed=True).count()

        if total == 0:
            return 0

        return round((completed / total) * 100, 2)


class CheckoutSessionDetailView(DashboardAccessMixin, View):
    """عرض تفاصيل جلسة الدفع"""

    def get(self, request, session_id):
        session = get_object_or_404(CheckoutSession, id=session_id)

        # معلومات العميل
        customer_info = {
            'email': session.email,
            'phone': session.phone_number,
            'user': session.user,
        }

        # معلومات المبالغ
        amount_info = {
            'subtotal': session.subtotal,
            'shipping_cost': session.shipping_cost,
            'tax_amount': session.tax_amount,
            'discount_amount': session.discount_amount,
            'total_amount': session.total_amount,
        }

        # معلومات سلة التسوق
        cart_items = []
        if session.cart and hasattr(session.cart, 'items'):
            cart_items = session.cart.items.all().select_related('product', 'variant')

        # المعاملات المالية
        transactions = []
        if hasattr(session, 'payment_transactions'):
            transactions = session.payment_transactions.all().order_by('-created_at')

        # الطلب المرتبط
        order = session.order

        context = {
            'session': session,
            'customer_info': customer_info,
            'amount_info': amount_info,
            'cart_items': cart_items,
            'transactions': transactions,
            'order': order,
            'checkout_steps': dict(CheckoutSession.CHECKOUT_STEPS),
        }

        return render(request, 'dashboard/checkout/session_detail.html', context)


# ========================= طرق الشحن =========================

class ShippingMethodListView(DashboardAccessMixin, View):
    """عرض قائمة طرق الشحن"""

    def get(self, request):
        # قائمة طرق الشحن
        shipping_methods = ShippingMethod.objects.all().order_by('sort_order')

        context = {
            'shipping_methods': shipping_methods,
        }

        return render(request, 'dashboard/checkout/shipping_method_list.html', context)


class ShippingMethodFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث طريقة الشحن"""

    def get(self, request, method_id=None):
        if method_id:
            shipping_method = get_object_or_404(ShippingMethod, id=method_id)
            form_title = 'تحديث طريقة الشحن'
        else:
            shipping_method = None
            form_title = 'إنشاء طريقة شحن جديدة'

        context = {
            'shipping_method': shipping_method,
            'form_title': form_title,
        }

        return render(request, 'dashboard/checkout/shipping_method_form.html', context)

    def post(self, request, method_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description', '')
        base_cost = request.POST.get('base_cost', 0)
        free_shipping_threshold = request.POST.get('free_shipping_threshold', 0)
        estimated_days_min = request.POST.get('estimated_days_min', 1)
        estimated_days_max = request.POST.get('estimated_days_max', 3)
        is_active = request.POST.get('is_active') == 'on'
        is_default = request.POST.get('is_default') == 'on'
        sort_order = request.POST.get('sort_order', 0)
        restrictions = request.POST.get('restrictions', '')

        # التحقق من البيانات المطلوبة
        if not name or not code:
            messages.error(request, 'اسم ورمز طريقة الشحن مطلوبان')
            return redirect(request.path)

        # التحقق من عدم تكرار الرمز
        if method_id:
            existing = ShippingMethod.objects.filter(code=code).exclude(id=method_id).exists()
        else:
            existing = ShippingMethod.objects.filter(code=code).exists()

        if existing:
            messages.error(request, 'رمز طريقة الشحن مستخدم بالفعل')
            return redirect(request.path)

        try:
            if method_id:
                # تحديث طريقة شحن موجودة
                shipping_method = get_object_or_404(ShippingMethod, id=method_id)

                # تحديث البيانات
                shipping_method.name = name
                shipping_method.code = code
                shipping_method.description = description
                shipping_method.base_cost = base_cost
                shipping_method.free_shipping_threshold = free_shipping_threshold
                shipping_method.estimated_days_min = estimated_days_min
                shipping_method.estimated_days_max = estimated_days_max
                shipping_method.is_active = is_active
                shipping_method.is_default = is_default
                shipping_method.sort_order = sort_order
                shipping_method.restrictions = restrictions

                shipping_method.save()
                messages.success(request, 'تم تحديث طريقة الشحن بنجاح')
            else:
                # إنشاء طريقة شحن جديدة
                shipping_method = ShippingMethod.objects.create(
                    name=name,
                    code=code,
                    description=description,
                    base_cost=base_cost,
                    free_shipping_threshold=free_shipping_threshold,
                    estimated_days_min=estimated_days_min,
                    estimated_days_max=estimated_days_max,
                    is_active=is_active,
                    is_default=is_default,
                    sort_order=sort_order,
                    restrictions=restrictions,
                )
                messages.success(request, 'تم إنشاء طريقة الشحن بنجاح')

            # معالجة الصورة إذا تم تحميلها
            icon = request.FILES.get('icon')
            if icon:
                shipping_method.icon = icon
                shipping_method.save()

            return redirect('dashboard:dashboard_shipping_methods')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ طريقة الشحن: {str(e)}')
            return redirect(request.path)


class ShippingMethodDeleteView(DashboardAccessMixin, View):
    """حذف طريقة الشحن"""

    def post(self, request, method_id):
        shipping_method = get_object_or_404(ShippingMethod, id=method_id)

        # التحقق من وجود جلسات دفع تستخدم هذه الطريقة
        checkout_count = CheckoutSession.objects.filter(shipping_method=shipping_method).count()
        if checkout_count > 0:
            messages.error(request, f'لا يمكن حذف طريقة الشحن لأنها مستخدمة في {checkout_count} جلسة دفع')
            return redirect('dashboard:dashboard_shipping_methods')

        try:
            method_name = shipping_method.name
            shipping_method.delete()
            messages.success(request, f'تم حذف طريقة الشحن "{method_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف طريقة الشحن: {str(e)}')

        return redirect('dashboard:dashboard_shipping_methods')


# ========================= طرق الدفع =========================

class PaymentMethodListView(DashboardAccessMixin, View):
    """عرض قائمة طرق الدفع"""

    def get(self, request):
        # قائمة طرق الدفع
        payment_methods = PaymentMethod.objects.all().order_by('sort_order')

        context = {
            'payment_methods': payment_methods,
        }

        return render(request, 'dashboard/checkout/payment_method_list.html', context)


class PaymentMethodFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث طريقة الدفع"""

    def get(self, request, method_id=None):
        if method_id:
            payment_method = get_object_or_404(PaymentMethod, id=method_id)
            form_title = 'تحديث طريقة الدفع'
        else:
            payment_method = None
            form_title = 'إنشاء طريقة دفع جديدة'

        context = {
            'payment_method': payment_method,
            'form_title': form_title,
            'payment_types': PaymentMethod.PAYMENT_TYPE_CHOICES,
        }

        return render(request, 'dashboard/checkout/payment_method_form.html', context)

    def post(self, request, method_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        code = request.POST.get('code')
        payment_type = request.POST.get('payment_type')
        description = request.POST.get('description', '')
        instructions = request.POST.get('instructions', '')
        fee_fixed = request.POST.get('fee_fixed', 0)
        fee_percentage = request.POST.get('fee_percentage', 0)
        is_active = request.POST.get('is_active') == 'on'
        is_default = request.POST.get('is_default') == 'on'
        min_amount = request.POST.get('min_amount', 0)
        max_amount = request.POST.get('max_amount', 0)
        sort_order = request.POST.get('sort_order', 0)

        # بيانات API (إذا كانت متوفرة)
        api_data = {}
        api_key = request.POST.get('api_key', '')
        api_secret = request.POST.get('api_secret', '')
        api_endpoint = request.POST.get('api_endpoint', '')
        api_mode = request.POST.get('api_mode', 'sandbox')

        if api_key:
            api_data['api_key'] = api_key
        if api_secret:
            api_data['api_secret'] = api_secret
        if api_endpoint:
            api_data['api_endpoint'] = api_endpoint
        if api_mode:
            api_data['mode'] = api_mode

        # التحقق من البيانات المطلوبة
        if not name or not code or not payment_type:
            messages.error(request, 'اسم ورمز ونوع طريقة الدفع مطلوبة')
            return redirect(request.path)

        # التحقق من عدم تكرار الرمز
        if method_id:
            existing = PaymentMethod.objects.filter(code=code).exclude(id=method_id).exists()
        else:
            existing = PaymentMethod.objects.filter(code=code).exists()

        if existing:
            messages.error(request, 'رمز طريقة الدفع مستخدم بالفعل')
            return redirect(request.path)

        try:
            if method_id:
                # تحديث طريقة دفع موجودة
                payment_method = get_object_or_404(PaymentMethod, id=method_id)

                # تحديث البيانات
                payment_method.name = name
                payment_method.code = code
                payment_method.payment_type = payment_type
                payment_method.description = description
                payment_method.instructions = instructions
                payment_method.fee_fixed = fee_fixed
                payment_method.fee_percentage = fee_percentage
                payment_method.is_active = is_active
                payment_method.is_default = is_default
                payment_method.min_amount = min_amount
                payment_method.max_amount = max_amount
                payment_method.sort_order = sort_order

                # تحديث بيانات API
                if api_data:
                    current_api_credentials = payment_method.api_credentials
                    current_api_credentials.update(api_data)
                    payment_method.api_credentials = current_api_credentials

                payment_method.save()
                messages.success(request, 'تم تحديث طريقة الدفع بنجاح')
            else:
                # إنشاء طريقة دفع جديدة
                payment_method = PaymentMethod.objects.create(
                    name=name,
                    code=code,
                    payment_type=payment_type,
                    description=description,
                    instructions=instructions,
                    fee_fixed=fee_fixed,
                    fee_percentage=fee_percentage,
                    is_active=is_active,
                    is_default=is_default,
                    min_amount=min_amount,
                    max_amount=max_amount,
                    sort_order=sort_order,
                    api_credentials=api_data,
                )
                messages.success(request, 'تم إنشاء طريقة الدفع بنجاح')

            # معالجة الصورة إذا تم تحميلها
            icon = request.FILES.get('icon')
            if icon:
                payment_method.icon = icon
                payment_method.save()

            return redirect('dashboard:dashboard_payment_methods')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ طريقة الدفع: {str(e)}')
            return redirect(request.path)


class PaymentMethodDeleteView(DashboardAccessMixin, View):
    """حذف طريقة الدفع"""

    def post(self, request, method_id):
        payment_method = get_object_or_404(PaymentMethod, id=method_id)

        # التحقق من وجود جلسات دفع تستخدم هذه الطريقة
        checkout_count = CheckoutSession.objects.filter(payment_method=payment_method).count()
        if checkout_count > 0:
            messages.error(request, f'لا يمكن حذف طريقة الدفع لأنها مستخدمة في {checkout_count} جلسة دفع')
            return redirect('dashboard:dashboard_payment_methods')

        try:
            method_name = payment_method.name
            payment_method.delete()
            messages.success(request, f'تم حذف طريقة الدفع "{method_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف طريقة الدفع: {str(e)}')

        return redirect('dashboard:dashboard_payment_methods')


# ========================= كوبونات الخصم =========================

class CouponListView(DashboardAccessMixin, View):
    """عرض قائمة كوبونات الخصم"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        status_filter = request.GET.get('status', '')
        type_filter = request.GET.get('type', '')

        # قائمة الكوبونات
        coupons = Coupon.objects.all().order_by('-created_at')

        # تطبيق البحث
        if query:
            coupons = coupons.filter(
                Q(code__icontains=query) |
                Q(description__icontains=query)
            )

        # تطبيق التصفية حسب الحالة
        if status_filter == 'active':
            coupons = coupons.filter(is_active=True)
        elif status_filter == 'inactive':
            coupons = coupons.filter(is_active=False)
        elif status_filter == 'expired':
            coupons = coupons.filter(end_date__lt=timezone.now())

        # تطبيق التصفية حسب النوع
        if type_filter:
            coupons = coupons.filter(discount_type=type_filter)

        # التصفح الجزئي
        paginator = Paginator(coupons, 20)  # 20 كوبون في كل صفحة
        page = request.GET.get('page', 1)
        coupons_page = paginator.get_page(page)

        # الإحصائيات
        stats = {
            'total': Coupon.objects.count(),
            'active': Coupon.objects.filter(is_active=True).count(),
            'expired': Coupon.objects.filter(end_date__lt=timezone.now()).count(),
            'total_usage': CouponUsage.objects.count(),
        }

        context = {
            'coupons': coupons_page,
            'query': query,
            'status_filter': status_filter,
            'type_filter': type_filter,
            'stats': stats,
            'discount_types': Coupon.DISCOUNT_TYPE_CHOICES,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/checkout/coupons_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': coupons_page.has_next(),
                'has_prev': coupons_page.has_previous(),
                'page': coupons_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/checkout/coupon_list.html', context)


class CouponFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث كوبون الخصم"""

    def get(self, request, coupon_id=None):
        if coupon_id:
            coupon = get_object_or_404(Coupon, id=coupon_id)
            form_title = 'تحديث كوبون الخصم'
        else:
            coupon = None
            form_title = 'إنشاء كوبون خصم جديد'

        context = {
            'coupon': coupon,
            'form_title': form_title,
            'discount_types': Coupon.DISCOUNT_TYPE_CHOICES,
        }

        return render(request, 'dashboard/checkout/coupon_form.html', context)

    def post(self, request, coupon_id=None):
        # جمع البيانات من النموذج
        code = request.POST.get('code')
        description = request.POST.get('description', '')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        min_order_value = request.POST.get('min_order_value', 0)
        max_discount_amount = request.POST.get('max_discount_amount', 0)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date', '')
        max_uses = request.POST.get('max_uses', 0)
        max_uses_per_user = request.POST.get('max_uses_per_user', 0)
        is_active = request.POST.get('is_active') == 'on'

        # التحقق من البيانات المطلوبة
        if not code or not discount_type or not discount_value or not start_date:
            messages.error(request, 'الرجاء ملء جميع الحقول المطلوبة')
            return redirect(request.path)

        # التحقق من عدم تكرار الكود
        if coupon_id:
            existing = Coupon.objects.filter(code=code).exclude(id=coupon_id).exists()
        else:
            existing = Coupon.objects.filter(code=code).exists()

        if existing:
            messages.error(request, 'كود الكوبون مستخدم بالفعل')
            return redirect(request.path)

        # تحويل التواريخ من نص إلى كائنات datetime
        import datetime
        try:
            start_date = timezone.make_aware(datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M'))
            if end_date:
                end_date = timezone.make_aware(datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M'))
            else:
                end_date = None
        except ValueError:
            messages.error(request, 'صيغة التاريخ غير صحيحة')
            return redirect(request.path)

        try:
            if coupon_id:
                # تحديث كوبون موجود
                coupon = get_object_or_404(Coupon, id=coupon_id)

                # تحديث البيانات
                coupon.code = code
                coupon.description = description
                coupon.discount_type = discount_type
                coupon.discount_value = discount_value
                coupon.min_order_value = min_order_value
                coupon.max_discount_amount = max_discount_amount
                coupon.start_date = start_date
                coupon.end_date = end_date
                coupon.max_uses = max_uses
                coupon.max_uses_per_user = max_uses_per_user
                coupon.is_active = is_active

                coupon.save()
                messages.success(request, 'تم تحديث كوبون الخصم بنجاح')
            else:
                # إنشاء كوبون جديد
                coupon = Coupon.objects.create(
                    code=code,
                    description=description,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    min_order_value=min_order_value,
                    max_discount_amount=max_discount_amount,
                    start_date=start_date,
                    end_date=end_date,
                    max_uses=max_uses,
                    max_uses_per_user=max_uses_per_user,
                    is_active=is_active,
                )
                messages.success(request, 'تم إنشاء كوبون الخصم بنجاح')

            return redirect('dashboard:dashboard_coupons')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ كوبون الخصم: {str(e)}')
            return redirect(request.path)


class CouponDeleteView(DashboardAccessMixin, View):
    """حذف كوبون الخصم"""

    def post(self, request, coupon_id):
        coupon = get_object_or_404(Coupon, id=coupon_id)

        # التحقق من استخدام الكوبون
        usage_count = CouponUsage.objects.filter(coupon=coupon).count()
        if usage_count > 0:
            messages.warning(request, f'تم حذف كوبون الخصم مع العلم أنه تم استخدامه {usage_count} مرة')

        try:
            coupon_code = coupon.code
            coupon.delete()
            messages.success(request, f'تم حذف كوبون الخصم "{coupon_code}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف كوبون الخصم: {str(e)}')

        return redirect('dashboard:dashboard_coupons')


# ========================= تقارير عملية الدفع =========================

class CheckoutReportsView(DashboardAccessMixin, View):
    """عرض تقارير وإحصائيات عملية الدفع"""

    def get(self, request):
        report_type = request.GET.get('report_type', 'checkout_funnel')
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

        # تقرير مسار التحويل (funnel)
        if report_type == 'checkout_funnel':
            # جلسات الدفع المنشأة في الفترة المحددة
            total_sessions = CheckoutSession.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).count()

            # تحليل الخطوات
            steps_data = {}
            for step_code, step_name in CheckoutSession.CHECKOUT_STEPS:
                steps_data[step_code] = {
                    'name': step_name,
                    'count': CheckoutSession.objects.filter(
                        created_at__date__gte=date_from,
                        created_at__date__lte=date_to,
                        current_step=step_code
                    ).count(),
                }

            # جلسات مكتملة
            completed_sessions = CheckoutSession.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to,
                is_completed=True
            ).count()

            # طلبات تم إنشاؤها
            created_orders = Order.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).count()

            # حساب معدلات التحويل
            conversion_rate = (created_orders / total_sessions * 100) if total_sessions > 0 else 0

            # استخراج البيانات للرسم البياني
            funnel_data = []
            for step_code, step_info in steps_data.items():
                funnel_data.append({
                    'name': step_info['name'],
                    'count': step_info['count'],
                    'percentage': (step_info['count'] / total_sessions * 100) if total_sessions > 0 else 0
                })

            # مقارنة مع الطلبات المكتملة
            funnel_data.append({
                'name': 'الطلبات المكتملة',
                'count': created_orders,
                'percentage': conversion_rate
            })

            report_data = {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'created_orders': created_orders,
                'conversion_rate': round(conversion_rate, 2),
                'steps_data': steps_data,
                'funnel_data': funnel_data,
            }

        # تقرير طرق الدفع
        elif report_type == 'payment_methods':
            # إحصائيات طرق الدفع
            payment_methods_data = []

            # جلب جميع طرق الدفع
            payment_methods = PaymentMethod.objects.filter(is_active=True)

            for method in payment_methods:
                # عدد جلسات الدفع التي استخدمت هذه الطريقة
                sessions_count = CheckoutSession.objects.filter(
                    created_at__date__gte=date_from,
                    created_at__date__lte=date_to,
                    payment_method=method
                ).count()

                # عدد الطلبات المكتملة بهذه الطريقة
                orders_count = Order.objects.filter(
                    created_at__date__gte=date_from,
                    created_at__date__lte=date_to,
                    payment_method=method.name
                ).count()

                # إجمالي المبلغ المدفوع بهذه الطريقة
                total_amount = Order.objects.filter(
                    created_at__date__gte=date_from,
                    created_at__date__lte=date_to,
                    payment_method=method.name
                ).aggregate(total=Sum('grand_total'))['total'] or 0

                payment_methods_data.append({
                    'method': method,
                    'sessions_count': sessions_count,
                    'orders_count': orders_count,
                    'total_amount': total_amount,
                })

            report_data = {
                'payment_methods_data': payment_methods_data,
            }

        # تقرير الكوبونات
        elif report_type == 'coupons':
            # إحصائيات الكوبونات
            coupons_data = []

            # جلب الكوبونات المستخدمة
            coupon_usages = CouponUsage.objects.filter(
                used_at__date__gte=date_from,
                used_at__date__lte=date_to
            ).values('coupon').annotate(
                usage_count=Count('id'),
                total_discount=Sum('order__discount_amount')
            ).order_by('-usage_count')

            for usage in coupon_usages:
                try:
                    coupon = Coupon.objects.get(id=usage['coupon'])
                    coupons_data.append({
                        'coupon': coupon,
                        'usage_count': usage['usage_count'],
                        'total_discount': usage['total_discount'] or 0,
                    })
                except Coupon.DoesNotExist:
                    pass

            # إجمالي استخدام الكوبونات
            total_usage = CouponUsage.objects.filter(
                used_at__date__gte=date_from,
                used_at__date__lte=date_to
            ).count()

            # إجمالي الخصم
            total_discount = CouponUsage.objects.filter(
                used_at__date__gte=date_from,
                used_at__date__lte=date_to
            ).aggregate(total=Sum('order__discount_amount'))['total'] or 0

            report_data = {
                'coupons_data': coupons_data,
                'total_usage': total_usage,
                'total_discount': total_discount,
            }

        else:
            report_data = {}

        context = {
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
            'report_data': report_data
        }

        return render(request, 'dashboard/checkout/checkout_reports.html', context)