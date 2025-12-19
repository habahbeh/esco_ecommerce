from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import floatformat, date as date_filter
from django.utils import timezone
import json
import datetime
import re

register = template.Library()


@register.filter
def abs(value):
    """
    إرجاع القيمة المطلقة للرقم
    مثال: {{ number|abs }}
    """
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value


@register.filter
def currency(value, currency_symbol='د.ا'):
    """
    تنسيق المبالغ مع رمز العملة
    مثال: {{ product.price|currency:'$' }}
    """
    if value is None:
        return ''
    try:
        value = float(value)
        formatted_value = floatformat(value, 2)
        formatted_with_commas = intcomma(formatted_value)
        return f"{formatted_with_commas} {currency_symbol}"
    except (ValueError, TypeError):
        return value


@register.filter
def percentage(value, decimal_places=1):
    """
    تنسيق النسب المئوية
    مثال: {{ percentage_value|percentage:2 }}
    """
    if value is None:
        return ''
    try:
        value = float(value)
        return f"{floatformat(value, decimal_places)}%"
    except (ValueError, TypeError):
        return value


@register.filter
def change_indicator(value, include_value=True):
    """
    عرض مؤشر التغير (إيجابي/سلبي) مع سهم وتنسيق اللون
    مثال: {{ change_value|change_indicator }}
    """
    if value is None:
        return ''
    try:
        value = float(value)
        if value > 0:
            indicator = '<span class="text-success"><i class="fas fa-arrow-up"></i>'
            if include_value:
                indicator += f" {floatformat(abs(value), 1)}%"
            indicator += '</span>'
        elif value < 0:
            indicator = '<span class="text-danger"><i class="fas fa-arrow-down"></i>'
            if include_value:
                indicator += f" {floatformat(abs(value), 1)}%"
            indicator += '</span>'
        else:
            indicator = '<span class="text-muted"><i class="fas fa-minus"></i>'
            if include_value:
                indicator += ' 0%'
            indicator += '</span>'
        return mark_safe(indicator)
    except (ValueError, TypeError):
        return value


# @register.filter
# def status_badge(status, status_dict=None):
#     """
#     عرض شارة حالة الطلب أو المنتج بتنسيق Bootstrap
#     مثال: {{ order.status|status_badge }}
#     """
#     default_status_classes = {
#         'pending': 'secondary',
#         'processing': 'info',
#         'on_hold': 'warning',
#         'completed': 'success',
#         'shipped': 'primary',
#         'delivered': 'success',
#         'cancelled': 'danger',
#         'refunded': 'dark',
#         'failed': 'danger',
#         'draft': 'secondary',
#         'published': 'success',
#         'out_of_stock': 'danger',
#         'in_stock': 'success',
#         'low_stock': 'warning',
#     }
#
#     # استخدام قاموس مخصص إذا تم تمريره
#     status_classes = status_dict or default_status_classes
#
#     # تحديد فئة الشارة
#     status_class = status_classes.get(status, 'secondary')
#
#     # تنسيق النص (تحويل under_score إلى Title Case)
#     if isinstance(status, str):
#         status_text = status.replace('_', ' ').title()
#     else:
#         status_text = str(status)
#
#     return mark_safe(f'<span class="badge bg-{status_class}">{status_text}</span>')


@register.filter
def status_badge(status):
    """
    إرجاع فئة Bootstrap للون حسب حالة الطلب
    مثال: {{ order.status|status_badge }}
    """
    status_classes = {
        'pending': 'warning',
        'confirmed': 'info',
        'closed': 'success',
        'cancelled': 'danger',
        'processing': 'info',
        'on_hold': 'warning',
        'completed': 'success',
        'shipped': 'primary',
        'delivered': 'success',
        'refunded': 'dark',
        'failed': 'danger',
        'draft': 'secondary',
        'published': 'success',
        'out_of_stock': 'danger',
        'in_stock': 'success',
        'low_stock': 'warning',
        # حالات الدفع
        'paid': 'success',
    }

    # إرجاع فئة اللون فقط
    return status_classes.get(status, 'secondary')


@register.filter
def status_badge_html(status, text=None):
    """
    عرض شارة حالة الطلب أو المنتج بتنسيق Bootstrap كاملة
    مثال: {{ order.status|status_badge_html }}
    """
    status_class = status_badge(status)

    # تنسيق النص (تحويل under_score إلى Title Case)
    if text is None:
        if isinstance(status, str):
            text = status.replace('_', ' ').title()
        else:
            text = str(status)

    return mark_safe(f'<span class="badge bg-{status_class}">{text}</span>')

