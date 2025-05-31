# File: products/views/base_views.py
"""
Base views and mixins for products app
Contains common functionality and base classes
"""

from typing import Optional, Dict, Any, List
from django.views.generic import ListView, DetailView
from django.db.models import Q, QuerySet, Prefetch
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext as _
from decimal import Decimal
import logging

from ..models import Product, Category, Brand, ProductImage, Tag

logger = logging.getLogger(__name__)


class CachedMixin:
    """Mixin for adding caching functionality"""
    cache_timeout = getattr(settings, 'CACHE_TIMEOUT', 300)  # 5 minutes default

    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key for the view"""
        return f"{self.__class__.__name__}:{':'.join(map(str, args))}:{hash(frozenset(kwargs.items()))}"

    def get_cached_data(self, key: str, default=None):
        """Get data from cache"""
        return cache.get(key, default)

    def set_cached_data(self, key: str, data, timeout=None):
        """Set data in cache"""
        if timeout is None:
            timeout = self.cache_timeout
        cache.set(key, data, timeout)


class OptimizedQueryMixin:
    """Mixin for optimizing database queries"""

    def get_optimized_product_queryset(self) -> QuerySet:
        """Get optimized product queryset with proper select_related and prefetch_related"""
        return Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related(
            'category',
            'brand',
            'created_by'
        ).prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.filter(is_primary=True).order_by('order')
            ),
            'tags',
            Prefetch(
                'reviews',
                queryset=self.get_approved_reviews_queryset()
            )
        )

    def get_approved_reviews_queryset(self) -> QuerySet:
        """Get approved reviews queryset"""
        from ..models import ProductReview
        return ProductReview.objects.filter(is_approved=True).select_related('user')


class FilterMixin:
    """Mixin for handling common filtering logic"""

    def get_filters_from_request(self) -> Dict[str, Any]:
        """Extract and validate filters from request"""
        filters = {}

        # Brand filter
        brands = self.request.GET.getlist('brand')
        if brands:
            filters['brands'] = [int(b) for b in brands if b.isdigit()]

        # Price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if min_price and self._is_valid_decimal(min_price):
            filters['min_price'] = Decimal(min_price)
        if max_price and self._is_valid_decimal(max_price):
            filters['max_price'] = Decimal(max_price)

        # Boolean filters
        filters['is_new'] = self.request.GET.get('is_new') == '1'
        filters['is_featured'] = self.request.GET.get('is_featured') == '1'
        filters['on_sale'] = self.request.GET.get('on_sale') == '1'
        filters['in_stock'] = self.request.GET.get('in_stock') == '1'

        # Tags
        tags = self.request.GET.getlist('tag')
        if tags:
            filters['tags'] = [int(t) for t in tags if t.isdigit()]

        # Rating
        min_rating = self.request.GET.get('min_rating')
        if min_rating and min_rating.isdigit():
            filters['min_rating'] = int(min_rating)

        return filters

    def _is_valid_decimal(self, value: str) -> bool:
        """Check if string can be converted to decimal"""
        try:
            Decimal(value)
            return True
        except (ValueError, TypeError):
            return False


class BreadcrumbMixin:
    """Mixin for generating breadcrumbs"""

    def get_breadcrumbs(self, obj=None) -> List[Dict[str, Optional[str]]]:
        """Generate breadcrumbs for the view"""
        breadcrumbs = [
            {'name': _('الرئيسية'), 'url': '/'}
        ]

        if hasattr(obj, 'category') and obj.category:
            # Add category breadcrumbs
            for ancestor in obj.category.get_ancestors():
                breadcrumbs.append({
                    'name': ancestor.name,
                    'url': ancestor.get_absolute_url()
                })

            breadcrumbs.append({
                'name': obj.category.name,
                'url': obj.category.get_absolute_url()
            })

        if obj and hasattr(obj, 'name'):
            breadcrumbs.append({
                'name': obj.name,
                'url': None  # Current page
            })

        return breadcrumbs


class PaginationMixin:
    """Mixin for handling pagination"""
    paginate_by = 12

    def get_paginated_objects(self, queryset: QuerySet, page_size: Optional[int] = None):
        """Get paginated objects"""
        if page_size is None:
            page_size = self.paginate_by

        paginator = Paginator(queryset, page_size)
        page = self.request.GET.get('page')

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return page_obj, paginator


class BaseProductListView(ListView, OptimizedQueryMixin, FilterMixin, PaginationMixin, CachedMixin):
    """Base class for product list views"""
    model = Product
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self) -> QuerySet:
        """Get filtered and sorted queryset"""
        queryset = self.get_optimized_product_queryset()

        # Apply search
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = self.apply_search_filter(queryset, search_query)

        # Apply filters
        filters = self.get_filters_from_request()
        queryset = self.apply_filters(queryset, filters)

        # Apply sorting
        queryset = self.apply_sorting(queryset)

        return queryset

    def apply_search_filter(self, queryset: QuerySet, query: str) -> QuerySet:
        """Apply search filter to queryset"""
        return queryset.filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(description__icontains=query) |
            Q(description_en__icontains=query) |
            Q(sku__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    def apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply filters to queryset"""
        # Brand filter
        if 'brands' in filters and filters['brands']:
            queryset = queryset.filter(brand__id__in=filters['brands'])

        # Price range
        if 'min_price' in filters:
            queryset = queryset.filter(base_price__gte=filters['min_price'])
        if 'max_price' in filters:
            queryset = queryset.filter(base_price__lte=filters['max_price'])

        # Feature filters
        if filters.get('is_new'):
            queryset = queryset.filter(is_new=True)
        if filters.get('is_featured'):
            queryset = queryset.filter(is_featured=True)
        if filters.get('on_sale'):
            queryset = self.filter_on_sale_products(queryset)
        if filters.get('in_stock'):
            queryset = self.filter_in_stock_products(queryset)

        # Tags
        if 'tags' in filters and filters['tags']:
            queryset = queryset.filter(tags__id__in=filters['tags']).distinct()

        # Rating
        if 'min_rating' in filters:
            from django.db.models import Avg
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).filter(avg_rating__gte=filters['min_rating'])

        return queryset

    def filter_on_sale_products(self, queryset: QuerySet) -> QuerySet:
        """Filter products that are on sale"""
        from django.utils import timezone
        now = timezone.now()

        return queryset.filter(
            Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
        ).filter(
            Q(discount_start__isnull=True) | Q(discount_start__lte=now)
        ).filter(
            Q(discount_end__isnull=True) | Q(discount_end__gte=now)
        )

    def filter_in_stock_products(self, queryset: QuerySet) -> QuerySet:
        """Filter products that are in stock"""
        return queryset.filter(
            Q(track_inventory=False, stock_status='in_stock') |
            Q(track_inventory=True, stock_quantity__gt=0)
        )

    def apply_sorting(self, queryset: QuerySet) -> QuerySet:
        """Apply sorting to queryset"""
        sort_by = self.request.GET.get('sort', 'newest')

        sort_options = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_low': 'base_price',
            'price_high': '-base_price',
            'name_az': 'name',
            'name_za': '-name',
            'best_selling': '-sales_count',
            'most_viewed': '-views_count',
        }

        if sort_by in sort_options:
            return queryset.order_by(sort_options[sort_by])
        elif sort_by == 'top_rated':
            from django.db.models import Avg, Count
            return queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
                review_count=Count('reviews', filter=Q(reviews__is_approved=True))
            ).order_by('-avg_rating', '-review_count')

        return queryset.order_by('-created_at')  # Default sorting

    def get_context_data(self, **kwargs):
        """Add common context data"""
        context = super().get_context_data(**kwargs)

        # Search query
        context['search_query'] = self.request.GET.get('q', '')

        # Sort option
        context['sort_by'] = self.request.GET.get('sort', 'newest')

        # View type
        context['view_type'] = self.request.GET.get('view', 'grid')

        # Active filters
        context['active_filters'] = self.get_active_filters()

        # Filter options
        context.update(self.get_filter_options())

        return context

    def get_active_filters(self) -> List[Dict[str, str]]:
        """Get active filters for display"""
        filters = []

        # Brand filters
        brand_ids = self.request.GET.getlist('brand')
        if brand_ids:
            brands = Brand.objects.filter(id__in=brand_ids)
            for brand in brands:
                filters.append({
                    'type': 'brand',
                    'label': _('العلامة التجارية'),
                    'value': str(brand.id),
                    'display': brand.name
                })

        # Price filters
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price or max_price:
            price_display = []
            if min_price:
                price_display.append(f"من {min_price}")
            if max_price:
                price_display.append(f"إلى {max_price}")
            filters.append({
                'type': 'price',
                'label': _('السعر'),
                'value': 'price',
                'display': ' '.join(price_display)
            })

        # Feature filters
        feature_filters = [
            ('is_new', _('منتجات جديدة')),
            ('on_sale', _('منتجات مخفضة')),
            ('is_featured', _('منتجات مميزة')),
            ('in_stock', _('متوفر في المخزون')),
        ]

        for filter_key, display_name in feature_filters:
            if self.request.GET.get(filter_key) == '1':
                filters.append({
                    'type': filter_key,
                    'label': _('الحالة'),
                    'value': '1',
                    'display': display_name
                })

        return filters

    def get_filter_options(self) -> Dict[str, Any]:
        """Get filter options for the template"""
        # Cache filter options
        cache_key = f'filter_options_{self.__class__.__name__}'
        cached_options = self.get_cached_data(cache_key)

        if cached_options is not None:
            return cached_options

        from django.db.models import Count, Min, Max

        # Get brands with product counts
        brands = Brand.objects.filter(
            is_active=True,
            products__is_active=True,
            products__status='published'
        ).annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        ).filter(product_count__gt=0).order_by('name')

        # Get price range
        price_stats = Product.objects.filter(
            is_active=True,
            status='published'
        ).aggregate(
            min_price=Min('base_price'),
            max_price=Max('base_price')
        )

        # Get popular tags
        popular_tags = Tag.objects.annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        ).filter(product_count__gt=0).order_by('-product_count')[:20]

        options = {
            'brands': brands,
            'price_range': {
                'min': price_stats['min_price'] or 0,
                'max': price_stats['max_price'] or 1000
            },
            'popular_tags': popular_tags,
        }

        # Cache for 10 minutes
        self.set_cached_data(cache_key, options, 600)

        return options


