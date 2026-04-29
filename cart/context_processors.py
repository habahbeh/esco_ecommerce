# cart/context_processors.py
"""
Cart Context Processor
Makes cart data available in all templates
Updated: min_quantity validation for automatic discounts
"""

from decimal import Decimal
from django.conf import settings
from products.models import Product, ProductVariant, ProductDiscount
from core.models import SiteSettings
from django.utils import timezone
from django.db.models import Q
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

    # Track automatic (campaign) discount savings
    automatic_discount_savings = Decimal('0.00')
    cart_original_subtotal = Decimal('0.00')  # Subtotal before any automatic discounts
    automatic_discount_info = None  # Store discount type/value info

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

            # Calculate price - check min_quantity for automatic discounts
            if variant and variant.base_price:
                # For variants, check if min_quantity is met for automatic discounts
                base_price = variant.variant_base_price if hasattr(variant, 'variant_base_price') else variant.base_price
                # Variants inherit discount from product
                discount = product.get_best_campaign_discount()

                if discount and not discount.requires_coupon_code and discount.min_quantity:
                    # Automatic discount with min_quantity requirement
                    if quantity >= discount.min_quantity:
                        price = variant.current_price if hasattr(variant, 'current_price') else base_price
                    else:
                        # Don't apply discount - use base price
                        price = base_price
                else:
                    price = variant.current_price if hasattr(variant, 'current_price') else base_price

                stock_quantity = variant.stock_quantity
                track_inventory = variant.track_inventory
            else:
                # For products, check if min_quantity is met for automatic discounts
                base_price = product.base_price
                discount = product.get_best_campaign_discount()

                if discount and not discount.requires_coupon_code and discount.min_quantity:
                    # Automatic discount with min_quantity requirement
                    if quantity >= discount.min_quantity:
                        price = product.current_price
                    else:
                        # Don't apply discount - use base price
                        price = base_price
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

            # Calculate item savings from automatic discount
            item_savings = Decimal('0.00')
            item_original_subtotal = base_price * quantity
            has_automatic_discount = False

            if price < base_price:
                item_savings = (base_price - price) * quantity
                has_automatic_discount = True
                # Store discount info (from the first item that has a discount)
                if automatic_discount_info is None and discount:
                    automatic_discount_info = {
                        'type': discount.discount_type,
                        'value': discount.value,
                        'name': discount.name,
                    }

            # Create cart item object
            cart_item = {
                'id': item_id,
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'price': price,
                'original_price': base_price,
                'subtotal': item_subtotal,
                'original_subtotal': item_original_subtotal,
                'in_stock': in_stock,
                'stock_message': stock_message,
                'stock_quantity': stock_quantity,
                'weight': item_weight,
                'savings': item_savings,
                'has_automatic_discount': has_automatic_discount,
                'discount': discount if discount and not discount.requires_coupon_code else None,
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
            cart_original_subtotal += item_original_subtotal
            automatic_discount_savings += item_savings

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

    # Calculate tax (extract from tax-inclusive prices)
    tax_rate = Decimal(getattr(settings, 'DEFAULT_TAX_RATE', '0.16'))  # 16% default
    if cart_subtotal > 0 and not has_digital:  # No tax on digital products
        cart_tax = cart_subtotal - (cart_subtotal / (1 + tax_rate))

    # Get shipping settings from database
    try:
        site_settings = SiteSettings.get_settings()
        shipping_enabled = site_settings.shipping_enabled
        shipping_fee_amman = site_settings.shipping_fee_amman
        shipping_fee_other = site_settings.shipping_fee_other
        free_shipping_threshold = site_settings.free_shipping_threshold
        pickup_enabled = getattr(site_settings, 'pickup_enabled', False)
    except Exception:
        # Fallback to defaults if settings not available
        shipping_enabled = True
        shipping_fee_amman = Decimal('2.00')
        shipping_fee_other = Decimal('3.00')
        free_shipping_threshold = Decimal('0.00')
        pickup_enabled = False

    # Get delivery method and selected city from session
    delivery_method = request.session.get('delivery_method', 'pickup')
    selected_city = request.session.get('shipping_city', 'amman')

    # Auto-select first branch if pickup and no branch chosen
    if delivery_method == 'pickup' and not request.session.get('pickup_branch_id'):
        try:
            from core.models import Branch
            first_branch = Branch.objects.filter(is_active=True).first()
            if first_branch:
                request.session['pickup_branch_id'] = first_branch.id
                request.session.modified = True
        except Exception:
            pass

    # Calculate shipping
    if delivery_method == 'pickup':
        cart_shipping = Decimal('0.00')
    elif has_physical and cart_subtotal > 0 and shipping_enabled:
        # Check free shipping threshold
        if free_shipping_threshold > 0 and cart_subtotal >= free_shipping_threshold:
            cart_shipping = Decimal('0.00')
        else:
            # Apply shipping fee based on city
            if selected_city == 'amman':
                cart_shipping = shipping_fee_amman
            else:
                cart_shipping = shipping_fee_other

    # Apply coupon discount if exists
    coupon_code = request.session.get('coupon_code')
    coupon_discount_id = request.session.get('coupon_discount_id')
    applied_coupon = None
    coupon_discount = Decimal('0.00')
    eligible_items_count = 0
    max_discount_applied = False
    original_coupon_discount = Decimal('0.00')

    if coupon_code and coupon_discount_id and cart_subtotal > 0:
        try:
            now = timezone.now()
            # Get the coupon discount
            discount = ProductDiscount.objects.filter(
                id=coupon_discount_id,
                code__iexact=coupon_code,
                is_active=True,
                requires_coupon_code=True,
                start_date__lte=now
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now)
            ).first()

            if discount:
                applied_coupon = discount

                # Check minimum purchase amount (applies to ALL application types)
                meets_min_purchase = True
                if discount.min_purchase_amount:
                    if cart_original_subtotal < discount.min_purchase_amount:
                        meets_min_purchase = False

                # Calculate discount per eligible item
                for item in cart_items:
                    product = item['product']
                    item_quantity = item['quantity']

                    # Check if product is eligible AND meets minimum quantity requirement
                    meets_min_quantity = True
                    if discount.min_quantity and item_quantity < discount.min_quantity:
                        meets_min_quantity = False

                    if discount.applies_to_product(product) and meets_min_quantity and meets_min_purchase:
                        # This item is eligible for the coupon discount
                        item_price = item['price']

                        # Calculate discount for this item
                        # Use apply_max_cap=False so max_discount_amount is applied to total, not per item
                        item_discount = discount.calculate_discount_amount(item_price, item_quantity, apply_max_cap=False)
                        item_total_discount = item_discount * item_quantity

                        # Store discount info in cart item
                        item['coupon_eligible'] = True
                        item['coupon_discount'] = item_total_discount
                        item['price_after_coupon'] = item_price - item_discount
                        item['subtotal_after_coupon'] = item['subtotal'] - item_total_discount

                        coupon_discount += item_total_discount
                        eligible_items_count += 1
                    else:
                        # This item is NOT eligible for the coupon (product doesn't match or min quantity/purchase not met)
                        item['coupon_eligible'] = False
                        item['coupon_discount'] = Decimal('0.00')
                        item['price_after_coupon'] = item['price']
                        item['subtotal_after_coupon'] = item['subtotal']

                        # Store reason for ineligibility
                        if not meets_min_purchase:
                            item['coupon_ineligible_reason'] = f'الحد الأدنى للشراء {discount.min_purchase_amount} د.أ'
                        elif discount.applies_to_product(product) and not meets_min_quantity:
                            item['coupon_ineligible_reason'] = f'الحد الأدنى للكمية {discount.min_quantity}'

                # Apply max_discount_amount to total coupon discount (not per item)
                max_discount_applied = False
                original_coupon_discount = coupon_discount
                if discount.max_discount_amount and coupon_discount > discount.max_discount_amount:
                    max_discount_applied = True
                    # Calculate the ratio to proportionally reduce each item's discount
                    reduction_ratio = discount.max_discount_amount / coupon_discount

                    # Adjust each eligible item's discount proportionally
                    for item in cart_items:
                        if item.get('coupon_eligible') and item.get('coupon_discount', Decimal('0.00')) > 0:
                            original_item_discount = item['coupon_discount']
                            adjusted_discount = original_item_discount * reduction_ratio
                            item['coupon_discount'] = adjusted_discount
                            item['subtotal_after_coupon'] = item['subtotal'] - adjusted_discount
                            # Recalculate price_after_coupon per unit
                            if item['quantity'] > 0:
                                item['price_after_coupon'] = item['price'] - (adjusted_discount / item['quantity'])

                    # Cap the total coupon discount
                    coupon_discount = discount.max_discount_amount
            else:
                # Coupon is no longer valid, remove from session
                if 'coupon_code' in request.session:
                    del request.session['coupon_code']
                if 'coupon_discount_id' in request.session:
                    del request.session['coupon_discount_id']
                request.session.modified = True
                coupon_code = None

        except Exception as e:
            logger.error(f"Error applying coupon discount: {str(e)}")
            coupon_discount = Decimal('0.00')

    # Set cart_discount to coupon_discount for backward compatibility
    cart_discount = coupon_discount

    # Check if there are any active coupon-based discounts available
    has_coupon_discounts_available = False
    try:
        now = timezone.now()
        coupon_discounts_exist = ProductDiscount.objects.filter(
            is_active=True,
            requires_coupon_code=True,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).exists()
        has_coupon_discounts_available = coupon_discounts_exist
    except Exception as e:
        logger.error(f"Error checking coupon discounts availability: {str(e)}")

    # Calculate final total (with coupon discount applied)
    # Note: cart_subtotal already includes tax (prices in DB include tax),
    # so we don't add cart_tax here - it's just for display purposes
    cart_total = cart_subtotal + cart_shipping - cart_discount

    # Calculate subtotal after coupon (for display)
    cart_subtotal_after_coupon = cart_subtotal - coupon_discount

    # Recalculate tax after coupon discount (extract from tax-inclusive amount)
    cart_tax_after_coupon = (cart_subtotal_after_coupon - (cart_subtotal_after_coupon / (1 + tax_rate))) if cart_subtotal_after_coupon > 0 and not has_digital else Decimal('0.00')

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

        # Coupon discount info
        'applied_coupon': applied_coupon,
        'coupon_discount': coupon_discount,
        'eligible_items_count': eligible_items_count,
        'has_coupon_discounts_available': has_coupon_discounts_available,
        'max_discount_applied': max_discount_applied,
        'original_coupon_discount': original_coupon_discount,
        'cart_subtotal_after_coupon': cart_subtotal_after_coupon,
        'cart_tax_after_coupon': cart_tax_after_coupon,

        # Automatic (campaign) discount info
        'automatic_discount_savings': automatic_discount_savings,
        'cart_original_subtotal': cart_original_subtotal,
        'has_automatic_discount': automatic_discount_savings > 0,
        'automatic_discount_info': automatic_discount_info,

        # Shipping info
        'shipping_enabled': shipping_enabled,
        'shipping_fee_amman': shipping_fee_amman,
        'shipping_fee_other': shipping_fee_other,
        'selected_shipping_city': selected_city,
        'free_shipping_threshold': free_shipping_threshold,

        # Pickup info
        'pickup_enabled': pickup_enabled,
        'delivery_method': delivery_method,
        'pickup_branch_id': request.session.get('pickup_branch_id'),

        # Messages for UI
        'cart_messages': {
            'empty': 'سلة التسوق فارغة',
            'free_shipping': f'احصل على شحن مجاني عند الشراء بقيمة {free_shipping_threshold} د.أ أو أكثر' if has_physical and free_shipping_threshold > 0 else None,
            'free_shipping_qualified': 'تهانينا! لقد حصلت على شحن مجاني' if has_physical and cart_summary[
                'has_free_shipping'] and free_shipping_threshold > 0 else None,
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