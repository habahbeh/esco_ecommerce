# File: products/views/api_views.py
"""
API endpoints for products app
Handles AJAX requests and JSON responses
"""

from typing import Dict, Any, List, Optional
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.urls import reverse
from django.db.models import Q, Avg, Count
from django.core.exceptions import ValidationError
from django.views import View
import json
import logging

from ..models import Product, Category, Brand, ProductVariant, ProductReview
from .base_views import CachedMixin

logger = logging.getLogger(__name__)


class BaseAPIView(View, CachedMixin):
    """Base class for API views"""

    def dispatch(self, request, *args, **kwargs):
        """Handle CORS and common API setup"""
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type'
            return response

        return super().dispatch(request, *args, **kwargs)

    def json_response(self, data: Dict[str, Any], status: int = 200) -> JsonResponse:
        """Create JSON response with proper headers"""
        response = JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def error_response(self, message: str, status: int = 400) -> JsonResponse:
        """Create error response"""
        return self.json_response({'success': False, 'error': message}, status)

    def success_response(self, data: Dict[str, Any] = None, message: str = None) -> JsonResponse:
        """Create success response"""
        response_data = {'success': True}
        if data:
            response_data.update(data)
        if message:
            response_data['message'] = message
        return self.json_response(response_data)


@method_decorator(cache_page(300), name='dispatch')  # Cache for 5 minutes
class SearchSuggestionsView(BaseAPIView):
    """
    API endpoint for search suggestions
    """

    def get(self, request):
        """Get search suggestions"""
        query = request.GET.get('q', '').strip()

        if len(query) < 2:
            return self.json_response({'suggestions': []})

        # Check cache first
        cache_key = f'search_suggestions:{query.lower()}'
        cached_suggestions = self.get_cached_data(cache_key)

        if cached_suggestions is not None:
            return self.json_response({'suggestions': cached_suggestions})

        suggestions = []

        try:
            # Search in products
            products = Product.objects.filter(
                Q(name__icontains=query) | Q(name_en__icontains=query),
                is_active=True,
                status='published'
            ).values('name', 'slug')[:5]

            # Search in categories
            categories = Category.objects.filter(
                Q(name__icontains=query) | Q(name_en__icontains=query),
                is_active=True
            ).values('name', 'slug')[:3]

            # Search in brands
            brands = Brand.objects.filter(
                Q(name__icontains=query) | Q(name_en__icontains=query),
                is_active=True
            ).values('name', 'slug')[:2]

            # Build suggestions
            for product in products:
                suggestions.append({
                    'type': 'product',
                    'name': product['name'],
                    'url': reverse('products:product_detail', kwargs={'slug': product['slug']}),
                    'icon': 'product'
                })

            for category in categories:
                suggestions.append({
                    'type': 'category',
                    'name': category['name'],
                    'url': reverse('products:category_products', kwargs={'category_slug': category['slug']}),
                    'icon': 'category'
                })

            for brand in brands:
                suggestions.append({
                    'type': 'brand',
                    'name': brand['name'],
                    'url': f"{reverse('products:product_list')}?brand={brand['slug']}",
                    'icon': 'brand'
                })

            # Cache suggestions for 5 minutes
            self.set_cached_data(cache_key, suggestions, 300)

            return self.json_response({'suggestions': suggestions})

        except Exception as e:
            logger.error(f"Error in search suggestions: {e}")
            return self.error_response(_('خطأ في البحث'), 500)


class ProductQuickViewView(BaseAPIView):
    """
    API endpoint for product quick view
    """

    def get(self, request, product_id):
        """Get product quick view data"""
        try:
            product = Product.objects.select_related('category', 'brand').prefetch_related(
                'images'
            ).get(
                id=product_id,
                is_active=True,
                status='published'
            )

            # Get primary image
            primary_image = product.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = product.images.first()

            # Calculate average rating
            avg_rating = product.reviews.filter(is_approved=True).aggregate(
                avg=Avg('rating')
            )['avg'] or 0

            review_count = product.reviews.filter(is_approved=True).count()

            data = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': str(product.current_price),
                'base_price': str(product.base_price),
                'has_discount': product.has_discount,
                'discount_percentage': product.discount_percentage,
                'short_description': product.short_description or '',
                'in_stock': product.in_stock,
                'stock_quantity': product.stock_quantity if product.track_inventory else None,
                'stock_status': product.get_stock_status_display(),
                'image': primary_image.image.url if primary_image else '/static/images/no-image.png',
                'image_alt': primary_image.alt_text if primary_image else product.name,
                'url': product.get_absolute_url(),
                'rating': round(float(avg_rating), 1),
                'review_count': review_count,
                'category': {
                    'name': product.category.name,
                    'url': product.category.get_absolute_url()
                } if product.category else None,
                'brand': {
                    'name': product.brand.name,
                    'url': product.brand.get_absolute_url() if hasattr(product.brand, 'get_absolute_url') else None
                } if product.brand else None,
                'variants_count': product.variants.filter(is_active=True).count(),
                'is_new': product.is_new,
                'is_featured': product.is_featured,
                'created_at': product.created_at.isoformat()
            }

            return self.json_response(data)

        except Product.DoesNotExist:
            return self.error_response(_('المنتج غير موجود'), 404)
        except Exception as e:
            logger.error(f"Error in product quick view: {e}")
            return self.error_response(_('خطأ في تحميل المنتج'), 500)


