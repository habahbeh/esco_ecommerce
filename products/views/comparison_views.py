# File: products/views/comparison_views.py
"""
Product comparison views
Handles product comparison functionality
"""

from typing import Dict, Any, List, Optional
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q, Avg, Count
from django.db import transaction
import logging

from .api_views import BaseAPIView
from .base_views import OptimizedQueryMixin
from ..models import Product, ProductComparison

logger = logging.getLogger(__name__)


class ComparisonMixin:
    """Mixin for comparison operations"""

    MAX_COMPARISON_PRODUCTS = 4

    def get_session_key(self, request):
        """Get or create session key"""
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key

    def get_comparison(self, request, create=False):
        """Get comparison object for session"""
        session_key = self.get_session_key(request)

        if create:
            comparison, created = ProductComparison.objects.get_or_create(
                session_key=session_key
            )
            return comparison
        else:
            try:
                return ProductComparison.objects.get(session_key=session_key)
            except ProductComparison.DoesNotExist:
                return None

    def get_comparison_count(self, request) -> int:
        """Get number of products in comparison"""
        comparison = self.get_comparison(request)
        return comparison.products.count() if comparison else 0


class ComparisonView(TemplateView, OptimizedQueryMixin, ComparisonMixin):
    """
    Display product comparison page
    """
    template_name = 'products/comparison.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get products from comparison or URL parameters
        products = self.get_comparison_products()

        if products:
            # Add comparison data
            context['products'] = products
            context['comparison_data'] = self.build_comparison_data(products)
            context['specifications'] = self.get_unique_specifications(products)

            # Statistics
            context['price_range'] = self.get_price_range(products)
            context['avg_ratings'] = self.get_average_ratings(products)
        else:
            context['products'] = []
            context['comparison_data'] = {}
            context['specifications'] = {}

        context['max_products'] = self.MAX_COMPARISON_PRODUCTS
        context['title'] = _('مقارنة المنتجات')

        return context

    def get_comparison_products(self):
        """Get products for comparison"""
        # First, try to get from URL parameters
        product_ids = self.request.GET.getlist('id')
        if product_ids:
            try:
                # Convert to integers and validate
                product_ids = [int(pid) for pid in product_ids if pid.isdigit()]
                products = Product.objects.filter(
                    id__in=product_ids[:self.MAX_COMPARISON_PRODUCTS],
                    is_active=True,
                    status='published'
                ).select_related('category', 'brand').prefetch_related(
                    'images', 'reviews'
                )
                return list(products)
            except (ValueError, TypeError):
                pass

        # Fallback to session comparison
        comparison = self.get_comparison(self.request)
        if comparison:
            return list(comparison.products.filter(
                is_active=True,
                status='published'
            ).select_related('category', 'brand').prefetch_related(
                'images', 'reviews'
            ))

        return []

    def build_comparison_data(self, products) -> Dict[str, Any]:
        """Build structured comparison data"""
        if not products:
            return {}

        comparison_data = {
            'basic_info': {},
            'pricing': {},
            'features': {},
            'ratings': {},
            'availability': {}
        }

        for product in products:
            product_id = str(product.id)

            # Basic information
            comparison_data['basic_info'][product_id] = {
                'name': product.name,
                'brand': product.brand.name if product.brand else '',
                'category': product.category.name if product.category else '',
                'sku': product.sku,
                'short_description': product.short_description or ''
            }

            # Pricing
            comparison_data['pricing'][product_id] = {
                'base_price': float(product.base_price),
                'current_price': float(product.current_price),
                'has_discount': product.has_discount,
                'discount_percentage': product.discount_percentage,
                'discount_amount': float(product.discount_amount or 0)
            }

            # Features
            comparison_data['features'][product_id] = {
                'is_new': product.is_new,
                'is_featured': product.is_featured,
                'weight': float(product.weight) if product.weight else None,
                'dimensions': product.dimensions
            }

            # Ratings
            avg_rating = product.reviews.filter(is_approved=True).aggregate(
                avg=Avg('rating')
            )['avg'] or 0
            review_count = product.reviews.filter(is_approved=True).count()

            comparison_data['ratings'][product_id] = {
                'average_rating': round(float(avg_rating), 1),
                'review_count': review_count,
                'rating_percentage': int((avg_rating / 5) * 100) if avg_rating else 0
            }

            # Availability
            comparison_data['availability'][product_id] = {
                'in_stock': product.in_stock,
                'stock_quantity': product.stock_quantity if product.track_inventory else None,
                'stock_status': product.get_stock_status_display()
            }

        return comparison_data

    def get_unique_specifications(self, products) -> Dict[str, Dict]:
        """Get unique specifications across all products"""
        all_specs = {}

        for product in products:
            if product.specifications:
                for spec_key, spec_value in product.specifications.items():
                    if spec_key not in all_specs:
                        all_specs[spec_key] = {}
                    all_specs[spec_key][str(product.id)] = spec_value

        return all_specs

    def get_price_range(self, products) -> Dict[str, float]:
        """Get price range for comparison"""
        if not products:
            return {'min': 0, 'max': 0}

        prices = [float(product.current_price) for product in products]
        return {
            'min': min(prices),
            'max': max(prices),
            'difference': max(prices) - min(prices)
        }

    def get_average_ratings(self, products) -> Dict[str, float]:
        """Get average ratings statistics"""
        ratings = []
        for product in products:
            avg_rating = product.reviews.filter(is_approved=True).aggregate(
                avg=Avg('rating')
            )['avg']
            if avg_rating:
                ratings.append(float(avg_rating))

        if not ratings:
            return {'min': 0, 'max': 0, 'average': 0}

        return {
            'min': min(ratings),
            'max': max(ratings),
            'average': sum(ratings) / len(ratings)
        }


