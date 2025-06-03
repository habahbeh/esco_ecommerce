# File: products/views/product_views.py
"""
Product-specific views
Handles product listing, detail, and related functionality
"""

from typing import Optional, Dict, Any
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Min, Max, Prefetch
from django.utils.translation import gettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
import logging

from .base_views import BaseProductListView, BaseProductDetailView, CachedMixin
from ..models import Product, Category, Brand, ProductImage, Tag
from django.views.generic import ListView

logger = logging.getLogger(__name__)


class ProductListView(BaseProductListView):
    """
    Enhanced product list view with advanced filtering and caching
    """
    template_name = 'products/product_list.html'

    def get_queryset(self):
        """Get queryset with category filtering"""
        queryset = super().get_queryset()

        # Category filter
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                # Use get_all_children() instead of get_descendants()
                categories = category.get_all_children(include_self=True)
                queryset = queryset.filter(category__in=categories)

                # Store category for context
                self.category = category
            except Category.DoesNotExist:
                raise Http404(_("الفئة غير موجودة"))
        else:
            self.category = None

        return queryset

    def get_context_data(self, **kwargs):
        """Add category-specific context"""
        context = super().get_context_data(**kwargs)

        # Category context
        if hasattr(self, 'category') and self.category:
            context['category'] = self.category
            context['subcategories'] = self.category.children.filter(is_active=True)
            context['breadcrumbs'] = self.get_breadcrumbs(self.category)
        else:
            context['category'] = None
            context['subcategories'] = Category.objects.filter(
                parent=None,
                is_active=True
            ).order_by('sort_order', 'name')

        # Results count
        context['total_count'] = self.get_queryset().count()

        return context


class ProductDetailView(BaseProductDetailView):
    """
    Enhanced product detail view with performance optimizations
    """
    template_name = 'products/product_detail.html'

    def get_context_data(self, **kwargs):
        """Add additional context for product detail"""
        context = super().get_context_data(**kwargs)

        # Add review form if user can review
        if context.get('can_review'):
            from ..forms import ProductReviewForm
            context['review_form'] = ProductReviewForm()

        return context


@method_decorator(cache_page(600), name='dispatch')  # Cache for 10 minutes
class CategoryListView(BaseProductListView):
    """
    Display main categories with product counts
    """
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        """Get main categories with product counts"""
        return Category.objects.filter(
            parent=None,
            is_active=True
        ).prefetch_related(
            Prefetch(
                'children',
                queryset=Category.objects.filter(is_active=True)
            )
        ).annotate(
            total_products=Count(
                'products',
                filter=Q(
                    products__is_active=True,
                    products__status='published'
                )
            )
        ).order_by('sort_order', 'name')  # تم التصحيح هنا

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Featured categories
        context['featured_categories'] = Category.objects.filter(
            is_featured=True,
            is_active=True
        ).order_by('sort_order')[:6]  # تم التصحيح هنا أيضاً

        return context


class CategoryDetailView(BaseProductDetailView):
    """
    Category detail view with products
    """
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'

    def get_queryset(self):
        """Get active categories"""
        return Category.objects.filter(is_active=True).select_related('parent')

    def get(self, request, *args, **kwargs):
        """Handle GET request and increment views"""
        response = super(BaseProductDetailView, self).get(request, *args, **kwargs)

        # Increment category view count
        try:
            self.object.increment_views()
        except Exception as e:
            logger.warning(f"Failed to increment views for category {self.object.id}: {e}")

        return response

    def get_context_data(self, **kwargs):
        """Add category-specific context"""
        context = super(BaseProductDetailView, self).get_context_data(**kwargs)
        category = self.object

        # Subcategories
        context['subcategories'] = category.children.filter(
            is_active=True
        ).annotate(
            products_count=Count(
                'products',
                filter=Q(
                    products__is_active=True,
                    products__status='published'
                )
            )
        )

        # Products in this category
        products_queryset = Product.objects.filter(
            category=category,
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images')

        # Apply sorting
        sort_by = self.request.GET.get('sort', 'newest')
        products_queryset = self.apply_category_sorting(products_queryset, sort_by)

        # Pagination
        from .base_views import PaginationMixin
        pagination_mixin = PaginationMixin()
        pagination_mixin.request = self.request
        products_page, paginator = pagination_mixin.get_paginated_objects(products_queryset)

        context['products'] = products_page
        context['page_obj'] = products_page
        context['paginator'] = paginator
        context['is_paginated'] = products_page.has_other_pages()

        # Statistics
        context['products_count'] = category.products.filter(
            is_active=True,
            status='published'
        ).count()
        context['subcategories_count'] = context['subcategories'].count()

        # Top brands in this category
        context['top_brands'] = Brand.objects.filter(
            products__category=category,
            products__is_active=True,
            products__status='published',
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(
                    products__category=category,
                    products__is_active=True,
                    products__status='published'
                )
            )
        ).order_by('-product_count')[:10]

        context['brands_count'] = context['top_brands'].count()

        return context

    def apply_category_sorting(self, queryset, sort_by: str):
        """Apply sorting specific to category view"""
        if sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'price_low':
            return queryset.order_by('base_price')
        elif sort_by == 'price_high':
            return queryset.order_by('-base_price')
        elif sort_by == 'best_selling':
            return queryset.order_by('-sales_count')
        elif sort_by == 'top_rated':
            return queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).order_by('-avg_rating')

        return queryset.order_by('-created_at')


