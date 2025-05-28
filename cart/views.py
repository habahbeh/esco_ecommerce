from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import Cart, CartItem
from products.models import Product, ProductVariant

class CartView(View):
    """
    عرض سلة التسوق - يعرض محتويات سلة التسوق
    Cart view - displays the contents of the shopping cart
    """
    template_name = 'cart/cart.html'

    def get(self, request):
        # الحصول على سلة التسوق الحالية أو إنشاء واحدة جديدة
        # Get the current cart or create a new one
        cart = self._get_or_create_cart(request)

        context = {
            'cart': cart,
            'cart_items': cart.items.all() if cart else []
        }

        return render(request, self.template_name, context)

    def _get_or_create_cart(self, request):
        """
        الحصول على سلة التسوق الحالية أو إنشاء واحدة جديدة
        Get the current cart or create a new one
        """
        if request.user.is_authenticated:
            # للمستخدمين المسجلين، استخدم معرف المستخدم
            # For logged-in users, use the user ID
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            # للزوار، استخدم مفتاح الجلسة
            # For visitors, use the session key
            session_key = request.session.session_key
            if not session_key:
                # إذا لم يكن هناك مفتاح جلسة، قم بإنشاء واحد
                # If there's no session key, create one
                request.session.create()
                session_key = request.session.session_key

            cart, created = Cart.objects.get_or_create(session_key=session_key)

        return cart

class AddToCartView(View):
    """
    عرض إضافة إلى السلة - يتيح للمستخدمين إضافة منتجات إلى سلة التسوق
    Add to cart view - allows users to add products to the shopping cart
    """
    def post(self, request, product_id):
        # الحصول على المنتج - Get the product
        product = get_object_or_404(Product, id=product_id, status='published', is_active=True)

        # الحصول على المتغير إذا تم تحديده - Get the variant if specified
        variant_id = request.POST.get('variant_id')
        variant = None

        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product, is_active=True)

        # الحصول على الكمية - Get the quantity
        quantity = int(request.POST.get('quantity', 1))

        # الحصول على سلة التسوق أو إنشاء واحدة جديدة - Get the cart or create a new one
        cart = self._get_or_create_cart(request)

        # إضافة المنتج إلى السلة - Add the product to the cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )

        if not created:
            # إذا كان العنصر موجودًا بالفعل، قم بزيادة الكمية
            # If the item already exists, increase the quantity
            cart_item.quantity += quantity
            cart_item.save()

        # الرد حسب نوع الطلب - Respond based on request type
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # إذا كان طلب Ajax، قم بإرجاع استجابة JSON
            # If it's an Ajax request, return a JSON response
            return JsonResponse({
                'status': 'success',
                'message': _('تمت إضافة المنتج إلى السلة'),
                'cart_count': cart.total_items,
                'cart_total': cart.total_price
            })
        else:
            # إذا كان طلبًا عاديًا، قم بإعادة التوجيه إلى السلة
            # If it's a regular request, redirect to the cart
            messages.success(request, _('تمت إضافة المنتج إلى السلة'))
            return redirect('cart:cart')

    def _get_or_create_cart(self, request):
        """
        الحصول على سلة التسوق الحالية أو إنشاء واحدة جديدة
        Get the current cart or create a new one
        """
        if request.user.is_authenticated:
            # للمستخدمين المسجلين، استخدم معرف المستخدم
            # For logged-in users, use the user ID
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            # للزوار، استخدم مفتاح الجلسة
            # For visitors, use the session key
            session_key = request.session.session_key
            if not session_key:
                # إذا لم يكن هناك مفتاح جلسة، قم بإنشاء واحد
                # If there's no session key, create one
                request.session.create()
                session_key = request.session.session_key

            cart, created = Cart.objects.get_or_create(session_key=session_key)

        return cart

class UpdateCartView(View):
    """
    عرض تحديث السلة - يتيح للمستخدمين تحديث كميات العناصر في سلة التسوق
    Update cart view - allows users to update quantities of items in the shopping cart
    """
    def post(self, request, item_id):
        # الحصول على عنصر السلة - Get the cart item
        cart_item = get_object_or_404(CartItem, id=item_id)

        # التحقق من أن العنصر ينتمي إلى سلة المستخدم
        # Check that the item belongs to the user's cart
        if request.user.is_authenticated:
            if cart_item.cart.user != request.user:
                messages.error(request, _('ليس لديك إذن لتحديث هذا العنصر'))
                return redirect('cart:cart')
        else:
            session_key = request.session.session_key
            if cart_item.cart.session_key != session_key:
                messages.error(request, _('ليس لديك إذن لتحديث هذا العنصر'))
                return redirect('cart:cart')

        # الحصول على الكمية الجديدة - Get the new quantity
        quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            # تحديث الكمية - Update the quantity
            cart_item.quantity = quantity
            cart_item.save()
        else:
            # إذا كانت الكمية 0 أو أقل، قم بإزالة العنصر
            # If the quantity is 0 or less, remove the item
            cart_item.delete()

        # الرد حسب نوع الطلب - Respond based on request type
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # إذا كان طلب Ajax، قم بإرجاع استجابة JSON
            # If it's an Ajax request, return a JSON response
            return JsonResponse({
                'status': 'success',
                'message': _('تم تحديث السلة'),
                'cart_count': cart_item.cart.total_items,
                'cart_total': cart_item.cart.total_price,
                'item_total': cart_item.total_price
            })
        else:
            # إذا كان طلبًا عاديًا، قم بإعادة التوجيه إلى السلة
            # If it's a regular request, redirect to the cart
            messages.success(request, _('تم تحديث السلة'))
            return redirect('cart:cart')

