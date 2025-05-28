from django import template

register = template.Library()


@register.filter
def hex_to_rgb(hex_color):
    """تحويل لون الهيكس إلى قيم RGB"""
    # إزالة # إذا كانت موجودة
    hex_color = hex_color.lstrip('#')

    # التحويل إلى RGB
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"