class SpecialOffersView(BaseProductListView):
    """
    Special offers and discounted products view
    """
    template_name = 'products/special_offers.html'

    def get_queryset(self):
        """Get products with active discounts"""
        from django.utils import timezone
        now = timezone.now()

        return self.get_optimized_product_queryset().filter(
            Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
        ).filter(
            Q(discount_start__isnull=True) | Q(discount_start__lte=now)
        ).filter(
            Q(discount_end__isnull=True) | Q(discount_end__gte=now)
        ).order_by('-discount_percentage', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('العروض الخاصة')

        # Calculate total savings
        products = self.get_queryset()
        total_savings = sum(
            (product.base_price - product.current_price)
            for product in products
            if product.has_discount
        )
        context['total_savings'] = total_savings

        return context


class TagProductsView(BaseProductListView):
    """
    Products filtered by tag
    """
    template_name = 'products/tag_products.html'

    def get_queryset(self):
        """Get products filtered by tag"""
        tag_slug = self.kwargs.get('tag_slug')

        try:
            self.tag = Tag.objects.get(slug=tag_slug)
        except Tag.DoesNotExist:
            raise Http404(_("الوسم غير موجود"))

        return super().get_queryset().filter(tags=self.tag)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['title'] = f'{_("منتجات بوسم")}: {self.tag.name}'

        return context


class BrandProductsView(BaseProductListView):
    """
    Products filtered by brand
    """
    template_name = 'products/brand_products.html'

    def get_queryset(self):
        """Get products filtered by brand"""
        brand_slug = self.kwargs.get('brand_slug')

        try:
            self.brand = Brand.objects.get(slug=brand_slug, is_active=True)
        except Brand.DoesNotExist:
            raise Http404(_("العلامة التجارية غير موجودة"))

        return super().get_queryset().filter(brand=self.brand)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand'] = self.brand
        context['title'] = f'{_("منتجات")}: {self.brand.name}'

        # Brand statistics
        context['brand_stats'] = {
            'total_products': self.brand.products.filter(
                is_active=True,
                status='published'
            ).count(),
            'categories_count': self.brand.products.filter(
                is_active=True,
                status='published'
            ).values('category').distinct().count(),
            'avg_rating': self.brand.products.filter(
                is_active=True,
                status='published'
            ).aggregate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            )['avg_rating'] or 0
        }

        return context


class NewProductsView(BaseProductListView):
    """
    View for new products
    """
    template_name = 'products/new_products.html'

    def get_queryset(self):
        """Get new products"""
        return super().get_queryset().filter(is_new=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('المنتجات الجديدة')

        return context


class FeaturedProductsView(BaseProductListView):
    """
    View for featured products
    """
    template_name = 'products/featured_products.html'

    def get_queryset(self):
        """Get featured products"""
        return super().get_queryset().filter(is_featured=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('المنتجات المميزة')

        return context


class BestSellersView(BaseProductListView):
    """
    View for best selling products
    """
    template_name = 'products/best_sellers.html'

    def get_queryset(self):
        """Get best selling products"""
        return super().get_queryset().filter(
            sales_count__gt=0
        ).order_by('-sales_count')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('الأكثر مبيعاً')

        return context


class ProductVariantDetailView(BaseProductDetailView):
    """
    Product variant detail view
    """
    template_name = 'products/variant_detail.html'

    def get_object(self, queryset=None):
        """Get product variant"""
        from ..models import ProductVariant

        variant_id = self.kwargs.get('variant_id')
        try:
            variant = ProductVariant.objects.select_related('product').get(
                id=variant_id,
                is_active=True,
                product__is_active=True,
                product__status='published'
            )
            return variant.product
        except ProductVariant.DoesNotExist:
            raise Http404(_("متغير المنتج غير موجود"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the specific variant
        variant_id = self.kwargs.get('variant_id')
        try:
            variant = self.object.variants.get(id=variant_id, is_active=True)
            context['selected_variant'] = variant
        except:
            context['selected_variant'] = None

        return context

# دالة الاستيراد المتأخر في بداية الملف
def get_product_model():
    from ..models import Product
    return Product

class ProductListView(ListView):
    def get_queryset(self):
        # استخدام الدالة عند الحاجة
        Product = get_product_model()
        return Product.objects.filter(is_active=True)