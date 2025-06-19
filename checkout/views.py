# checkout/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse

from .models import CheckoutSession, PaymentMethod, ShippingMethod
from cart.models import Cart
from orders.models import Order
from payment.models import Payment, Transaction
import uuid
import os
from decimal import Decimal

class CheckoutView(LoginRequiredMixin, View):
    """
    صفحة بيانات العميل - الخطوة الأولى في عملية الدفع
    تتطلب تسجيل الدخول
    """
    template_name = 'checkout/checkout.html'
    login_url = '/accounts/login/'  # URL صفحة تسجيل الدخول (قم بتعديله حسب مشروعك)
    redirect_field_name = 'next'

    def get(self, request):
        # التحقق من وجود منتجات في السلة
        cart = request.session.get('cart', {})
        if not cart:
            messages.warning(request, _('لا يوجد منتجات في سلة التسوق'))
            return redirect('cart:cart_detail')

        # الحصول على طرق الشحن
        shipping_methods = ShippingMethod.objects.filter(is_active=True).order_by('sort_order')

        # جلب معلومات المستخدم من النموذج مباشرة
        user = request.user
        user_data = {
            'full_name': user.get_full_name(),
            'email': user.email,
            'phone': user.phone_number,
            'address': user.address,
            'city': user.city,
            'state': '',  # لا يوجد حقل state في نموذج User، يمكن تركه فارغًا
            'country': user.country,
            'postal_code': user.postal_code,
        }

        # محاولة الحصول على عنوان الشحن الافتراضي إن وجد
        try:
            default_shipping_address = user.addresses.filter(is_shipping_default=True).first()
            if default_shipping_address:
                user_data.update({
                    'full_name': default_shipping_address.full_name,
                    'address': default_shipping_address.address_line_1,
                    'address_line_2': default_shipping_address.address_line_2,
                    'city': default_shipping_address.city,
                    'state': default_shipping_address.state,
                    'country': default_shipping_address.country,
                    'postal_code': default_shipping_address.postal_code,
                    'phone': default_shipping_address.phone_number or user.phone_number,
                })
        except:
            # في حالة عدم وجود عناوين للمستخدم، نستخدم المعلومات الأساسية المذكورة سابقًا
            pass

        return render(request, self.template_name, {
            'shipping_methods': shipping_methods,
            'user_data': user_data,
        })

    def post(self, request):
        # الحصول على بيانات النموذج
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country', 'الأردن')
        postal_code = request.POST.get('postal_code', '')
        notes = request.POST.get('notes', '')
        shipping_method_id = request.POST.get('shipping_method')

        # التحقق من البيانات المطلوبة
        if not all([full_name, email, phone, address, city, state]):
            messages.error(request, _('الرجاء إدخال جميع البيانات المطلوبة'))
            return redirect('checkout:checkout')

        # حفظ البيانات في الجلسة
        request.session['checkout_data'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'address': address,
            'city': city,
            'state': state,
            'country': country,
            'postal_code': postal_code,
            'notes': notes,
            'shipping_method_id': shipping_method_id,
        }

        # الانتقال إلى صفحة اختيار طريقة الدفع
        return redirect('checkout:payment_method')


class PaymentMethodView(LoginRequiredMixin, View):
    """
    صفحة اختيار طريقة الدفع
    تتطلب تسجيل الدخول
    """
    template_name = 'checkout/payment_method.html'
    login_url = '/accounts/login/'  # URL صفحة تسجيل الدخول
    redirect_field_name = 'next'

    def get(self, request):
        # التحقق من وجود بيانات الشحن
        if 'checkout_data' not in request.session:
            messages.error(request, _('الرجاء إدخال بيانات الشحن أولاً'))
            return redirect('checkout:checkout')

        # الحصول على طرق الدفع
        payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('sort_order')

        return render(request, self.template_name, {
            'payment_methods': payment_methods,
        })

    def post(self, request):
        # الحصول على طريقة الدفع المختارة
        payment_method_id = request.POST.get('payment_method')

        if not payment_method_id:
            messages.error(request, _('الرجاء اختيار طريقة دفع'))
            return redirect('checkout:payment_method')

        # حفظ طريقة الدفع في الجلسة
        checkout_data = request.session.get('checkout_data', {})
        checkout_data['payment_method_id'] = payment_method_id
        request.session['checkout_data'] = checkout_data

        # الانتقال إلى صفحة تأكيد الدفع
        return redirect('checkout:payment_confirmation')


