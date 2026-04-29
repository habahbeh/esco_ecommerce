# cart/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.db import models
from decimal import Decimal

from products.models import Product, ProductVariant
from .signals import emit_cart_item_added, emit_cart_item_removed


class CartMixin:
    """
    Mixin to handle cart operations
    """
    def get_cart(self, request):
        """Get or create cart in session"""
        if 'cart' not in request.session:
            request.session['cart'] = {}
        return request.session['cart']
    
    def save_cart(self, request, cart):
        """Save cart to session"""
        request.session['cart'] = cart
        request.session.modified = True
    
    def get_cart_items_count(self, request):
        """Get total items count in cart"""
        cart = self.get_cart(request)
        return sum(item.get('quantity', 0) for item in cart.values())
    
    def get_cart_total(self, request):
        """Calculate cart total"""
        cart = self.get_cart(request)
        total = Decimal('0.00')
        
        for item_id, item_data in cart.items():
            try:
                product = Product.objects.get(id=item_data['product_id'])
                quantity = item_data.get('quantity', 0)
                price = product.current_price
                total += price * quantity
            except Product.DoesNotExist:
                continue
                
        return total


# cart/views.py (تعديل CartDetailView)
class CartDetailView(CartMixin, TemplateView):
    """
    Display cart details
    Uses cart_context processor for cart_items with min_quantity validation
    """
    template_name = 'cart/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Note: cart_items, cart_count, cart_total, etc. are provided by
        # cart_context processor in context_processors.py
        # This processor handles min_quantity validation for automatic discounts

        # إضافة معلومات عما إذا كان المستخدم مسجل دخول أم لا
        context['is_authenticated'] = self.request.user.is_authenticated
        context['login_url'] = '/accounts/login/?next=/checkout/'  # تعديل هذا حسب مسار تسجيل الدخول في مشروعك

        return context

class AddToCartView(CartMixin, View):
    """
    Add product to cart
    """
    def post(self, request, product_id):
        try:
            # طباعة معلومات الطلب
            print(f"طلب إضافة للسلة - المنتج: {product_id}")
            print(f"البيانات: {request.POST}")

            # الحصول على المنتج
            product = get_object_or_404(Product, id=product_id, is_active=True)

            # الحصول على المتغير (إذا وجد)
            variant_id = request.POST.get('variant_id')
            variant = None
            if variant_id:
                variant = ProductVariant.objects.filter(id=variant_id, product=product).first()

            # الحصول على الكمية
            quantity = int(request.POST.get('quantity', 1))

            # مفتاح عنصر السلة
            cart_item_key = f"{product_id}_{variant_id}" if variant_id else str(product_id)

            # الحصول على السلة
            cart = self.get_cart(request)
            print(f"السلة قبل الإضافة: {cart}")

            # إضافة المنتج للسلة
            if cart_item_key in cart:
                cart[cart_item_key]['quantity'] += quantity
            else:
                cart[cart_item_key] = {
                    'product_id': product_id,
                    'quantity': quantity,
                    'name': product.name,
                    'price': str(variant.current_price if variant else product.current_price)
                }

                if variant:
                    cart[cart_item_key]['variant_id'] = variant.id

            # حفظ السلة
            self.save_cart(request, cart)
            print(f"السلة بعد الإضافة: {cart}")

            # التحقق من تحديث الجلسة
            print(f"تم تعديل الجلسة: {request.session.modified}")

            # الرد بنجاح
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'تمت إضافة "{product.name}" إلى السلة',
                    'cart_count': self.get_cart_items_count(request),
                    'cart_total': str(self.get_cart_total(request))
                })

            # إعادة التوجيه إذا لم يكن طلب AJAX
            return redirect('cart:cart_detail')

        except Exception as e:
            # تسجيل الخطأ بالتفصيل
            import traceback
            traceback.print_exc()

            # الرد بالخطأ
            error_msg = f"حدث خطأ: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })

            # إعادة التوجيه مع رسالة خطأ
            messages.error(request, error_msg)
            return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


