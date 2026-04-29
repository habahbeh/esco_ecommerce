from django import template
from core.models import Branch

register = template.Library()


@register.simple_tag
def get_active_branches():
    return Branch.objects.filter(is_active=True).order_by('sort_order')