@register.filter
def pretty_json(value):
    """
    تنسيق بيانات JSON بشكل جميل
    مثال: {{ object.json_data|pretty_json }}
    """
    if not value:
        return ''
    try:
        if isinstance(value, str):
            parsed = json.loads(value)
        else:
            parsed = value
        return mark_safe(f'<pre class="json-data">{json.dumps(parsed, indent=4, ensure_ascii=False)}</pre>')
    except (ValueError, TypeError):
        return value


@register.filter
def get_dict_value(dictionary, key):
    """
    استخراج قيمة من قاموس باستخدام المفتاح
    مثال: {{ my_dict|get_dict_value:my_key }}
    """
    if not dictionary:
        return ''
    try:
        return dictionary.get(key, '')
    except (AttributeError, TypeError):
        return ''


@register.filter
def get_item(obj, key):
    """
    استخراج قيمة من كائن أو قاموس باستخدام المفتاح
    مثال: {{ object|get_item:'attribute_name' }}
    """
    if not obj:
        return ''
    try:
        # محاولة الوصول كقاموس
        return obj.get(key, '')
    except (AttributeError, TypeError):
        try:
            # محاولة الوصول كخاصية
            return getattr(obj, key, '')
        except (AttributeError, TypeError):
            try:
                # محاولة الوصول كعنصر قائمة
                return obj[key]
            except (IndexError, TypeError, KeyError):
                return ''


@register.filter
def format_date(value, format_string=None):
    """
    تنسيق التاريخ بالطريقة المناسبة
    مثال: {{ created_at|format_date:'Y-m-d' }}
    """
    if not value:
        return ''

    if format_string:
        return date_filter(value, format_string)

    # إذا كان التاريخ اليوم
    today = timezone.now().date()
    if hasattr(value, 'date') and value.date() == today:
        return _('اليوم، ') + date_filter(value, 'g:i a')

    # إذا كان التاريخ بالأمس
    yesterday = today - datetime.timedelta(days=1)
    if hasattr(value, 'date') and value.date() == yesterday:
        return _('الأمس، ') + date_filter(value, 'g:i a')

    # إذا كان التاريخ هذا العام
    if hasattr(value, 'year') and value.year == today.year:
        return date_filter(value, 'd M، g:i a')

    # التاريخ الكامل
    return date_filter(value, 'd M Y، g:i a')