class RemoveFromCartView(View):
    """
    عرض إزالة من السلة - يتيح للمستخدمين إزالة عناصر من سلة التسوق
    Remove from cart view - allows users to remove items from the shopping cart
    """
    def post(self, request, item_id):
        # الحصول على عنصر السلة - Get the cart item
        cart_item = get_object_or_404(CartItem, id=item_id)

        # التحقق من أن العنصر ينتمي إلى سلة المستخدم
        # Check that the item belongs to the user's cart
        if request.user.is_authenticated:
            if cart_item.cart.user != request.user:
                messages.error(request, _('ليس لديك إذن لإزالة هذا العنصر'))
                return redirect('cart:cart')
        else:
            session_key = request.session.session_key
            if cart_item.cart.session_key != session_key:
                messages.error(request, _('ليس لديك إذن لإزالة هذا العنصر'))
                return redirect('cart:cart')

        # الحصول على السلة قبل حذف العنصر - Get the cart before deleting the item
        cart = cart_item.cart

        # حذف العنصر - Delete the item
        cart_item.delete()

        # الرد حسب نوع الطلب - Respond based on request type
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # إذا كان طلب Ajax، قم بإرجاع استجابة JSON
            # If it's an Ajax request, return a JSON response
            return JsonResponse({
                'status': 'success',
                'message': _('تمت إزالة العنصر من السلة'),
                'cart_count': cart.total_items,
                'cart_total': cart.total_price
            })
        else:
            # إذا كان طلبًا عاديًا، قم بإعادة التوجيه إلى السلة
            # If it's a regular request, redirect to the cart
            messages.success(request, _('تمت إزالة العنصر من السلة'))
            return redirect('cart:cart')

class CheckoutView(View):
    """
    عرض الدفع - يتيح للمستخدمين إكمال عملية الشراء
    Checkout view - allows users to complete the purchase process
    """
    template_name = 'cart/checkout.html'

    def get(self, request):
        # الحصول على سلة التسوق - Get the shopping cart
        cart = self._get_cart(request)

        if not cart or cart.items.count() == 0:
            messages.warning(request, _('سلة التسوق فارغة'))
            return redirect('cart:cart')

        # إعداد بيانات المستخدم للنموذج إذا كان مسجل الدخول
        # Set up user data for the form if logged in
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'full_name': f"{request.user.first_name} {request.user.last_name}".strip(),
                'email': request.user.email,
                'phone': request.user.phone or '',
                'address': request.user.address or ''
            }

        context = {
            'cart': cart,
            'cart_items': cart.items.all(),
            'initial_data': initial_data
        }

        return render(request, self.template_name, context)

    def post(self, request):
        # الحصول على سلة التسوق - Get the shopping cart
        cart = self._get_cart(request)

        if not cart or cart.items.count() == 0:
            messages.warning(request, _('سلة التسوق فارغة'))
            return redirect('cart:cart')

        # معالجة بيانات النموذج - Process form data
        from orders.models import Order, OrderItem

        # إنشاء الطلب - Create the order
        order = Order(
            user=request.user if request.user.is_authenticated else None,
            cart=cart,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            shipping_address=request.POST.get('address'),
            shipping_city=request.POST.get('city'),
            shipping_state=request.POST.get('state'),
            shipping_country=request.POST.get('country'),
            shipping_postal_code=request.POST.get('postal_code', ''),
            total_price=cart.total_price,
            shipping_cost=0,  # يمكن حساب تكلفة الشحن بناءً على القواعد - Can calculate shipping cost based on rules
            tax_amount=0,  # يمكن حساب الضريبة بناءً على القواعد - Can calculate tax based on rules
            payment_method=request.POST.get('payment_method')
        )

        # حساب المجموع الكلي - Calculate the grand total
        order.grand_total = order.total_price + order.shipping_cost + order.tax_amount

        # حفظ الطلب - Save the order
        order.save()

        # إنشاء عناصر الطلب - Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product_name=cart_item.product.name,
                product_id=str(cart_item.product.id),
                variant_name=cart_item.variant.name if cart_item.variant else '',
                variant_id=str(cart_item.variant.id) if cart_item.variant else '',
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total_price
            )

        # معالجة الدفع - Process payment
        # هنا يمكن إضافة رمز لمعالجة الدفع باستخدام بوابة دفع - Here you can add code to process payment using a payment gateway

        # بعد الانتهاء من الدفع، قم بتحديث حالة الطلب
        # After payment is complete, update the order status
        order.status = 'processing'
        order.payment_status = 'paid'
        order.save()

        # إفراغ السلة - Clear the cart
        cart.delete()

        # إعادة التوجيه إلى صفحة الشكر - Redirect to thank you page
        return redirect('orders:thank_you', order_id=order.id)

    def _get_cart(self, request):
        """
        الحصول على سلة التسوق الحالية
        Get the current shopping cart
        """
        if request.user.is_authenticated:
            # للمستخدمين المسجلين، استخدم معرف المستخدم
            # For logged-in users, use the user ID
            try:
                return Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                return None
        else:
            # للزوار، استخدم مفتاح الجلسة
            # For visitors, use the session key
            session_key = request.session.session_key
            if not session_key:
                return None

            try:
                return Cart.objects.get(session_key=session_key)
            except Cart.DoesNotExist:
                return None