class BaseProductDetailView(DetailView, OptimizedQueryMixin, BreadcrumbMixin, CachedMixin):
    """Base class for product detail views"""
    model = Product
    context_object_name = 'product'
    slug_field = 'slug'

    def get_queryset(self) -> QuerySet:
        """Get optimized product queryset"""
        return Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related(
            'category', 'brand', 'created_by'
        ).prefetch_related(
            'images',
            'tags',
            'variants',
            'related_products',
            Prefetch(
                'reviews',
                queryset=self.get_approved_reviews_queryset()
            )
        )

    def get(self, request, *args, **kwargs):
        """Handle GET request and increment views"""
        response = super().get(request, *args, **kwargs)

        # Increment view count asynchronously
        try:
            self.object.increment_views()
        except Exception as e:
            logger.warning(f"Failed to increment views for product {self.object.id}: {e}")

        return response

    def get_context_data(self, **kwargs):
        """Add context data for product detail"""
        context = super().get_context_data(**kwargs)
        product = self.object

        # Breadcrumbs
        context['breadcrumbs'] = self.get_breadcrumbs(product)

        # Reviews context
        context.update(self.get_reviews_context(product))

        # Related products
        context['related_products'] = self.get_related_products(product)

        # Product variants
        context['variants'] = product.variants.filter(is_active=True)

        # Check if in wishlist
        if self.request.user.is_authenticated:
            context['in_wishlist'] = self.is_in_wishlist(product)

        # Specifications
        context['specifications'] = product.specifications or {}

        # Recently viewed
        context['recently_viewed'] = self.get_recently_viewed(product)

        return context

    def get_reviews_context(self, product) -> Dict[str, Any]:
        """Get reviews context data"""
        reviews = product.reviews.filter(is_approved=True)

        return {
            'reviews': reviews[:5],
            'total_reviews': reviews.count(),
            'rating_breakdown': self.get_rating_breakdown(reviews),
            'can_review': product.can_review(self.request.user) if self.request.user.is_authenticated else False,
        }

    def get_rating_breakdown(self, reviews) -> Dict[int, Dict[str, int]]:
        """Calculate rating breakdown"""
        breakdown = {5: {'count': 0, 'percentage': 0}, 4: {'count': 0, 'percentage': 0},
                     3: {'count': 0, 'percentage': 0}, 2: {'count': 0, 'percentage': 0},
                     1: {'count': 0, 'percentage': 0}}

        total = reviews.count()
        if total == 0:
            return breakdown

        for rating in range(1, 6):
            count = reviews.filter(rating=rating).count()
            breakdown[rating] = {
                'count': count,
                'percentage': int((count / total) * 100)
            }

        return breakdown

    def get_related_products(self, product, limit: int = 4):
        """Get related products"""
        # Manual related products first
        related = list(product.related_products.filter(
            is_active=True,
            status='published'
        )[:limit])

        # Fill remaining with auto-suggested products
        if len(related) < limit:
            auto_related = Product.objects.filter(
                category=product.category,
                is_active=True,
                status='published'
            ).exclude(
                id__in=[product.id] + [p.id for p in related]
            ).order_by('-sales_count')[:limit - len(related)]

            related.extend(list(auto_related))

        return related

    def is_in_wishlist(self, product) -> bool:
        """Check if product is in user's wishlist"""
        from ..models import Wishlist
        return Wishlist.objects.filter(
            user=self.request.user,
            product=product
        ).exists()

    def get_recently_viewed(self, product, limit: int = 4):
        """Get recently viewed products from session"""
        session_key = 'recently_viewed'
        recently_viewed = self.request.session.get(session_key, [])

        # Add current product
        if product.id not in recently_viewed:
            recently_viewed.insert(0, product.id)
            recently_viewed = recently_viewed[:5]  # Keep only 5
            self.request.session[session_key] = recently_viewed

        # Get products excluding current one
        if len(recently_viewed) > 1:
            return Product.objects.filter(
                id__in=recently_viewed,
                is_active=True,
                status='published'
            ).exclude(id=product.id)[:limit]

        return []


@method_decorator([cache_page(300), vary_on_headers('User-Agent')], name='dispatch')
class CachedListView(BaseProductListView):
    """Cached version of product list view"""
    pass


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin that requires admin/staff permissions"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)