class ProductVariantDetailsView(BaseAPIView):
    """
    API endpoint for product variant details
    """

    def get(self, request, variant_id):
        """Get variant details"""
        try:
            variant = ProductVariant.objects.select_related('product').prefetch_related(
                'images'
            ).get(
                id=variant_id,
                is_active=True,
                product__is_active=True,
                product__status='published'
            )

            # Get variant images or fallback to product images
            images = list(variant.images.all())
            if not images:
                images = list(variant.product.images.all())

            data = {
                'id': variant.id,
                'name': variant.name or variant.product.name,
                'sku': variant.sku,
                'price': str(variant.current_price),
                'base_price': str(variant.base_price),
                'stock_quantity': variant.stock_quantity,
                'available_quantity': variant.available_quantity,
                'in_stock': variant.is_in_stock,
                'weight': str(variant.weight) if variant.weight else None,
                'dimensions': variant.dimensions,
                'attributes': variant.display_attributes,
                'images': [
                    {
                        'url': img.image.url,
                        'alt': img.alt_text or variant.name,
                        'is_primary': getattr(img, 'is_primary', False)
                    } for img in images
                ]
            }

            return self.json_response(data)

        except ProductVariant.DoesNotExist:
            return self.error_response(_('متغير المنتج غير موجود'), 404)
        except Exception as e:
            logger.error(f"Error getting variant details: {e}")
            return self.error_response(_('خطأ في تحميل تفاصيل المنتج'), 500)


class ProductFiltersView(BaseAPIView):
    """
    API endpoint for getting filter options
    """

    def get(self, request):
        """Get filter options for products"""
        category_slug = request.GET.get('category')

        try:
            # Base queryset
            products_filter = Q(is_active=True, status='published')

            # Filter by category if provided
            if category_slug:
                try:
                    category = Category.objects.get(slug=category_slug, is_active=True)
                    categories = [category] + list(category.get_descendants())
                    products_filter &= Q(category__in=categories)
                except Category.DoesNotExist:
                    pass

            # Get brands with product counts
            brands = Brand.objects.filter(
                is_active=True,
                products__is_active=True,
                products__status='published'
            ).annotate(
                product_count=Count('products', filter=products_filter)
            ).filter(product_count__gt=0).order_by('name').values(
                'id', 'name', 'slug', 'product_count'
            )

            # Get price range
            from django.db.models import Min, Max
            price_stats = Product.objects.filter(products_filter).aggregate(
                min_price=Min('base_price'),
                max_price=Max('base_price')
            )

            # Get categories with product counts (if not filtering by category)
            categories = []
            if not category_slug:
                categories = Category.objects.filter(
                    is_active=True,
                    products__is_active=True,
                    products__status='published'
                ).annotate(
                    product_count=Count('products', filter=products_filter)
                ).filter(product_count__gt=0).order_by('name').values(
                    'id', 'name', 'slug', 'product_count'
                )[:20]

            # Get popular tags
            from ..models import Tag
            tags = Tag.objects.filter(
                products__is_active=True,
                products__status='published'
            ).annotate(
                product_count=Count('products', filter=products_filter)
            ).filter(product_count__gt=0).order_by('-product_count').values(
                'id', 'name', 'slug', 'product_count'
            )[:15]

            data = {
                'brands': list(brands),
                'categories': list(categories),
                'tags': list(tags),
                'price_range': {
                    'min': float(price_stats['min_price'] or 0),
                    'max': float(price_stats['max_price'] or 1000)
                }
            }

            return self.json_response(data)

        except Exception as e:
            logger.error(f"Error getting filter options: {e}")
            return self.error_response(_('خطأ في تحميل خيارات الفلترة'), 500)


