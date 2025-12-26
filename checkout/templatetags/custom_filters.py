from django import template
register = template.Library()

@register.filter
def without_tax(value):
    """
    Remove 16% tax from a price.
    Formula: price - (price × 0.16)
    Example: 55 - (55 × 0.16) = 55 - 8.8 = 46.20
    """
    try:
        price = float(value)
        tax = price * 0.16
        return price - tax
    except (ValueError, ZeroDivisionError):
        return 0