class PaymentConfirmationView(LoginRequiredMixin, View):
    """
    صفحة تأكيد الدفع وإرفاق الإيصال
    تتطلب تسجيل الدخول
    """
    template_name = 'checkout/payment_confirmation.html'
    login_url = '/accounts/login/'  # URL صفحة تسجيل الدخول
    redirect_field_name = 'next'

    def get(self, request):
        # التحقق من وجود بيانات الشحن وطريقة الدفع
        checkout_data = request.session.get('checkout_data', {})
        if not checkout_data or 'payment_method_id' not in checkout_data:
            messages.error(request, _('الرجاء إكمال بيانات الطلب أولاً'))
            return redirect('checkout:checkout')

        # الحصول على طريقة الدفع
        try:
            payment_method = PaymentMethod.objects.get(id=checkout_data.get('payment_method_id'))
        except PaymentMethod.DoesNotExist:
            messages.error(request, _('طريقة الدفع غير متوفرة'))
            return redirect('checkout:payment_method')

        # الحصول على بيانات السلة
        cart_data = request.session.get('cart', {})
        cart_items = []
        total = Decimal('0.00')

        for item_id, item_info in cart_data.items():
            product_id = item_info.get('product_id')
            quantity = item_info.get('quantity', 1)
            price = Decimal(str(item_info.get('price', '0.00')))
            item_total = price * quantity
            total += item_total

            cart_items.append({
                'product_id': product_id,
                'name': item_info.get('name', ''),
                'quantity': quantity,
                'price': price,
                'total': item_total,
            })

        # إضافة تكاليف الشحن والضريبة
        shipping_cost = Decimal('5.00')  # تكلفة افتراضية، يمكن جلبها من طريقة الشحن
        tax_amount = total * Decimal('0.16')  # 16% ضريبة القيمة المضافة
        grand_total = total + shipping_cost + tax_amount

        context = {
            'payment_method': payment_method,
            'cart_items': cart_items,
            'total': total,
            'shipping_cost': shipping_cost,
            'tax_amount': tax_amount,
            'grand_total': grand_total,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        # التحقق من وجود بيانات الشحن وطريقة الدفع
        checkout_data = request.session.get('checkout_data', {})
        if not checkout_data or 'payment_method_id' not in checkout_data:
            messages.error(request, _('الرجاء إكمال بيانات الطلب أولاً'))
            return redirect('checkout:checkout')

        # الحصول على طريقة الدفع
        try:
            payment_method = PaymentMethod.objects.get(id=checkout_data.get('payment_method_id'))
        except PaymentMethod.DoesNotExist:
            messages.error(request, _('طريقة الدفع غير متوفرة'))
            return redirect('checkout:payment_method')

        # التعامل مع ملف الإيصال المرفق
        receipt_file = request.FILES.get('receipt')
        receipt_path = None

        if receipt_file:
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'receipts'))
            filename = fs.save(f"{uuid.uuid4()}_{receipt_file.name}", receipt_file)
            receipt_path = os.path.join('receipts', filename)
        else:
            # إذا كانت طريقة الدفع تتطلب إيصالًا
            if payment_method.payment_type in ['bank_transfer', 'other']:
                messages.error(request, _('الرجاء إرفاق إيصال الدفع'))
                return redirect('checkout:payment_confirmation')

        # إنشاء الطلب
        cart_data = request.session.get('cart', {})
        user = request.user if request.user.is_authenticated else None

        # الحصول على أو إنشاء سلة في قاعدة البيانات
        cart = None
        session_key = request.session.session_key

        if user:
            cart, created = Cart.objects.get_or_create(
                user=user,
                is_active=True,
                defaults={'session_key': session_key}
            )
        elif session_key:
            cart, created = Cart.objects.get_or_create(
                session_key=session_key,
                is_active=True,
                user=None
            )

        # إنشاء الطلب
        order = Order.objects.create(
            user=user,
            cart=cart,
            full_name=checkout_data.get('full_name', ''),
            email=checkout_data.get('email', ''),
            phone=checkout_data.get('phone', ''),
            shipping_address=checkout_data.get('address', ''),
            shipping_city=checkout_data.get('city', ''),
            shipping_state=checkout_data.get('state', ''),
            shipping_country=checkout_data.get('country', 'الأردن'),
            shipping_postal_code=checkout_data.get('postal_code', ''),
            total_price=Decimal('0.00'),  # سيتم تحديثه لاحقًا
            shipping_cost=Decimal('5.00'),  # تكلفة افتراضية
            tax_amount=Decimal('0.00'),  # سيتم حسابه
            grand_total=Decimal('0.00'),  # سيتم حسابه
            payment_method=payment_method.name,
            status='pending',
            payment_status='pending',
            notes=checkout_data.get('notes', '')
        )

        # حساب المبالغ وإضافة عناصر الطلب
        total = Decimal('0.00')

        for item_id, item_info in cart_data.items():
            from products.models import Product, ProductVariant

            product_id = item_info.get('product_id')
            variant_id = item_info.get('variant_id')
            quantity = item_info.get('quantity', 1)

            try:
                product = Product.objects.get(id=product_id)
                variant = None

                if variant_id:
                    try:
                        variant = ProductVariant.objects.get(id=variant_id)
                    except ProductVariant.DoesNotExist:
                        pass

                unit_price = variant.current_price if variant else product.current_price
                item_total = unit_price * quantity
                total += item_total

                # إضافة عنصر الطلب
                from orders.models import OrderItem

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=variant,
                    product_name=product.name,
                    variant_name=variant.name if variant else '',
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=item_total
                )

            except Product.DoesNotExist:
                continue

        # تحديث مبالغ الطلب
        shipping_cost = Decimal('5.00')  # تكلفة افتراضية
        tax_amount = total * Decimal('0.16')  # 16% ضريبة القيمة المضافة
        grand_total = total + shipping_cost + tax_amount

        order.total_price = total
        order.tax_amount = tax_amount
        order.grand_total = grand_total
        order.save()

        # إنشاء معاملة دفع
        transaction = Transaction.objects.create(
            user=user,
            order=order,
            amount=grand_total,
            currency='JOD',
            transaction_type='payment',
            status='pending',
            payment_gateway=payment_method.code,
            payment_method=payment_method.name,
            description=f"دفع الطلب رقم {order.order_number}",
            notes=f"تم الدفع عبر {payment_method.name}"
        )

        # إنشاء سجل دفع
        payment = Payment.objects.create(
            user=user,
            order=order,
            transaction=transaction,
            amount=grand_total,
            currency='JOD',
            payment_method=payment_method.payment_type,
            status='pending',
            payment_gateway=payment_method.code,
            description=f"دفع الطلب رقم {order.order_number}",
            notes=f"تم إرفاق إيصال الدفع: {receipt_path}" if receipt_path else "بانتظار التأكيد"
        )

        if receipt_path:
            # حفظ مسار الإيصال في حقل metadata في المعاملة
            metadata = transaction.metadata or {}
            metadata['receipt_path'] = receipt_path
            transaction.metadata = metadata
            transaction.save()

        # تحديث حالة السلة
        if cart:
            cart.converted_to_order = True
            cart.is_active = False
            cart.save()

        # مسح بيانات السلة والدفع من الجلسة
        if 'cart' in request.session:
            del request.session['cart']
        if 'checkout_data' in request.session:
            del request.session['checkout_data']

        request.session.modified = True

        # توجيه المستخدم إلى صفحة نجاح الطلب
        return redirect('checkout:order_success', order_id=order.id)


class OrderSuccessView(LoginRequiredMixin, TemplateView):
    """
    صفحة نجاح الطلب
    تتطلب تسجيل الدخول
    """
    template_name = 'checkout/order_success.html'
    login_url = '/accounts/login/'  # URL صفحة تسجيل الدخول
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order_id = self.kwargs.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            # التحقق من أن الطلب ينتمي للمستخدم الحالي
            if order.user != self.request.user:
                context['order'] = None
                context['error'] = _('لا يمكنك الوصول إلى هذا الطلب')
            else:
                context['order'] = order
        except Order.DoesNotExist:
            context['order'] = None
            context['error'] = _('الطلب غير موجود')
            
        return context