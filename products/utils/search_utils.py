# products/utils/search_utils.py

from django.db.models import Q
from django.utils.translation import get_language
import re


def clean_search_query(query):
    """
    تنظيف كلمة البحث - إزالة الرموز الخاصة والمسافات الزائدة
    Clean search query - remove special characters and extra spaces
    """
    if not query:
        return ""

    # إزالة الرموز الخاصة
    query = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', query)

    # إزالة المسافات الزائدة
    query = ' '.join(query.split())

    return query.strip()


def get_search_terms(query):
    """
    تقسيم كلمة البحث إلى مصطلحات منفصلة
    Split search query into individual terms
    """
    query = clean_search_query(query)
    if not query:
        return []

    # تقسيم حسب المسافات
    terms = query.split()

    # إزالة المصطلحات القصيرة جداً
    terms = [term for term in terms if len(term) > 1]

    return terms


def build_product_search_query(terms):
    """
    بناء استعلام البحث للمنتجات
    Build search query for products
    """
    if not terms:
        return Q()

    search_query = Q()

    for term in terms:
        term_query = Q()

        # البحث في اسم المنتج
        term_query |= Q(name__icontains=term)
        term_query |= Q(name_en__icontains=term)

        # البحث في الوصف
        term_query |= Q(description__icontains=term)
        term_query |= Q(description_en__icontains=term)

        # البحث في الوصف القصير
        term_query |= Q(short_description__icontains=term)
        term_query |= Q(short_description_en__icontains=term)

        # البحث في SKU
        term_query |= Q(sku__icontains=term)

        # البحث في العلامة التجارية
        term_query |= Q(brand__name__icontains=term)
        term_query |= Q(brand__name_en__icontains=term)

        # البحث في الفئة
        term_query |= Q(category__name__icontains=term)
        term_query |= Q(category__name_en__icontains=term)

        # البحث في الوسوم
        term_query |= Q(tags__name__icontains=term)
        term_query |= Q(tags__name_en__icontains=term)

        # دمج المصطلحات مع AND
        search_query &= term_query

    return search_query


def get_search_suggestions_query(query, limit=10):
    """
    الحصول على اقتراحات البحث
    Get search suggestions
    """
    from ..models import Product, Category, Brand

    suggestions = []

    if len(query) < 2:
        return suggestions

    # اقتراحات المنتجات
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(name_en__icontains=query),
        is_active=True,
        status='published'
    ).select_related('category', 'brand')[:5]

    for product in products:
        suggestions.append({
            'type': 'product',
            'title': product.name,
            'url': product.get_absolute_url(),
            'image': product.main_image.url if product.main_image else '',
            'price': str(product.current_price),
        })

    # اقتراحات الفئات
    categories = Category.objects.filter(
        Q(name__icontains=query) | Q(name_en__icontains=query),
        is_active=True
    )[:3]

    for category in categories:
        suggestions.append({
            'type': 'category',
            'title': category.name,
            'url': category.get_absolute_url(),
            'count': category.products.filter(
                is_active=True,
                status='published'
            ).count(),
        })

    # اقتراحات العلامات التجارية
    brands = Brand.objects.filter(
        Q(name__icontains=query) | Q(name_en__icontains=query),
        is_active=True
    )[:2]

    for brand in brands:
        brand_url = '#'  # يمكن تحديث هذا لاحقاً
        if hasattr(brand, 'get_absolute_url'):
            brand_url = brand.get_absolute_url()

        suggestions.append({
            'type': 'brand',
            'title': brand.name,
            'url': brand_url,
            'count': brand.products.filter(
                is_active=True,
                status='published'
            ).count(),
        })

    return suggestions[:limit]


def get_popular_searches():
    """
    الحصول على عمليات البحث الشائعة
    Get popular searches
    """
    # يمكن تحسين هذا لاحقاً بحفظ إحصائيات البحث
    return [
        'لابتوب',
        'هاتف ذكي',
        'ساعة ذكية',
        'سماعات',
        'تابلت',
        'كاميرا',
        'العاب',
        'اكسسوارات',
    ]


def log_search_query(query, user=None, results_count=0):
    """
    تسجيل عملية البحث للإحصائيات
    Log search query for analytics
    """
    # يمكن إضافة نموذج SearchLog لحفظ الإحصائيات
    import logging

    logger = logging.getLogger('search')
    logger.info(f"Search: '{query}' | User: {user} | Results: {results_count}")


def get_related_searches(query):
    """
    الحصول على عمليات بحث ذات صلة
    Get related searches
    """
    # منطق بسيط لاقتراح عمليات بحث ذات صلة
    related = []

    # إضافة كلمات مفاتيح ذات صلة
    if 'لابتوب' in query.lower():
        related.extend(['لابتوب gaming', 'لابتوب dell', 'لابتوب hp'])
    elif 'هاتف' in query.lower():
        related.extend(['هاتف samsung', 'هاتف iphone', 'هاتف xiaomi'])
    elif 'ساعة' in query.lower():
        related.extend(['ساعة apple', 'ساعة samsung', 'ساعة رياضية'])

    return related[:5]