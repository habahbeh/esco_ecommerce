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
        context['cart_total'] = self.get_cart_total(self.request)
        context['cart_count'] = self.get_cart_items_count(self.request)
        
        return context


class AddToCartView(CartMixin, View):
    """
    Add product to cart
    """
    def post(self, request, product_id):
        # Get product
        product = get_object_or_404(Product, id=product_id, is_active=True, status='published')
        
        # Get cart
        cart = self.get_cart(request)
        
        # Get quantity and variant
        quantity = int(request.POST.get('quantity', 1))
        variant_id = request.POST.get('variant_id')
        
        # Create cart item key
        cart_item_key = str(product_id)
        if variant_id:
            cart_item_key = f"{product_id}_{variant_id}"
        
        # Check stock
        if product.track_inventory:
            available_qty = product.available_quantity
            current_qty = cart.get(cart_item_key, {}).get('quantity', 0)
            
            if current_qty + quantity > available_qty:
                messages.error(request, _('الكمية المطلوبة غير متوفرة'))
                return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))
        
        # Add to cart
        if cart_item_key in cart:
            cart[cart_item_key]['quantity'] += quantity
        else:
            cart[cart_item_key] = {
                'product_id': product_id,
                'quantity': quantity,
                'name': product.name,
                'price': str(product.current_price)
            }
            
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id)
                    cart[cart_item_key]['variant_id'] = variant_id
                    cart[cart_item_key]['variant_name'] = variant.name
                except ProductVariant.DoesNotExist:
                    pass
        
        # Save cart
        self.save_cart(request, cart)
        
        # Success message
        messages.success(request, _('تمت إضافة المنتج إلى السلة'))

        # إطلاق الإشارة
        emit_cart_item_added(request, product_id, quantity)
        
        # Return response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': str(_('تمت إضافة المنتج إلى السلة')),
                'cart_count': self.get_cart_items_count(request),
                'cart_total': str(self.get_cart_total(request))
            })
        
        return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


class UpdateCartItemView(CartMixin, View):
    """
    Update cart item quantity
    """
    def post(self, request, item_id):
        cart = self.get_cart(request)
        quantity = int(request.POST.get('quantity', 1))
        
        if str(item_id) in cart:
            if quantity > 0:
                # Check stock
                product_id = cart[str(item_id)]['product_id']
                product = get_object_or_404(Product, id=product_id)
                
                if product.track_inventory and quantity > product.available_quantity:
                    messages.error(request, _('الكمية المطلوبة غير متوفرة'))
                else:
                    cart[str(item_id)]['quantity'] = quantity
                    messages.success(request, _('تم تحديث الكمية'))
            else:
                del cart[str(item_id)]
                messages.success(request, _('تم إزالة المنتج من السلة'))
            
            self.save_cart(request, cart)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': self.get_cart_items_count(request),
                'cart_total': str(self.get_cart_total(request))
            })
        
        return redirect('cart:cart_detail')


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