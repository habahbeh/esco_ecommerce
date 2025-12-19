# cart/context_processors.py
"""
Cart Context Processor
Makes cart data available in all templates
"""

from decimal import Decimal
from django.conf import settings
from products.models import Product, ProductVariant
import logging

logger = logging.getLogger(__name__)


def cart_context(request):
    """
    Add cart information to all templates

    Returns:
        dict: Context variables for cart
            - cart: The cart session data
            - cart_items: List of cart items with product details
            - cart_count: Total number of items in cart
            - cart_total: Total price of all items
            - cart_subtotal: Subtotal before tax/shipping
            - cart_tax: Tax amount
            - cart_shipping: Shipping cost
            - cart_discount: Discount amount
            - cart_is_empty: Boolean indicating if cart is empty
            - cart_has_digital: Boolean indicating if cart has digital products
            - cart_has_physical: Boolean indicating if cart has physical products
    """

    # Initialize cart from session
    cart = request.session.get('cart', {})

    # Initialize variables
    cart_items = []
    cart_total = Decimal('0.00')
    cart_subtotal = Decimal('0.00')
    cart_tax = Decimal('0.00')
    cart_shipping = Decimal('0.00')
    cart_discount = Decimal('0.00')
    cart_count = 0
    cart_weight = Decimal('0.00')
    has_digital = False
    has_physical = False

    # Process cart items
    #for item_id, item_data in cart.items():
    for item_id, item_data in list(cart.items()):
        try:
            # Get product
            product_id = item_data.get('product_id')
            if not product_id:
                continue

            product = Product.objects.select_related('category', 'brand').get(
                id=product_id,
                is_active=True,
                status='published'
            )

            # Get variant if specified
            variant = None
            variant_id = item_data.get('variant_id')
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(
                        id=variant_id,
                        product=product,
                        is_active=True
                    )
                except ProductVariant.DoesNotExist:
                    logger.warning(f"Variant {variant_id} not found for product {product_id}")

            # Get quantity
            quantity = int(item_data.get('quantity', 1))

            # Calculate price
            if variant and variant.base_price:
                price = variant.current_price if hasattr(variant, 'current_price') else variant.base_price
                stock_quantity = variant.stock_quantity
                track_inventory = variant.track_inventory
            else:
                price = product.current_price
                stock_quantity = product.stock_quantity
                track_inventory = product.track_inventory

            # Calculate subtotal for this item
            item_subtotal = price * quantity

            # Check stock availability
            in_stock = True
            stock_message = ""
            if track_inventory:
                available_qty = stock_quantity - (variant.reserved_quantity if variant else product.reserved_quantity)
                if quantity > available_qty:
                    in_stock = False
                    stock_message = f"متوفر {available_qty} قطعة فقط"
                elif available_qty <= 5:
                    stock_message = f"متبقي {available_qty} قطع فقط"

            # Calculate item weight
            item_weight = Decimal('0.00')
            if product.weight and product.requires_shipping:
                item_weight = product.weight * quantity
                cart_weight += item_weight

            # Check product type
            if product.is_digital:
                has_digital = True
            if product.requires_shipping:
                has_physical = True

            # Create cart item object
            cart_item = {
                'id': item_id,
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'price': price,
                'original_price': product.base_price,
                'subtotal': item_subtotal,
                'in_stock': in_stock,
                'stock_message': stock_message,
                'stock_quantity': stock_quantity,
                'weight': item_weight,
                'savings': (product.base_price - price) * quantity if product.has_discount else Decimal('0.00'),
                'image': product.default_image.image.url if product.default_image else None,
                'variant_info': {
                    'id': variant.id if variant else None,
                    'name': variant.name if variant else None,
                    'sku': variant.sku if variant else product.sku,
                    'attributes': variant.attributes if variant else {}
                } if variant else None
            }

            # Add to totals
            cart_count += quantity
            cart_subtotal += item_subtotal

            # Add to items list
            cart_items.append(cart_item)

        except Product.DoesNotExist:
            # Remove invalid items from cart
            logger.warning(f"Product {product_id} not found, removing from cart")
            del cart[item_id]
            request.session.modified = True
        except Exception as e:
            logger.error(f"Error processing cart item {item_id}: {str(e)}")
            continue

    # Calculate tax (if applicable)
    tax_rate = Decimal(getattr(settings, 'DEFAULT_TAX_RATE', '0.16'))  # 16% default
    if cart_subtotal > 0 and not has_digital:  # No tax on digital products
        cart_tax = cart_subtotal * tax_rate

    # تعريف القيمة الافتراضية قبل الشرط
    free_shipping_threshold = Decimal(getattr(settings, 'FREE_SHIPPING_THRESHOLD', '0.00'))

    # Calculate shipping
    if has_physical and cart_subtotal > 0:
        # Free shipping threshold
        free_shipping_threshold = Decimal(getattr(settings, 'FREE_SHIPPING_THRESHOLD', '50.00'))
        if cart_subtotal < free_shipping_threshold:
            # Basic shipping calculation
            base_shipping = Decimal(getattr(settings, 'BASE_SHIPPING_COST', '5.00'))
            weight_rate = Decimal(getattr(settings, 'SHIPPING_WEIGHT_RATE', '0.50'))  # per kg
            cart_shipping = base_shipping + (cart_weight * weight_rate)

    # Apply coupon discount if exists
    coupon_code = request.session.get('coupon_code')
    if coupon_code and cart_subtotal > 0:
        # Here you would validate and calculate coupon discount
        # For now, just a placeholder
        cart_discount = Decimal('0.00')

    # Calculate final total
    cart_total = cart_subtotal + cart_tax + cart_shipping - cart_discount

    # Prepare summary data
    cart_summary = {
        'items_count': cart_count,
        'unique_items': len(cart_items),
        'subtotal': cart_subtotal,
        'tax': cart_tax,
        'tax_rate': tax_rate * 100,  # As percentage
        'shipping': cart_shipping,
        'discount': cart_discount,
        'total': cart_total,
        'weight': cart_weight,
        'free_shipping_threshold': free_shipping_threshold if has_physical else None,
        'free_shipping_remaining': max(free_shipping_threshold - cart_subtotal,
                                       Decimal('0.00')) if has_physical else None,
        'has_free_shipping': cart_subtotal >= free_shipping_threshold if has_physical else True,
    }

    # Return context
    return {
        # Basic cart data
        'cart': cart,
        'cart_items': cart_items,
        'cart_count': cart_count,
        'cart_total': cart_total,
        'cart_subtotal': cart_subtotal,
        'cart_tax': cart_tax,
        'cart_shipping': cart_shipping,
        'cart_discount': cart_discount,

        # Cart state
        'cart_is_empty': cart_count == 0,
        'cart_has_items': cart_count > 0,
        'cart_has_digital': has_digital,
        'cart_has_physical': has_physical,
        'cart_has_mixed': has_digital and has_physical,

        # Additional info
        'cart_weight': cart_weight,
        'cart_summary': cart_summary,
        'coupon_code': coupon_code,

        # Messages for UI
        'cart_messages': {
            'empty': 'سلة التسوق فارغة',
            'free_shipping': f'احصل على شحن مجاني عند الشراء بقيمة {free_shipping_threshold} د.أ أو أكثر' if has_physical else None,
            'free_shipping_qualified': 'تهانينا! لقد حصلت على شحن مجاني' if has_physical and cart_summary[
                'has_free_shipping'] else None,
        }
    }


