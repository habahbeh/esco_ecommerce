# cart/context_processors.py
from django.core.exceptions import ValidationError
from django.contrib.auth import logout
import logging

logger = logging.getLogger(__name__)


def cart(request):
    """
    معالج سياق للعربة - يضيف بيانات العربة إلى سياق القالب
    Cart context processor - adds cart data to template context
    """
    try:
        # التحقق من صحة المستخدم مع معالجة أخطاء UUID
        if hasattr(request, 'user') and request.user.is_authenticated:
            # المستخدم مسجل الدخول - جلب العربة من قاعدة البيانات
            from .models import Cart
            try:
                cart_obj, created = Cart.objects.get_or_create(user=request.user)
                cart_items = cart_obj.items.select_related(
                    'product',
                    'product__category',
                    'product__brand'
                ).prefetch_related('product__images')

                return {
                    'cart': cart_obj,
                    'cart_items': cart_items,
                    'cart_total_items': cart_obj.total_items,
                    'cart_total_price': cart_obj.total_price,
                }
            except Exception as e:
                logger.error(f"Error getting cart for user {request.user.id}: {e}")
                return get_empty_cart_context()
        else:
            # مستخدم غير مسجل - جلب العربة من الجلسة
            return get_session_cart_context(request)

    except ValidationError as e:
        # خطأ في UUID - تنظيف الجلسة وتسجيل خروج المستخدم
        logger.warning(f"UUID validation error in cart context processor: {e}")

        # تنظيف الجلسة
        if hasattr(request, 'session'):
            request.session.flush()

        # تسجيل خروج المستخدم إذا كان موجوداً
        if hasattr(request, 'user'):
            try:
                logout(request)
            except:
                pass

        return get_empty_cart_context()

    except Exception as e:
        # أي خطأ آخر
        logger.error(f"Unexpected error in cart context processor: {e}")
        return get_empty_cart_context()


def get_session_cart_context(request):
    """
    الحصول على سياق العربة من الجلسة للمستخدمين غير المسجلين
    Get cart context from session for anonymous users
    """
    try:
        cart_items = request.session.get('cart', {})
        total_items = 0
        total_price = 0

        if cart_items:
            from .models import Product
            cart_products = []

            for product_id, quantity in cart_items.items():
                try:
                    product = Product.objects.select_related(
                        'category', 'brand'
                    ).prefetch_related('images').get(
                        id=product_id,
                        is_active=True,
                        status='published'
                    )

                    cart_products.append({
                        'product': product,
                        'quantity': quantity,
                        'total_price': product.current_price * quantity
                    })

                    total_items += quantity
                    total_price += product.current_price * quantity

                except Product.DoesNotExist:
                    # إزالة المنتج غير الموجود من العربة
                    del request.session['cart'][product_id]
                    request.session.modified = True
                except Exception as e:
                    logger.error(f"Error processing cart item {product_id}: {e}")

            return {
                'cart': None,
                'cart_items': cart_products,
                'cart_total_items': total_items,
                'cart_total_price': total_price,
            }

    except Exception as e:
        logger.error(f"Error getting session cart: {e}")

    return get_empty_cart_context()


def get_empty_cart_context():
    """
    إرجاع سياق عربة فارغة
    Return empty cart context
    """
    return {
        'cart': None,
        'cart_items': [],
        'cart_total_items': 0,
        'cart_total_price': 0,
    }