@method_decorator(require_http_methods(["POST"]), name='dispatch')
class IncrementViewsView(BaseAPIView):
    """
    API endpoint for incrementing product/category views
    """

    def post(self, request):
        """Increment views for object"""
        try:
            object_type = request.POST.get('type')  # 'product' or 'category'
            object_id = request.POST.get('id')

            if not object_type or not object_id:
                return self.error_response(_('معاملات مفقودة'))

            if object_type == 'product':
                try:
                    product = Product.objects.get(id=object_id, is_active=True)
                    product.increment_views()
                    return self.success_response({'views': product.views_count})
                except Product.DoesNotExist:
                    return self.error_response(_('المنتج غير موجود'), 404)

            elif object_type == 'category':
                try:
                    category = Category.objects.get(id=object_id, is_active=True)
                    category.increment_views()
                    return self.success_response({'views': category.views_count})
                except Category.DoesNotExist:
                    return self.error_response(_('الفئة غير موجودة'), 404)
            else:
                return self.error_response(_('نوع غير صحيح'))

        except Exception as e:
            logger.error(f"Error incrementing views: {e}")
            return self.error_response(_('خطأ في العملية'), 500)


class Product360View(BaseAPIView):
    """
    API endpoint for 360-degree product view
    """

    def get(self, request, product_id):
        """Get 360-degree view images"""
        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True,
                status='published'
            )

            # Get 360-degree images
            images_360 = product.images.filter(is_360=True).order_by('order')

            if not images_360.exists():
                return self.error_response(_('لا توجد صور بزاوية 360 درجة'), 404)

            data = {
                'product_name': product.name,
                'product_id': product.id,
                'images': [
                    {
                        'url': img.image.url,
                        'order': img.order,
                        'alt': img.alt_text or f"{product.name} - 360° view {img.order}"
                    } for img in images_360
                ],
                'total_images': images_360.count()
            }

            return self.json_response(data)

        except Product.DoesNotExist:
            return self.error_response(_('المنتج غير موجود'), 404)
        except Exception as e:
            logger.error(f"Error getting 360 view: {e}")
            return self.error_response(_('خطأ في تحميل العرض'), 500)


class ProductStockCheckView(BaseAPIView):
    """
    API endpoint for checking product stock
    """

    def get(self, request, product_id):
        """Check product stock status"""
        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True,
                status='published'
            )

            # Check if it's a variant request
            variant_id = request.GET.get('variant_id')
            if variant_id:
                try:
                    variant = product.variants.get(id=variant_id, is_active=True)
                    stock_data = {
                        'in_stock': variant.is_in_stock,
                        'stock_quantity': variant.stock_quantity if variant.track_inventory else None,
                        'available_quantity': variant.available_quantity,
                        'stock_status': variant.get_stock_status_display(),
                        'max_order_quantity': variant.max_order_quantity or 10
                    }
                except ProductVariant.DoesNotExist:
                    return self.error_response(_('متغير المنتج غير موجود'), 404)
            else:
                stock_data = {
                    'in_stock': product.in_stock,
                    'stock_quantity': product.stock_quantity if product.track_inventory else None,
                    'available_quantity': product.available_quantity,
                    'stock_status': product.get_stock_status_display(),
                    'max_order_quantity': product.max_order_quantity or 10
                }

            return self.json_response(stock_data)

        except Product.DoesNotExist:
            return self.error_response(_('المنتج غير موجود'), 404)
        except Exception as e:
            logger.error(f"Error checking stock: {e}")
            return self.error_response(_('خطأ في فحص المخزون'), 500)


# Function-based views for backward compatibility
@require_http_methods(["GET"])
@cache_page(300)
def search_suggestions(request):
    """Legacy function view for search suggestions"""
    view = SearchSuggestionsView()
    view.request = request
    return view.get(request)


@require_http_methods(["GET"])
def product_quick_view(request, product_id):
    """Legacy function view for product quick view"""
    view = ProductQuickViewView()
    view.request = request
    return view.get(request, product_id)


@require_http_methods(["GET"])
def get_variant_details(request, variant_id):
    """Legacy function view for variant details"""
    view = ProductVariantDetailsView()
    view.request = request
    return view.get(request, variant_id)


@require_http_methods(["POST"])
def increment_category_views(request, category_id):
    """Legacy function view for incrementing category views"""
    view = IncrementViewsView()
    view.request = request
    return view.post(request)


@require_http_methods(["GET"])
def product_360_view(request, product_id):
    """Legacy function view for 360 product view"""
    view = Product360View()
    view.request = request
    return view.get(request, product_id)