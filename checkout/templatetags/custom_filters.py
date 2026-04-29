from django import template
register = template.Library()

@register.filter
def without_tax(value):
    """
    Extract pre-tax price from a tax-inclusive price.
    Prices in DB include 16% tax, so: price_before_tax = price / 1.16
    Example: 1.25 / 1.16 = 1.0776
    """
    try:
        price = float(value)
        return round(price / 1.16, 4)
    except (ValueError, ZeroDivisionError):
        return 0