# class UpdateCartItemView(CartMixin, View):
#     """
#     Update cart item quantity
#     """
#     def post(self, request, item_id):
#         cart = self.get_cart(request)
#         quantity = int(request.POST.get('quantity', 1))
#
#         if str(item_id) in cart:
#             if quantity > 0:
#                 # Check stock
#                 product_id = cart[str(item_id)]['product_id']
#                 product = get_object_or_404(Product, id=product_id)
#
#                 if product.track_inventory and quantity > product.available_quantity:
#                     messages.error(request, _('الكمية المطلوبة غير متوفرة'))
#                 else:
#                     cart[str(item_id)]['quantity'] = quantity
#                     messages.success(request, _('تم تحديث الكمية'))
#             else:
#                 del cart[str(item_id)]
#                 messages.success(request, _('تم إزالة المنتج من السلة'))
#
#             self.save_cart(request, cart)
#
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'cart_count': self.get_cart_items_count(request),
#                 'cart_total': str(self.get_cart_total(request))
#             })
#
#         return redirect('cart:cart_detail')

class UpdateCartItemView(CartMixin, View):
    """
    طريقة عرض لتحديث كمية عنصر في سلة التسوق
    تدعم طلبات AJAX وطلبات HTTP العادية
    """

    def post(self, request, item_id):
        """
        معالجة طلب POST لتحديث كمية عنصر

        Args:
            request: طلب HTTP
            item_id: معرف عنصر السلة

        Returns:
            JsonResponse للطلبات من نوع AJAX
            HTTP redirect للطلبات العادية
        """
        cart = self.get_cart(request)
        item_key = str(item_id)  # تحويل المعرف إلى نص
        quantity = int(request.POST.get('quantity', 1))

        # تهيئة بيانات الاستجابة
        response_data = {
            'success': False,
            'message': '',
            'item_id': item_key,
            'item_quantity': quantity,
            'item_subtotal': '0.00',  # قيمة افتراضية
            'cart_count': 0,
            'cart_subtotal': '0.00',
            'cart_tax': '0.00',
            'cart_total': '0.00',
        }

        # التحقق من وجود العنصر في السلة
        if item_key in cart:
            try:
                if quantity > 0:
                    # الحصول على بيانات المنتج
                    product_id = cart[item_key]['product_id']
                    product = get_object_or_404(Product, id=product_id)

                    # الحصول على المتغير إن وجد
                    variant = None
                    variant_id = cart[item_key].get('variant_id')
                    if variant_id:
                        try:
                            variant = ProductVariant.objects.get(
                                id=variant_id,
                                product=product,
                                is_active=True
                            )
                        except ProductVariant.DoesNotExist:
                            pass

                    # التحقق من الكمية المتاحة
                    if variant and variant.track_inventory:
                        available_quantity = variant.stock_quantity - variant.reserved_quantity
                        track_inventory = True
                    else:
                        available_quantity = product.stock_quantity - product.reserved_quantity
                        track_inventory = product.track_inventory

                    # التحقق من توفر المخزون
                    if track_inventory and quantity > available_quantity:
                        response_data['message'] = _('الكمية المطلوبة غير متوفرة! المتاح حاليا: {}'.format(available_quantity))
                        messages.error(request, response_data['message'])
                    else:
                        # تحديث الكمية في السلة
                        cart[item_key]['quantity'] = quantity
                        response_data['message'] = _('تم تحديث الكمية بنجاح')
                        response_data['success'] = True
                        messages.success(request, response_data['message'])
                else:
                    # إذا كانت الكمية 0 أو أقل، قم بإزالة العنصر
                    del cart[item_key]
                    response_data['message'] = _('تم إزالة المنتج من السلة')
                    response_data['success'] = True
                    messages.success(request, response_data['message'])

                # حفظ التغييرات في السلة
                self.save_cart(request, cart)

                # الحصول على بيانات السلة المحدثة
                cart_context = self.get_cart_context(request)

                # تحديث بيانات الاستجابة بالقيم الجديدة
                # Extract pre-tax price: price_before_tax = price / 1.16
                def without_tax(value):
                    return round(value / Decimal('1.16'), 4)

                response_data.update({
                    'cart_count': cart_context['cart_count'],
                    'cart_subtotal': str(without_tax(cart_context['cart_subtotal'])),
                    'cart_tax': str(round(cart_context['cart_tax'], 2)),
                    'cart_total': str(cart_context['cart_total']),  # Total with tax (no without_tax filter)
                    # Coupon discount info
                    'coupon_discount': str(without_tax(cart_context.get('coupon_discount', Decimal('0.00')))),
                    'has_coupon': cart_context.get('applied_coupon') is not None,
                    'coupon_code': cart_context.get('coupon_code', ''),
                    'eligible_items_count': cart_context.get('eligible_items_count', 0),
                    # Automatic discount info
                    'has_automatic_discount': cart_context.get('has_automatic_discount', False),
                    'automatic_discount_savings': str(without_tax(cart_context.get('automatic_discount_savings', Decimal('0.00')))),
                    'cart_original_subtotal': str(without_tax(cart_context.get('cart_original_subtotal', Decimal('0.00')))),
                    'automatic_discount_info': cart_context.get('automatic_discount_info'),
                })

                # البحث عن معلومات العنصر المحدث
                if quantity > 0:  # فقط إذا لم تتم إزالة العنصر
                    for item in cart_context['cart_items']:
                        if item['id'] == item_key:
                            response_data['item_subtotal'] = str(without_tax(item['subtotal']))
                            response_data['item_price'] = str(without_tax(item['price']))
                            response_data['item_original_price'] = str(without_tax(item['original_price']))
                            response_data['item_original_subtotal'] = str(without_tax(item.get('original_subtotal', item['subtotal'])))
                            # Add automatic discount info for this item
                            response_data['item_has_automatic_discount'] = item.get('has_automatic_discount', False)
                            response_data['item_savings'] = str(without_tax(item.get('savings', Decimal('0.00'))))
                            # Add coupon info for this item
                            response_data['item_coupon_eligible'] = item.get('coupon_eligible', False)
                            response_data['item_coupon_discount'] = str(without_tax(item.get('coupon_discount', Decimal('0.00'))))
                            response_data['item_subtotal_after_coupon'] = str(without_tax(item.get('subtotal_after_coupon', item['subtotal'])))
                            break

                # Add all items info for updating UI (includes both coupon and automatic discount)
                items_info = []
                for item in cart_context['cart_items']:
                    items_info.append({
                        'id': item['id'],
                        'price': str(without_tax(item['price'])),
                        'original_price': str(without_tax(item['original_price'])),
                        'subtotal': str(without_tax(item['subtotal'])),
                        'original_subtotal': str(without_tax(item.get('original_subtotal', item['subtotal']))),
                        # Automatic discount info
                        'has_automatic_discount': item.get('has_automatic_discount', False),
                        'savings': str(without_tax(item.get('savings', Decimal('0.00')))),
                        # Coupon info
                        'coupon_eligible': item.get('coupon_eligible', False),
                        'coupon_discount': str(without_tax(item.get('coupon_discount', Decimal('0.00')))),
                        'subtotal_after_coupon': str(without_tax(item.get('subtotal_after_coupon', item['subtotal']))),
                    })
                response_data['items_info'] = items_info
                # Keep items_coupon_info for backward compatibility
                response_data['items_coupon_info'] = items_info

            except Exception as e:
                # معالجة أي استثناءات
                response_data['message'] = str(e)
                response_data['success'] = False
                messages.error(request, _('حدث خطأ أثناء تحديث السلة'))

        else:
            # العنصر غير موجود في السلة
            response_data['message'] = _('العنصر غير موجود في السلة')
            messages.warning(request, response_data['message'])

            # الحصول على بيانات السلة الحالية
            cart_context = self.get_cart_context(request)

            # تحديث بيانات الاستجابة بالقيم الحالية
            response_data.update({
                'cart_count': cart_context['cart_count'],
                'cart_subtotal': str(round(cart_context['cart_subtotal'] / Decimal('1.16'), 4)),
                'cart_tax': str(round(cart_context['cart_tax'], 4)),
                'cart_total': str(cart_context['cart_total']),
            })

        # للطلبات من نوع AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(response_data)

        # للطلبات العادية، إعادة توجيه إلى صفحة السلة
        return redirect('cart:cart_detail')

    def get_cart_context(self, request):
        """
        الحصول على بيانات السلة من context processor

        Args:
            request: طلب HTTP

        Returns:
            dict: بيانات السلة
        """
        from .context_processors import cart_context
        return cart_context(request)


