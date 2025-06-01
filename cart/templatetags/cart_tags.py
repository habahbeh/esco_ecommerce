# cart/templatetags/cart_tags.py
"""
Custom template tags for cart functionality
"""

from django import template
from django.utils.safestring import mark_safe
from decimal import Decimal
import json

register = template.Library()


@register.simple_tag(takes_context=True)
def cart_item_count(context):
    """
    Get cart items count
    Usage: {% cart_item_count %}
    """
    return context.get('cart_count', 0)


@register.simple_tag(takes_context=True)
def cart_total_price(context):
    """
    Get cart total price formatted
    Usage: {% cart_total_price %}
    """
    total = context.get('cart_total', Decimal('0.00'))
    return f"{total:.2f} د.أ"


@register.simple_tag(takes_context=True)
def product_in_cart(context, product):
    """
    Check if product is in cart and return quantity
    Usage: {% product_in_cart product as in_cart %}
    """
    cart_items = context.get('cart_items', [])
    for item in cart_items:
        if item['product'].id == product.id:
            return item['quantity']
    return 0


@register.inclusion_tag('cart/includes/cart_icon.html', takes_context=True)
def cart_icon(context):
    """
    Render cart icon with count
    Usage: {% cart_icon %}
    """
    return {
        'cart_count': context.get('cart_count', 0),
        'cart_total': context.get('cart_total', Decimal('0.00')),
    }


@register.inclusion_tag('cart/includes/mini_cart.html', takes_context=True)
def mini_cart(context, max_items=3):
    """
    Render mini cart widget
    Usage: {% mini_cart %} or {% mini_cart max_items=5 %}
    """
    cart_items = context.get('cart_items', [])[:max_items]
    return {
        'cart_items': cart_items,
        'cart_count': context.get('cart_count', 0),
        'cart_total': context.get('cart_total', Decimal('0.00')),
        'cart_is_empty': context.get('cart_is_empty', True),
        'show_more': len(context.get('cart_items', [])) > max_items,
    }


@register.filter
def multiply(value, arg):
    """
    Multiply filter
    Usage: {{ price|multiply:quantity }}
    """
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except:
        return 0


@register.filter
def percentage(value, total):
    """
    Calculate percentage
    Usage: {{ cart_subtotal|percentage:free_shipping_threshold }}
    """
    try:
        if total == 0:
            return 0
        return int((Decimal(str(value)) / Decimal(str(total))) * 100)
    except:
        return 0


@register.simple_tag(takes_context=True)
def cart_progress_to_free_shipping(context):
    """
    Calculate progress to free shipping
    Usage: {% cart_progress_to_free_shipping as progress %}
    """
    if not context.get('cart_has_physical', False):
        return 100

    summary = context.get('cart_summary', {})
    if summary.get('has_free_shipping', False):
        return 100

    subtotal = context.get('cart_subtotal', Decimal('0.00'))
    threshold = summary.get('free_shipping_threshold', Decimal('50.00'))

    if threshold > 0:
        progress = int((subtotal / threshold) * 100)
        return min(progress, 100)
    return 0


@register.simple_tag
def cart_item_savings(original_price, current_price, quantity=1):
    """
    Calculate savings for cart item
    Usage: {% cart_item_savings item.original_price item.price item.quantity %}
    """
    try:
        original = Decimal(str(original_price))
        current = Decimal(str(current_price))
        qty = int(quantity)

        if original > current:
            savings = (original - current) * qty
            return f"{savings:.2f}"
        return "0.00"
    except:
        return "0.00"


@register.inclusion_tag('cart/includes/add_to_cart_button.html')
def add_to_cart_button(product, quantity=1, variant=None, css_class="btn btn-primary", show_text=True):
    """
    Render add to cart button
    Usage: {% add_to_cart_button product %}
    """
    return {
        'product': product,
        'quantity': quantity,
        'variant': variant,
        'css_class': css_class,
        'show_text': show_text,
        'in_stock': product.in_stock if hasattr(product, 'in_stock') else True,
    }


@register.simple_tag(takes_context=True)
def cart_json(context):
    """
    Get cart data as JSON for JavaScript
    Usage: {% cart_json as cart_data %}
    """
    cart_data = {
        'count': context.get('cart_count', 0),
        'total': float(context.get('cart_total', 0)),
        'subtotal': float(context.get('cart_subtotal', 0)),
        'items': []
    }

    for item in context.get('cart_items', []):
        cart_data['items'].append({
            'id': item['id'],
            'product_id': item['product'].id,
            'name': item['product'].name,
            'quantity': item['quantity'],
            'price': float(item['price']),
            'subtotal': float(item['subtotal']),
        })

    return mark_safe(json.dumps(cart_data))


@register.simple_tag
def cart_item_subtotal(price, quantity):
    """
    Calculate subtotal for display
    Usage: {{ item.price|cart_item_subtotal:item.quantity }}
    """
    try:
        return Decimal(str(price)) * int(quantity)
    except:
        return Decimal('0.00')


@register.filter
def cart_format_price(value):
    """
    Format price for display
    Usage: {{ price|cart_format_price }}
    """
    try:
        price = Decimal(str(value))
        return f"{price:.2f}"
    except:
        return "0.00"

# Template includes directory structure:
# cart/templatetags/
#   __init__.py
#   cart_tags.py
# cart/templates/cart/includes/
#   cart_icon.html
#   mini_cart.html
#   add_to_cart_button.html