def cart_preview_context(request):
    """
    Lightweight cart context for header/navbar
    Only includes essential information for performance
    """
    cart = request.session.get('cart', {})
    cart_count = 0
    cart_total = Decimal('0.00')
    preview_items = []

    # Calculate quick totals
    for item_id, item_data in cart.items():
        quantity = int(item_data.get('quantity', 0))
        cart_count += quantity

        # Add to preview (max 3 items)
        if len(preview_items) < 3:
            try:
                product = Product.objects.only('id', 'name', 'slug').get(
                    id=item_data.get('product_id')
                )
                preview_items.append({
                    'name': product.name[:30] + '...' if len(product.name) > 30 else product.name,
                    'quantity': quantity,
                    'url': product.get_absolute_url()
                })
            except Product.DoesNotExist:
                pass

    # Quick total calculation (can be cached)
    if cart_count > 0:
        try:
            # This is a simplified calculation for preview
            # The full calculation is done in cart_context
            product_ids = [item.get('product_id') for item in cart.values()]
            products = Product.objects.filter(id__in=product_ids).only('id', 'base_price')

            for item_id, item_data in cart.items():
                product = next((p for p in products if p.id == item_data.get('product_id')), None)
                if product:
                    cart_total += product.current_price * item_data.get('quantity', 0)
        except Exception as e:
            logger.error(f"Error calculating cart preview total: {str(e)}")

    return {
        'cart_preview': {
            'count': cart_count,
            'total': cart_total,
            'items': preview_items,
            'has_more': len(cart) > 3
        }
    }