class AddToComparisonView(BaseAPIView, ComparisonMixin):
    """
    Add product to comparison via AJAX
    """

    def post(self, request):
        """Add product to comparison"""
        try:
            product_id = request.POST.get('product_id')
            if not product_id:
                return self.error_response(_('معرف المنتج مطلوب'))

            try:
                product_id = int(product_id)
            except (ValueError, TypeError):
                return self.error_response(_('معرف المنتج غير صحيح'))

            with transaction.atomic():
                product = get_object_or_404(
                    Product,
                    id=product_id,
                    is_active=True,
                    status='published'
                )

                # Get or create comparison
                comparison = self.get_comparison(request, create=True)

                # Check if product already in comparison
                if comparison.products.filter(id=product_id).exists():
                    return self.error_response(_('المنتج موجود بالفعل في المقارنة'))

                # Check limit
                if comparison.products.count() >= self.MAX_COMPARISON_PRODUCTS:
                    return self.error_response(
                        _('يمكن مقارنة {} منتجات كحد أقصى').format(self.MAX_COMPARISON_PRODUCTS)
                    )

                # Add product
                comparison.products.add(product)
                comparison.save()

                # Log the action
                logger.info(f"Product {product_id} added to comparison for session {request.session.session_key}")

                return self.success_response({
                    'message': str(_('تمت إضافة المنتج للمقارنة')),
                    'comparison_count': comparison.products.count(),
                    'product_id': product_id,
                    'product_name': product.name,
                    'max_reached': comparison.products.count() >= self.MAX_COMPARISON_PRODUCTS
                })

        except Product.DoesNotExist:
            return self.error_response(_('المنتج غير موجود'), 404)
        except Exception as e:
            logger.error(f"Error adding to comparison: {e}")
            return self.error_response(_('حدث خطأ أثناء الإضافة'), 500)


class RemoveFromComparisonView(BaseAPIView, ComparisonMixin):
    """
    Remove product from comparison via AJAX
    """

    def post(self, request):
        """Remove product from comparison"""
        try:
            product_id = request.POST.get('product_id')
            if not product_id:
                return self.error_response(_('معرف المنتج مطلوب'))

            try:
                product_id = int(product_id)
            except (ValueError, TypeError):
                return self.error_response(_('معرف المنتج غير صحيح'))

            comparison = self.get_comparison(request)
            if not comparison:
                return self.error_response(_('لا توجد مقارنة'))

            try:
                product = comparison.products.get(id=product_id)
                product_name = product.name

                with transaction.atomic():
                    comparison.products.remove(product)

                    # If no products left, delete comparison
                    if comparison.products.count() == 0:
                        comparison.delete()

                # Log the action
                logger.info(f"Product {product_id} removed from comparison for session {request.session.session_key}")

                return self.success_response({
                    'message': str(_('تمت إزالة المنتج من المقارنة')),
                    'comparison_count': self.get_comparison_count(request),
                    'product_id': product_id,
                    'product_name': product_name
                })

            except Product.DoesNotExist:
                return self.error_response(_('المنتج غير موجود في المقارنة'), 404)

        except Exception as e:
            logger.error(f"Error removing from comparison: {e}")
            return self.error_response(_('حدث خطأ أثناء الإزالة'), 500)


class ClearComparisonView(BaseAPIView, ComparisonMixin):
    """
    Clear all products from comparison
    """

    def post(self, request):
        """Clear comparison"""
        try:
            comparison = self.get_comparison(request)
            if not comparison:
                return self.error_response(_('لا توجد مقارنة'))

            product_count = comparison.products.count()

            with transaction.atomic():
                comparison.delete()

            # Log the action
            logger.info(f"Comparison cleared for session {request.session.session_key} ({product_count} products)")

            return self.success_response({
                'message': str(_('تم مسح المقارنة')),
                'cleared_count': product_count,
                'comparison_count': 0
            })

        except Exception as e:
            logger.error(f"Error clearing comparison: {e}")
            return self.error_response(_('حدث خطأ أثناء المسح'), 500)


class ComparisonStatusView(BaseAPIView, ComparisonMixin):
    """
    Get comparison status and products
    """

    def get(self, request):
        """Get comparison status"""
        try:
            comparison = self.get_comparison(request)

            if not comparison:
                return self.success_response({
                    'comparison_count': 0,
                    'products': [],
                    'max_products': self.MAX_COMPARISON_PRODUCTS,
                    'can_add_more': True
                })

            # Get product data
            products_data = []
            for product in comparison.products.all():
                primary_image = product.images.filter(is_primary=True).first()
                if not primary_image:
                    primary_image = product.images.first()

                products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'slug': product.slug,
                    'price': str(product.current_price),
                    'image': primary_image.image.url if primary_image else '/static/images/no-image.png',
                    'url': product.get_absolute_url()
                })

            comparison_count = comparison.products.count()

            return self.success_response({
                'comparison_count': comparison_count,
                'products': products_data,
                'max_products': self.MAX_COMPARISON_PRODUCTS,
                'can_add_more': comparison_count < self.MAX_COMPARISON_PRODUCTS
            })

        except Exception as e:
            logger.error(f"Error getting comparison status: {e}")
            return self.error_response(_('حدث خطأ في جلب البيانات'), 500)


# Legacy function-based views for backward compatibility
@require_http_methods(["POST"])
def add_to_comparison(request):
    """Legacy function view for adding to comparison"""
    view = AddToComparisonView()
    view.request = request
    return view.post(request)


def comparison_view(request):
    """Legacy function view for comparison"""
    view = ComparisonView.as_view()
    return view(request)