import re
import hashlib
from django.db.models import Q
from django.core.cache import cache

STOP_WORDS = {
    'what', 'which', 'where', 'when', 'how', 'who', 'is', 'are', 'was', 'were',
    'do', 'does', 'did', 'have', 'has', 'had', 'the', 'a', 'an', 'and', 'or',
    'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'can',
    'could', 'would', 'should', 'will', 'shall', 'may', 'might', 'your', 'you',
    'i', 'me', 'my', 'we', 'our', 'they', 'them', 'their', 'it', 'its',
    'this', 'that', 'these', 'those', 'any', 'some', 'all', 'about', 'tell',
    'show', 'give', 'want', 'need', 'looking', 'find', 'search', 'get', 'best',
    'good', 'new', 'latest', 'please', 'thanks', 'thank',
    'هل', 'ما', 'من', 'في', 'على', 'إلى', 'عن', 'هذا', 'هذه', 'ذلك',
    'أريد', 'أبي', 'ابي', 'لي', 'لك', 'هي', 'هو', 'كم', 'أي', 'لديكم',
    'عندكم', 'يوجد', 'أفضل', 'أحسن', 'جديد', 'أخبرني', 'وش', 'شو',
}


def _extract_keywords(query):
    words = re.findall(r'[\w؀-ۿ]+', query.lower())
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    expanded = []
    for kw in keywords:
        expanded.append(kw)
        if kw.endswith('s') and len(kw) > 3:
            expanded.append(kw[:-1])
        if kw.endswith('es') and len(kw) > 4:
            expanded.append(kw[:-2])
        if kw.endswith('ing') and len(kw) > 5:
            expanded.append(kw[:-3])
    return expanded if expanded else words[:3]


def search_products(query, limit=5, chatbot_settings=None):
    settings_key = ''
    if chatbot_settings:
        settings_key = f'_{chatbot_settings.product_status_filter}_{chatbot_settings.hide_products_without_price}_{chatbot_settings.hide_out_of_stock}_{chatbot_settings.product_sort_order}_{chatbot_settings.show_price_in_response}'
    cache_key = f'chatbot_products_{hashlib.md5(query.lower().encode()).hexdigest()}_{limit}{settings_key}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    base = _build_product_base_qs(chatbot_settings)

    products = base.filter(
        Q(name__icontains=query) |
        Q(name_en__icontains=query) |
        Q(short_description__icontains=query) |
        Q(sku__icontains=query) |
        Q(search_keywords__icontains=query)
    ).select_related('category', 'brand').prefetch_related('images')[:limit]

    results = list(products)
    if len(results) < limit:
        keywords = _extract_keywords(query)
        seen_ids = {p.id for p in results}
        for kw in keywords:
            if len(results) >= limit:
                break
            kw_products = base.filter(
                Q(name__icontains=kw) |
                Q(name_en__icontains=kw) |
                Q(short_description__icontains=kw) |
                Q(search_keywords__icontains=kw)
            ).exclude(id__in=seen_ids).select_related('category', 'brand').prefetch_related('images')[:limit - len(results)]
            for p in kw_products:
                if p.id not in seen_ids:
                    results.append(p)
                    seen_ids.add(p.id)

    if not results:
        results = list(base.select_related('category', 'brand').prefetch_related('images')[:limit])

    show_price = True
    if chatbot_settings:
        show_price = chatbot_settings.show_price_in_response
    result = [_serialize_product(p, show_price=show_price) for p in results[:limit]]
    cache.set(cache_key, result, 300)
    return result


def _build_product_base_qs(chatbot_settings=None):
    from products.models import Product
    base = Product.objects.filter(is_active=True)

    status_filter = 'published_only'
    hide_no_price = True
    hide_oos = False
    sort_order = 'newest'

    if chatbot_settings:
        status_filter = chatbot_settings.product_status_filter
        hide_no_price = chatbot_settings.hide_products_without_price
        hide_oos = chatbot_settings.hide_out_of_stock
        sort_order = chatbot_settings.product_sort_order

    if status_filter == 'published_only':
        base = base.filter(status='published')
    elif status_filter == 'published_and_draft':
        base = base.filter(status__in=['published', 'draft'])

    if hide_no_price:
        base = base.exclude(base_price__isnull=True).exclude(base_price=0)

    if hide_oos:
        base = base.filter(
            Q(track_inventory=False) | Q(stock_quantity__gt=0)
        )

    sort_map = {
        'newest': '-created_at',
        'price_low': 'base_price',
        'price_high': '-base_price',
        'name': 'name',
    }
    base = base.order_by(sort_map.get(sort_order, '-created_at'))

    return base


