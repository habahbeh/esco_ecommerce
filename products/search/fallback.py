import logging
import os
from django.conf import settings
from django.db.models import Q, Case, When, IntegerField, Value

logger = logging.getLogger(__name__)


class DjangoORMSearcher:

    def search(self, query, filters=None, sort=None, page=1, per_page=20, queryset=None):
        from products.models import Product

        if queryset is None:
            queryset = Product.objects.filter(
                is_active=True, status='published'
            ).select_related('category', 'brand').prefetch_related('images', 'tags', 'variants')

        terms = [t.strip() for t in query.split() if len(t.strip()) >= 2]
        if not terms:
            return {'hits': [], 'total': 0, 'query': query, 'processing_time_ms': 0}

        q_filter = Q()
        for term in terms:
            q_filter &= (
                Q(name__icontains=term) |
                Q(name_en__icontains=term) |
                Q(sku__icontains=term) |
                Q(barcode__icontains=term) |
                Q(variants__sku__icontains=term) |
                Q(variants__name__icontains=term) |
                Q(short_description__icontains=term) |
                Q(description__icontains=term) |
                Q(tags__name__icontains=term) |
                Q(category__name__icontains=term) |
                Q(category__name_en__icontains=term) |
                Q(brand__name__icontains=term) |
                Q(brand__name_en__icontains=term)
            )

        queryset = queryset.filter(q_filter).distinct()

        # Relevance ordering
        relevance_cases = []
        for i, term in enumerate(terms):
            relevance_cases.append(When(sku__iexact=term, then=Value(100 - i)))
            relevance_cases.append(When(barcode__iexact=term, then=Value(95 - i)))
            relevance_cases.append(When(name__iexact=term, then=Value(90 - i)))
            relevance_cases.append(When(name__icontains=term, then=Value(50 - i)))
            relevance_cases.append(When(sku__icontains=term, then=Value(70 - i)))

        if sort and sort != ['relevance']:
            sort_map = {
                'base_price:asc': 'base_price',
                'base_price:desc': '-base_price',
                'sales_count:desc': '-sales_count',
                'created_at:desc': '-created_at',
            }
            order_fields = [sort_map.get(s, '-created_at') for s in sort]
            queryset = queryset.order_by(*order_fields)
        else:
            queryset = queryset.annotate(
                relevance=Case(*relevance_cases, default=Value(0), output_field=IntegerField())
            ).order_by('-relevance', '-created_at')

        total = queryset.count()
        offset = (page - 1) * per_page
        products = queryset[offset:offset + per_page]

        default_image = settings.STATIC_URL + 'images/no-image.png'
        hits = []
        for p in products:
            image_url = default_image
            try:
                all_images = list(p.images.all())
                if all_images:
                    primary = next((img for img in all_images if img.is_primary), None)
                    img = primary or all_images[0]
                    if img and img.image and os.path.isfile(img.image.path):
                        image_url = img.image.url
            except Exception:
                pass

            hits.append({
                'id': p.id,
                'name': p.name or '',
                'name_en': p.name_en or '',
                'sku': p.sku or '',
                'barcode': p.barcode or '',
                'base_price': float(p.base_price or 0),
                'image_url': image_url,
                'category_name': p.category.name if p.category else '',
                'category_name_en': p.category.name_en if p.category and hasattr(p.category, 'name_en') else '',
                'brand_name': p.brand.name if p.brand else '',
                'brand_name_en': p.brand.name_en if p.brand and hasattr(p.brand, 'name_en') else '',
                'stock_status': p.stock_status or 'in_stock',
                'is_active': p.is_active,
                'status': p.status,
            })

        return {'hits': hits, 'total': total, 'query': query, 'processing_time_ms': 0}

    def suggest(self, query, limit=5, storefront_only=True):
        from products.models import Product

        base_qs = Product.objects.select_related('category', 'brand')
        if storefront_only:
            base_qs = base_qs.filter(is_active=True, status='published')

        products = base_qs.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query) |
            Q(sku__icontains=query) | Q(barcode__icontains=query) |
            Q(variants__sku__icontains=query) | Q(variants__name__icontains=query)
        ).distinct()[:limit]

        default_image = settings.STATIC_URL + 'images/no-image.png'
        hits = []
        for p in products:
            image_url = default_image
            try:
                all_images = list(p.images.all())
                if all_images:
                    primary = next((img for img in all_images if img.is_primary), None)
                    img = primary or all_images[0]
                    if img and img.image and os.path.isfile(img.image.path):
                        image_url = img.image.url
            except Exception:
                pass

            hits.append({
                'id': p.id,
                'name': p.name or '',
                'name_en': p.name_en or '',
                'sku': p.sku or '',
                'base_price': float(p.base_price or 0),
                'image_url': image_url,
                'category_name': p.category.name if p.category else '',
                'category_name_en': p.category.name_en if p.category and hasattr(p.category, 'name_en') else '',
                'brand_name': p.brand.name if p.brand else '',
                'brand_name_en': p.brand.name_en if p.brand and hasattr(p.brand, 'name_en') else '',
            })

        return hits

    def did_you_mean(self, query, storefront_only=True):
        from products.models import Product

        base_qs = Product.objects.all()
        if storefront_only:
            base_qs = base_qs.filter(is_active=True, status='published')

        # Check if current query has results
        has_results = base_qs.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query) |
            Q(sku__icontains=query) | Q(barcode__icontains=query) |
            Q(variants__sku__icontains=query) | Q(variants__name__icontains=query)
        ).exists()

        if has_results:
            return None

        # Try first 3 chars
        partial = query[:3] if len(query) > 3 else query
        alternatives = base_qs.filter(
            Q(name__icontains=partial) | Q(name_en__icontains=partial)
        ).values_list('name', flat=True)[:3]

        return list(alternatives) if alternatives else None