class RemoveFromCartView(CartMixin, View):
    """
    Remove item from cart
    """
    def post(self, request, item_id):
        cart = self.get_cart(request)
        
        if str(item_id) in cart:
            del cart[str(item_id)]
            self.save_cart(request, cart)
            messages.success(request, _('تم إزالة المنتج من السلة'))
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': self.get_cart_items_count(request),
                'cart_total': str(self.get_cart_total(request))
            })
        
        return redirect('cart:cart_detail')


class ClearCartView(CartMixin, View):
    """
    Clear all items from cart
    """
    def post(self, request):
        request.session['cart'] = {}
        for key in ['delivery_method', 'pickup_branch_id', 'coupon_code', 'coupon_discount_id', 'shipping_city']:
            request.session.pop(key, None)
        request.session.modified = True
        messages.success(request, _('تم إفراغ السلة'))
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': str(_('تم إفراغ السلة'))
            })
        
        return redirect('cart:cart_detail')


class ApplyCouponView(CartMixin, View):
    """
    Apply coupon to cart
    """
    def post(self, request):
        from products.models import ProductDiscount
        from django.utils import timezone

        coupon_code = request.POST.get('coupon_code', '').strip().upper()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not coupon_code:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': str(_('الرجاء إدخال كود الخصم'))
                })
            messages.error(request, _('الرجاء إدخال كود الخصم'))
            return redirect('cart:cart_detail')

        # البحث عن الخصم بالكود
        try:
            now = timezone.now()
            discount = ProductDiscount.objects.filter(
                code__iexact=coupon_code,
                is_active=True,
                requires_coupon_code=True,
                start_date__lte=now
            ).filter(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
            ).first()

            if not discount:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': str(_('كود الخصم غير صالح أو منتهي الصلاحية'))
                    })
                messages.error(request, _('كود الخصم غير صالح أو منتهي الصلاحية'))
                return redirect('cart:cart_detail')

            # التحقق من عدد مرات الاستخدام
            if discount.max_uses and discount.current_uses >= discount.max_uses:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': str(_('تم استنفاد عدد مرات استخدام هذا الكود'))
                    })
                messages.error(request, _('تم استنفاد عدد مرات استخدام هذا الكود'))
                return redirect('cart:cart_detail')

            # حفظ الكود في الجلسة
            request.session['coupon_code'] = coupon_code
            request.session['coupon_discount_id'] = discount.id
            request.session.modified = True

            # حساب مجموع السلة للتحقق من الحد الأدنى للشراء والحد الأقصى للخصم
            from .context_processors import cart_context
            cart_ctx = cart_context(request)
            cart_original_subtotal = cart_ctx.get('cart_original_subtotal', Decimal('0.00'))
            max_discount_applied = cart_ctx.get('max_discount_applied', False)
            coupon_discount_amount = cart_ctx.get('coupon_discount', Decimal('0.00'))

            # التحقق من الحد الأدنى للشراء
            meets_min_purchase = True
            min_purchase_message = ''
            if discount.min_purchase_amount and cart_original_subtotal < discount.min_purchase_amount:
                meets_min_purchase = False
                min_purchase_message = _('تم حفظ كود الخصم، لكن لا يمكن تطبيقه لأن المجموع أقل من {} د.أ').format(int(discount.min_purchase_amount))

            # رسالة الحد الأقصى للخصم
            max_discount_message = ''
            if max_discount_applied and discount.max_discount_amount:
                max_discount_message = _('تم تطبيق الحد الأقصى للخصم: {} د.أ').format(round(float(discount.max_discount_amount) / 1.16, 2))

            if is_ajax:
                if meets_min_purchase:
                    message = str(_('تم تطبيق كود الخصم بنجاح'))
                    if max_discount_message:
                        message += ' - ' + str(max_discount_message)
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'discount_name': discount.name,
                        'discount_type': discount.discount_type,
                        'discount_value': str(discount.value),
                        'max_discount_applied': max_discount_applied,
                        'max_discount_amount': str(discount.max_discount_amount) if discount.max_discount_amount else None
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'message': str(min_purchase_message),
                        'warning': True,
                        'discount_name': discount.name,
                        'min_purchase_amount': str(discount.min_purchase_amount)
                    })

            if meets_min_purchase:
                success_message = _('تم تطبيق كود الخصم بنجاح')
                if max_discount_message:
                    success_message = str(success_message) + ' - ' + str(max_discount_message)
                messages.success(request, success_message)
            else:
                messages.warning(request, min_purchase_message)

        except Exception as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': str(_('حدث خطأ أثناء تطبيق كود الخصم'))
                })
            messages.error(request, _('حدث خطأ أثناء تطبيق كود الخصم'))

        return redirect('cart:cart_detail')