def search_blog(query, limit=3):
    try:
        from blog.models import BlogPost
        posts = BlogPost.objects.filter(
            status='published'
        ).filter(
            Q(title__icontains=query) |
            Q(title_en__icontains=query) |
            Q(excerpt__icontains=query)
        )[:limit]
        return [_serialize_blog(p) for p in posts]
    except Exception:
        return []


def search_categories(query, limit=5):
    from products.models import Category
    cats = Category.objects.filter(
        is_active=True
    ).filter(
        Q(name__icontains=query) |
        Q(name_en__icontains=query)
    )[:limit]
    return [{'id': c.id, 'name': c.name, 'name_en': c.name_en or c.name, 'slug': c.slug} for c in cats]


def get_categories_tree(language='ar'):
    from products.models import Category
    from django.core.cache import cache

    cache_key = f'chatbot_categories_tree_{language}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    categories = Category.objects.filter(is_active=True, level=0).order_by('tree_id', 'lft')
    lines = []
    for cat in categories:
        name = cat.name if language == 'ar' else (cat.name_en or cat.name)
        indent = '  ' * cat.level
        lines.append(f"{indent}- {name}")

    result = '\n'.join(lines) if lines else ''
    cache.set(cache_key, result, 1800)
    return result


def get_products_for_comparison(product_ids, chatbot_settings=None):
    from products.models import Product
    products = Product.objects.filter(
        id__in=product_ids, is_active=True
    ).select_related('category', 'brand').prefetch_related('images')[:4]
    show_price = True
    if chatbot_settings:
        show_price = chatbot_settings.show_price_in_response
    return [_serialize_product(p, full=True, show_price=show_price) for p in products]


def match_custom_qa(query, language='ar'):
    from chatbot.models import CustomQA
    query_lower = query.lower()
    qas = CustomQA.objects.filter(is_active=True).order_by('-priority')
    for qa in qas:
        q_field = qa.question_ar if language == 'ar' else (qa.question_en or qa.question_ar)
        if q_field.lower() in query_lower or query_lower in q_field.lower():
            return {
                'question': q_field,
                'answer': qa.answer_ar if language == 'ar' else (qa.answer_en or qa.answer_ar),
            }
        if qa.keywords:
            keywords = [k.strip().lower() for k in qa.keywords.split(',') if k.strip()]
            for kw in keywords:
                if kw in query_lower:
                    return {
                        'question': q_field,
                        'answer': qa.answer_ar if language == 'ar' else (qa.answer_en or qa.answer_ar),
                    }
    return None


def get_suggested_questions(language='ar'):
    from chatbot.models import SuggestedQuestion
    suggestions = SuggestedQuestion.objects.filter(is_active=True)[:6]
    result = []
    for s in suggestions:
        result.append({
            'text': s.text_ar if language == 'ar' else (s.text_en or s.text_ar),
            'icon': s.icon,
        })
    return result


def _serialize_product(product, full=False, show_price=True):
    has_discount = bool(product.compare_price and product.base_price and product.compare_price > product.base_price)
    discount_pct = 0
    if has_discount:
        discount_pct = int(round((float(product.compare_price) - float(product.base_price)) / float(product.compare_price) * 100))

    data = {
        'id': product.id,
        'name': product.name,
        'name_en': product.name_en or product.name,
        'price': str(product.base_price) if (product.base_price and show_price) else '',
        'compare_price': str(product.compare_price) if (product.compare_price and show_price) else '',
        'has_discount': has_discount if show_price else False,
        'discount_percentage': discount_pct if show_price else 0,
        'url': f'/products/{product.slug}/' if product.slug else f'/products/{product.id}/',
        'in_stock': product.stock_quantity > 0 if product.track_inventory else True,
        'brand': product.brand.name if product.brand else '',
        'category': product.category.name if product.category else '',
        'sku': product.sku or '',
        'short_description': product.short_description or '',
        'show_price': show_price,
    }
    images = product.images.all()[:1]
    if images:
        try:
            data['image_url'] = images[0].image.url
        except Exception:
            data['image_url'] = ''
    else:
        data['image_url'] = ''

    if full:
        data['specifications'] = product.specifications if product.specifications else {}
        data['features'] = product.features if product.features else ''

    return data


def _serialize_blog(post):
    return {
        'id': post.id,
        'title': post.title,
        'title_en': post.title_en or post.title,
        'excerpt': post.excerpt or '',
        'url': f'/blog/{post.slug}/' if post.slug else f'/blog/{post.id}/',
    }
