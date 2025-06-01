# cart/signals.py
"""
Cart signals for stock management and notifications
ملف اختياري لإدارة المخزون والإشعارات
"""

from django.dispatch import Signal, receiver
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
import logging

logger = logging.getLogger('cart')

# Custom signals
cart_item_added = Signal()  # عند إضافة منتج للسلة
cart_item_removed = Signal()  # عند حذف منتج من السلة
cart_item_updated = Signal()  # عند تحديث كمية منتج
cart_cleared = Signal()  # عند إفراغ السلة


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    """
    دمج سلة الزائر مع سلة المستخدم عند تسجيل الدخول
    """
    try:
        # الحصول على سلة الزائر
        anonymous_cart = request.session.get('cart', {})

        if anonymous_cart:
            # هنا يمكن دمج السلة مع سلة المستخدم المحفوظة في قاعدة البيانات
            # إذا كان لديك نموذج Cart للمستخدمين المسجلين

            logger.info(f"Merging anonymous cart with {len(anonymous_cart)} items for user {user.username}")

            # مثال: حفظ السلة للمستخدم
            # user_cart = Cart.objects.get_or_create(user=user)[0]
            # for item_id, item_data in anonymous_cart.items():
            #     user_cart.add_item(...)

            # مسح سلة الزائر بعد الدمج
            # request.session['cart'] = {}

    except Exception as e:
        logger.error(f"Error merging cart on login: {str(e)}")


def update_product_stock_cache(product_id):
    """
    تحديث cache المخزون للمنتج
    """
    from products.models import Product

    try:
        product = Product.objects.get(id=product_id)
        cache_key = f"product_stock_{product_id}"
        cache.set(cache_key, {
            'quantity': product.stock_quantity,
            'reserved': product.reserved_quantity,
            'available': product.available_quantity,
            'in_stock': product.in_stock
        }, timeout=300)  # 5 minutes
    except Product.DoesNotExist:
        pass


def send_low_stock_notification(product):
    """
    إرسال إشعار عند انخفاض المخزون
    """
    if product.stock_quantity <= product.min_stock_level:
        # إرسال إيميل للإدارة
        logger.warning(f"Low stock alert for product {product.name} (ID: {product.id})")

        # يمكن إضافة إرسال إيميل هنا
        # from django.core.mail import send_mail
        # send_mail(
        #     'تنبيه: مخزون منخفض',
        #     f'المنتج {product.name} وصل للحد الأدنى من المخزون ({product.stock_quantity} قطعة)',
        #     'noreply@esco.com',
        #     ['admin@esco.com'],
        # )


def check_cart_items_availability(cart_items):
    """
    التحقق من توفر جميع منتجات السلة
    """
    from products.models import Product

    unavailable_items = []

    for item_id, item_data in cart_items.items():
        try:
            product = Product.objects.get(id=item_data['product_id'])
            requested_qty = item_data['quantity']

            if not product.in_stock or requested_qty > product.available_quantity:
                unavailable_items.append({
                    'product': product,
                    'requested': requested_qty,
                    'available': product.available_quantity
                })
        except Product.DoesNotExist:
            unavailable_items.append({
                'product_id': item_data['product_id'],
                'error': 'منتج محذوف'
            })

    return unavailable_items


# إشارات مخصصة للسلة
@receiver(cart_item_added)
def on_cart_item_added(sender, request, product_id, quantity, **kwargs):
    """
    عند إضافة منتج للسلة
    """
    logger.info(f"Product {product_id} added to cart with quantity {quantity}")

    # تحديث cache المخزون
    update_product_stock_cache(product_id)

    # تحديث إحصائيات المنتج
    # Product.objects.filter(id=product_id).update(
    #     cart_additions=F('cart_additions') + 1
    # )


@receiver(cart_item_removed)
def on_cart_item_removed(sender, request, product_id, **kwargs):
    """
    عند حذف منتج من السلة
    """
    logger.info(f"Product {product_id} removed from cart")

    # يمكن تتبع المنتجات المحذوفة من السلة
    # لتحليل سلوك المستخدمين


@receiver(cart_cleared)
def on_cart_cleared(sender, request, **kwargs):
    """
    عند إفراغ السلة
    """
    user_info = request.user.username if request.user.is_authenticated else 'Anonymous'
    logger.info(f"Cart cleared by {user_info}")


# Helper functions للاستخدام في views
def emit_cart_item_added(request, product_id, quantity):
    """
    إطلاق إشارة إضافة منتج للسلة
    """
    cart_item_added.send(
        sender=None,
        request=request,
        product_id=product_id,
        quantity=quantity
    )


def emit_cart_item_removed(request, product_id):
    """
    إطلاق إشارة حذف منتج من السلة
    """
    cart_item_removed.send(
        sender=None,
        request=request,
        product_id=product_id
    )


def emit_cart_cleared(request):
    """
    إطلاق إشارة إفراغ السلة
    """
    cart_cleared.send(
        sender=None,
        request=request
    )

