# cart/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
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
    """
    template_name = 'cart/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart(self.request)
        cart_items = []

        for item_id, item_data in cart.items():
            try:
                product = Product.objects.get(id=item_data['product_id'])
                variant = None
                if 'variant_id' in item_data:
                    try:
                        variant = ProductVariant.objects.get(id=item_data['variant_id'])
                    except ProductVariant.DoesNotExist:
                        pass

                cart_items.append({
                    'id': item_id,
                    'product': product,
                    'variant': variant,
                    'quantity': item_data.get('quantity', 1),
                    'price': variant.current_price if variant else product.current_price,
                    'subtotal': (variant.current_price if variant else product.current_price) * item_data.get('quantity', 1)
                })
            except Product.DoesNotExist:
                continue

        context['cart_items'] = cart_items
        # context['cart_total'] = self.get_cart_total(self.request)
        context['cart_count'] = self.get_cart_items_count(self.request)

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
                response_data.update({
                    'cart_count': cart_context['cart_count'],
                    'cart_subtotal': str(round(cart_context['cart_subtotal']/ Decimal('1.16'),2)),
                    'cart_tax': str(round(cart_context['cart_tax'],2)),
                    'cart_total': str(round(cart_context['cart_total']/ Decimal('1.16'),2)),
                })

                # البحث عن معلومات العنصر المحدث
                if quantity > 0:  # فقط إذا لم تتم إزالة العنصر
                    for item in cart_context['cart_items']:
                        if item['id'] == item_key:
                            response_data['item_subtotal'] = str(round(item['subtotal'] / Decimal('1.16'),2))
                            break

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
                'cart_subtotal': str(round(cart_context['cart_subtotal'] / Decimal('1.16'),2)),
                'cart_tax': str(round(cart_context['cart_tax'],2)),
                'cart_total': str(round(cart_context['cart_total'] / Decimal('1.16'),2)),
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
        coupon_code = request.POST.get('coupon_code', '').strip()
        
        if not coupon_code:
            messages.error(request, _('الرجاء إدخال كود الخصم'))
        else:
            # Here you would implement coupon validation logic
            # For now, just store the coupon code
            request.session['coupon_code'] = coupon_code
            messages.success(request, _('تم تطبيق كود الخصم'))
        
        return redirect('cart:cart_detail')


class RemoveCouponView(CartMixin, View):
    """
    Remove coupon from cart
    """
    def post(self, request):
        if 'coupon_code' in request.session:
            del request.session['coupon_code']
            request.session.modified = True
            messages.success(request, _('تم إزالة كود الخصم'))
        
        return redirect('cart:cart_detail')