class RemoveCouponView(CartMixin, View):
    """
    Remove coupon from cart
    """
    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if 'coupon_code' in request.session:
            del request.session['coupon_code']
        if 'coupon_discount_id' in request.session:
            del request.session['coupon_discount_id']
        request.session.modified = True

        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': str(_('تم إزالة كود الخصم'))
            })

        messages.success(request, _('تم إزالة كود الخصم'))
        return redirect('cart:cart_detail')


class UpdateShippingCityView(CartMixin, View):
    """
    Update shipping city in session for shipping fee calculation
    """
    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        city = request.POST.get('city', 'amman')

        # Validate city value
        if city not in ['amman', 'other']:
            city = 'amman'

        # Save to session
        request.session['shipping_city'] = city
        request.session.modified = True

        if is_ajax:
            # Get updated cart context
            from .context_processors import cart_context
            cart_ctx = cart_context(request)

            return JsonResponse({
                'success': True,
                'message': str(_('تم تحديث منطقة الشحن')),
                'shipping_fee': str(cart_ctx.get('cart_shipping', 0)),
                'cart_total': str(cart_ctx.get('cart_total', 0)),
                'city': city
            })

        return redirect('cart:cart_detail')


class UpdateDeliveryMethodView(CartMixin, View):
    def post(self, request):
        from core.models import Branch

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        method = request.POST.get('delivery_method', 'pickup')
        branch_id = request.POST.get('branch_id', '')

        if method not in ['delivery', 'pickup']:
            method = 'pickup'

        request.session['delivery_method'] = method
        if method == 'pickup' and branch_id:
            try:
                branch = Branch.objects.get(id=int(branch_id), is_active=True)
                request.session['pickup_branch_id'] = branch.id
            except (Branch.DoesNotExist, ValueError, TypeError):
                request.session.pop('pickup_branch_id', None)
        else:
            request.session.pop('pickup_branch_id', None)
        request.session.modified = True

        if is_ajax:
            from .context_processors import cart_context
            cart_ctx = cart_context(request)
            return JsonResponse({
                'success': True,
                'shipping_fee': str(cart_ctx.get('cart_shipping', 0)),
                'cart_total': str(cart_ctx.get('cart_total', 0)),
                'delivery_method': method,
            })
        return redirect('cart:cart_detail')

