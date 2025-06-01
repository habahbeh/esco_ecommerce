# File: products/views/base_views.py
"""
Base views for products app
Contains common functionality and mixins used across different views
"""

from typing import Dict, Any, List, Optional
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Avg, Min, Max, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.utils import timezone
import logging
from django.views.decorators.vary import vary_on_headers
from django.contrib.auth.mixins import LoginRequiredMixin



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



logger = logging.getLogger(__name__)


class CachedMixin:
    """
    Mixin for caching functionality
    """
    cache_timeout = 300  # 5 minutes default

    @method_decorator(cache_page(cache_timeout))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class OptimizedQueryMixin:
    """
    Mixin for optimizing database queries
    """

    def get_optimized_product_queryset(self):
        """Get optimized product queryset with related objects"""
        from ..models import Product

        return Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related(
            'category',
            'brand'
        ).prefetch_related(
            'images',
            'tags'
        )

    def get_optimized_category_queryset(self):
        """Get optimized category queryset"""
        from ..models import Category

        return Category.objects.filter(
            is_active=True
        ).annotate(
            products_count=Count(
                'products',
                filter=Q(
                    products__is_active=True,
                    products__status='published'
                )
            )
        ).select_related('parent')


class PaginationMixin:
    """
    Mixin for pagination functionality
    """
    paginate_by = 12
    page_kwarg = 'page'

    def get_paginated_objects(self, queryset, per_page=None):
        """Get paginated objects"""
        per_page = per_page or self.paginate_by
        paginator = Paginator(queryset, per_page)
        page = self.request.GET.get(self.page_kwarg)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return page_obj, paginator


class FilterMixin:
    """
    Mixin for filtering functionality
    """

    def get_filters_from_request(self) -> Dict[str, Any]:
        """Extract filters from request parameters"""
        filters = {}

        # Category filter
        category = self.request.GET.get('category')
        if category:
            filters['category'] = category

        # Brand filter
        brand = self.request.GET.get('brand')
        if brand:
            filters['brand'] = brand

        # Price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            try:
                filters['min_price'] = float(min_price)
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                filters['max_price'] = float(max_price)
            except (ValueError, TypeError):
                pass

        # Boolean filters
        if self.request.GET.get('on_sale'):
            filters['on_sale'] = True
        if self.request.GET.get('in_stock'):
            filters['in_stock'] = True
        if self.request.GET.get('is_new'):
            filters['is_new'] = True
        if self.request.GET.get('is_featured'):
            filters['is_featured'] = True

        # Rating filter
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            try:
                filters['min_rating'] = int(min_rating)
            except (ValueError, TypeError):
                pass

        return filters

    def apply_filters(self, queryset, filters: Dict[str, Any]):
        """Apply filters to queryset"""
        if not filters:
            return queryset

        # Category filter
        if 'category' in filters:
            try:
                from ..models import Category
                category = Category.objects.get(slug=filters['category'], is_active=True)
                # Include subcategories if category has get_descendants method
                if hasattr(category, 'get_descendants'):
                    categories = [category] + list(category.get_descendants())
                    queryset = queryset.filter(category__in=categories)
                else:
                    queryset = queryset.filter(category=category)
            except:
                pass

        # Brand filter
        if 'brand' in filters:
            try:
                from ..models import Brand
                brand = Brand.objects.get(slug=filters['brand'], is_active=True)
                queryset = queryset.filter(brand=brand)
            except:
                pass

        # Price filters
        if 'min_price' in filters:
            queryset = queryset.filter(base_price__gte=filters['min_price'])
        if 'max_price' in filters:
            queryset = queryset.filter(base_price__lte=filters['max_price'])

        # On sale filter
        if filters.get('on_sale'):
            now = timezone.now()
            queryset = queryset.filter(
                Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
            ).filter(
                Q(discount_start__isnull=True) | Q(discount_start__lte=now)
            ).filter(
                Q(discount_end__isnull=True) | Q(discount_end__gte=now)
            )

        # Stock filter
        if filters.get('in_stock'):
            queryset = queryset.filter(
                Q(track_inventory=False, stock_status='in_stock') |
                Q(track_inventory=True, stock_quantity__gt=0)
            )

        # Boolean filters
        if filters.get('is_new'):
            queryset = queryset.filter(is_new=True)
        if filters.get('is_featured'):
            queryset = queryset.filter(is_featured=True)

        # Rating filter
        if 'min_rating' in filters:
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).filter(avg_rating__gte=filters['min_rating'])

        return queryset


class SortingMixin:
    """
    Mixin for sorting functionality
    """

    def apply_sorting(self, queryset):
        """Apply sorting to queryset"""
        sort_by = self.request.GET.get('sort', 'newest')

        if sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'oldest':
            return queryset.order_by('created_at')
        elif sort_by == 'price_low':
            return queryset.order_by('base_price')
        elif sort_by == 'price_high':
            return queryset.order_by('-base_price')
        elif sort_by == 'name_asc':
            return queryset.order_by('name')
        elif sort_by == 'name_desc':
            return queryset.order_by('-name')
        elif sort_by == 'best_selling':
            return queryset.order_by('-sales_count')
        elif sort_by == 'top_rated':
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).order_by('-avg_rating')
            return queryset
        elif sort_by == 'most_viewed':
            return queryset.order_by('-view_count')

        # Default sorting
        return queryset.order_by('-created_at')


