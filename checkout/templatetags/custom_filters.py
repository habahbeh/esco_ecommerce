from django import template
register = template.Library()

@register.filter
def without_tax(value):
    try:
        return float(value) / 1.16
    except (ValueError, ZeroDivisionError):
        return 0