@register.filter
def time_since(value):
    """
    عرض الوقت المنقضي منذ تاريخ معين
    مثال: {{ created_at|time_since }}
    """
    if not value:
        return ''

    now = timezone.now()
    if hasattr(value, 'tzinfo') and value.tzinfo is None:
        value = timezone.make_aware(value)

    diff = now - value
    seconds = diff.total_seconds()

    # تحديد الوحدة المناسبة
    if seconds < 60:
        return _('منذ قليل')
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return _('منذ %(minutes)d دقيقة') % {'minutes': minutes}
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return _('منذ %(hours)d ساعة') % {'hours': hours}
    elif seconds < 604800:
        days = int(seconds // 86400)
        return _('منذ %(days)d يوم') % {'days': days}
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return _('منذ %(weeks)d أسبوع') % {'weeks': weeks}
    elif seconds < 31536000:
        months = int(seconds // 2592000)
        return _('منذ %(months)d شهر') % {'months': months}
    else:
        years = int(seconds // 31536000)
        return _('منذ %(years)d سنة') % {'years': years}


@register.filter
def phone_format(value):
    """
    تنسيق رقم الهاتف بشكل مقروء
    مثال: {{ phone_number|phone_format }}
    """
    if not value:
        return ''

    value = str(value).strip()

    # إزالة أي رموز غير أرقام
    numbers_only = re.sub(r'\D', '', value)

    # إذا كان رقماً سعودياً
    if numbers_only.startswith('966') and len(numbers_only) >= 12:
        formatted = numbers_only[3:]
        return f"+966 {formatted[0:2]} {formatted[2:5]} {formatted[5:]}"

    # إذا كان يبدأ بـ 0
    if numbers_only.startswith('0') and len(numbers_only) >= 10:
        formatted = numbers_only[1:]
        return f"0{formatted[0:2]} {formatted[2:5]} {formatted[5:]}"

    # إرجاع القيمة كما هي إذا لم تطابق أي تنسيق
    return value


@register.filter
def truncate_chars(value, max_length=50):
    """
    اقتطاع النص الطويل وإضافة نقاط الحذف
    مثال: {{ long_text|truncate_chars:100 }}
    """
    if not value:
        return ''

    value = str(value)
    if len(value) <= max_length:
        return value

    return value[:max_length - 3] + '...'


@register.filter
def file_size_format(bytes_value):
    """
    تنسيق حجم الملف بالوحدة المناسبة
    مثال: {{ file.size|file_size_format }}
    """
    if not bytes_value:
        return '0 bytes'

    try:
        bytes_value = float(bytes_value)
        for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                if unit == 'bytes':
                    return f"{int(bytes_value)} {unit}"
                return f"{floatformat(bytes_value, 2)} {unit}"
            bytes_value /= 1024
    except (ValueError, TypeError):
        return bytes_value


@register.filter
def has_permission(user, permission_name):
    """
    التحقق من وجود صلاحية معينة للمستخدم
    مثال: {% if user|has_permission:'products.add_product' %}...{% endif %}
    """
    if not user or not permission_name:
        return False

    if user.is_superuser:
        return True

    return user.has_perm(permission_name)


@register.simple_tag
def get_verbose_name(model, field_name):
    """
    استخراج الاسم المعروض للحقل من النموذج
    مثال: {% get_verbose_name model 'field_name' %}
    """
    try:
        return model._meta.get_field(field_name).verbose_name
    except (AttributeError, FieldDoesNotExist):
        return field_name


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    تحويل معلمات URL مع الحفاظ على المعلمات الحالية
    مثال: <a href="?{% query_transform page=1 %}">الصفحة الأولى</a>
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()


@register.inclusion_tag('dashboard/components/status_pill.html')
def status_pill(status, text=None, tooltip=None):
    """
    عرض حالة بتنسيق دائري ملون
    مثال: {% status_pill 'active' 'نشط' 'المنتج متاح للشراء' %}
    """
    status_colors = {
        'active': 'success',
        'inactive': 'danger',
        'draft': 'secondary',
        'pending': 'warning',
        'completed': 'success',
        'processing': 'info',
        'cancelled': 'danger',
    }

    return {
        'status': status,
        'color': status_colors.get(status, 'secondary'),
        'text': text or status.replace('_', ' ').title(),
        'tooltip': tooltip,
    }


@register.inclusion_tag('dashboard/components/action_buttons.html')
def action_buttons(obj, edit_url=None, delete_url=None, view_url=None, can_edit=True, can_delete=True):
    """
    عرض أزرار الإجراءات (عرض، تعديل، حذف) لكائن
    مثال: {% action_buttons object edit_url='product_edit' delete_url='product_delete' %}
    """
    return {
        'object': obj,
        'edit_url': edit_url,
        'delete_url': delete_url,
        'view_url': view_url,
        'can_edit': can_edit,
        'can_delete': can_delete,
    }


@register.filter
def subtract(value, arg):
    """
    طرح قيمة من قيمة أخرى
    مثال: {{ product.current_price|subtract:product.cost }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def divide(value, arg):
    """
    قسمة قيمة على قيمة أخرى
    مثال: {{ product.current_price|divide:2 }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0  # إرجاع صفر في حالة الخطأ أو القسمة على صفر

@register.filter
def multiply(value, arg):
    """
    ضرب قيمة في قيمة أخرى
    مثال: {{ product.price|multiply:quantity }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0  # إرجاع صفر في حالة الخطأ


@register.filter
def dict_get(dictionary, key):
    """
    دالة للوصول الآمن إلى قيم القاموس، مع إرجاع قيمة فارغة إذا كان القاموس فارغًا أو المفتاح غير موجود
    مثال: {{ form_data|dict_get:'name' }}
    """
    if dictionary is None:
        return ''
    return dictionary.get(key, '')


@register.filter
def dict_get_default(dictionary, key_default):
    """
    دالة للوصول الآمن إلى قيم القاموس، مع إمكانية توفير قيمة افتراضية
    مثال: {{ form_data|dict_get_default:'name:القيمة الافتراضية' }}
    """
    if dictionary is None:
        return ''

    if ':' in key_default:
        key, default = key_default.split(':', 1)
    else:
        key, default = key_default, ''

    return dictionary.get(key, default)

# @register.filter
# def getattribute(form, attr_name):
#     """يسترجع حقل من النموذج عن طريق الاسم الديناميكي"""
#     attr_id = attr_name.split('_')[-1]
#     return form.get(f'{attr_name}{attr_id}', None)

@register.filter
def getattribute(form, attr_name):
    """يسترجع حقل من النموذج عن طريق الاسم الديناميكي"""
    try:
        # استخراج معرف الخاصية
        attr_id = attr_name.split('_')[-1]
        # استخدام الاسم الكامل للحقل
        field_name = f'attribute_{attr_id}'
        return form[field_name]
    except (KeyError, IndexError):
        return None

@register.filter
def get_field(form, field_name):
    """استرجاع حقل من النموذج بالاسم المباشر"""
    try:
        return form[field_name]
    except KeyError:
        return None


@register.filter
def get_item(dictionary, key):
    """استخراج قيمة من قاموس باستخدام مفتاح"""
    return dictionary.get(key, '')

@register.filter
def get(dictionary, key):
    return dictionary.get(key, key)