class BreadcrumbMixin:
    """
    Mixin for breadcrumb functionality
    """

    def get_breadcrumbs(self, category=None):
        """Get breadcrumbs for navigation"""
        breadcrumbs = [
            {'name': _('الرئيسية'), 'url': '/'},
            {'name': _('المنتجات'), 'url': '/products/'},
        ]

        if category:
            # Add category hierarchy if get_ancestors exists
            if hasattr(category, 'get_ancestors'):
                ancestors = list(category.get_ancestors())
                for ancestor in ancestors:
                    breadcrumbs.append({
                        'name': ancestor.name,
                        'url': ancestor.get_absolute_url() if hasattr(ancestor, 'get_absolute_url') else '#'
                    })

            # Add current category
            breadcrumbs.append({
                'name': category.name,
                'url': category.get_absolute_url() if hasattr(category, 'get_absolute_url') else '#',
                'active': True
            })

        return breadcrumbs


class BaseProductListView(ListView, OptimizedQueryMixin, PaginationMixin, FilterMixin, SortingMixin, BreadcrumbMixin):
    """
    Base view for product listing with common functionality
    """
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        """Get the base queryset for products"""
        return self.get_optimized_product_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filtering context
        context['filters'] = self.get_filters_from_request()
        context['sort_options'] = self.get_sort_options()
        context['current_sort'] = self.request.GET.get('sort', 'newest')

        # Add pagination info - تحقق من وجود pagination
        if hasattr(self, 'paginate_by') and self.paginate_by:
            # تحقق من وجود paginator و page_obj في السياق
            if 'paginator' in context and 'page_obj' in context:
                context['is_paginated'] = context['paginator'].num_pages > 1
                if context['is_paginated']:
                    context['page_range'] = self.get_page_range(context['paginator'], context['page_obj'])

        return context

    def get_sort_options(self):
        """Get available sorting options"""
        return [
            ('newest', _('الأحدث')),
            ('oldest', _('الأقدم')),
            ('price_low', _('السعر: من الأقل للأعلى')),
            ('price_high', _('السعر: من الأعلى للأقل')),
            ('name_asc', _('الاسم: أ-ي')),
            ('name_desc', _('الاسم: ي-أ')),
            ('best_selling', _('الأكثر مبيعاً')),
            ('top_rated', _('الأعلى تقييماً')),
            ('most_viewed', _('الأكثر مشاهدة')),
        ]

    def get_page_range(self, paginator, page_obj):
        """Get page range for pagination"""
        current_page = page_obj.number
        total_pages = paginator.num_pages

        # Show 5 pages around current page
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)

        return range(start_page, end_page + 1)


class BaseProductDetailView(DetailView, OptimizedQueryMixin, BreadcrumbMixin):
    """
    Base view for product detail with common functionality
    """
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'

    def get_queryset(self):
        """Get optimized queryset for product detail"""
        return self.get_optimized_product_queryset()

    def get_object(self, queryset=None):
        """Get product object and increment view count"""
        obj = super().get_object(queryset)

        # Increment view count if method exists
        try:
            if hasattr(obj, 'increment_views'):
                obj.increment_views()
        except Exception as e:
            logger.warning(f"Failed to increment views for product {obj.id}: {e}")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Add breadcrumbs
        if hasattr(product, 'category') and product.category:
            context['breadcrumbs'] = self.get_breadcrumbs(product.category)

        # Add related products
        context['related_products'] = self.get_related_products(product)

        # Add product images
        if hasattr(product, 'images'):
            context['product_images'] = product.images.filter(is_active=True).order_by('order')

        # Add product variants if available
        if hasattr(product, 'variants'):
            context['product_variants'] = product.variants.filter(is_active=True)

        # Add reviews if available
        if hasattr(product, 'reviews'):
            context['reviews'] = product.reviews.filter(is_approved=True).order_by('-created_at')[:10]
            context['reviews_count'] = product.reviews.filter(is_approved=True).count()
            context['average_rating'] = product.reviews.filter(is_approved=True).aggregate(
                avg=Avg('rating')
            )['avg'] or 0

            # Check if user can review (if user is authenticated)
            context['can_review'] = (
                    self.request.user.is_authenticated and
                    not product.reviews.filter(user=self.request.user).exists()
            )

        return context

    def get_related_products(self, product, limit=6):
        """Get related products"""
        if not hasattr(product, 'category') or not product.category:
            return []

        related = self.get_optimized_product_queryset().filter(
            category=product.category
        ).exclude(id=product.id)

        # If not enough products in same category, include products from parent category
        if related.count() < limit and hasattr(product.category, 'parent') and product.category.parent:
            additional = self.get_optimized_product_queryset().filter(
                category=product.category.parent
            ).exclude(
                id__in=[product.id] + list(related.values_list('id', flat=True))
            )
            related = list(related) + list(additional[:limit - related.count()])

        return related[:limit]

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