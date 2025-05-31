# File: products/views/admin_views.py
"""
Admin views for products management
Handles admin-only functionality like bulk operations and analytics
"""

from typing import Dict, Any, List, Optional
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, TemplateView
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum, F
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import csv
import json
import logging
from datetime import datetime, timedelta

from .base_views import AdminRequiredMixin, OptimizedQueryMixin, PaginationMixin
from .api_views import BaseAPIView
from ..models import Product, Category, Brand, ProductReview, Tag

logger = logging.getLogger(__name__)


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """
    Admin dashboard with product statistics and quick actions
    """
    template_name = 'admin/products/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Product statistics
        context['product_stats'] = self.get_product_statistics()

        # Recent activities
        context['recent_reviews'] = self.get_recent_reviews()
        context['low_stock_products'] = self.get_low_stock_products()
        context['pending_reviews'] = self.get_pending_reviews()

        # Performance metrics
        context['performance_metrics'] = self.get_performance_metrics()

        context['title'] = _('لوحة تحكم المنتجات')

        return context

    def get_product_statistics(self) -> Dict[str, Any]:
        """Get comprehensive product statistics"""
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True, status='published').count()

        return {
            'total_products': total_products,
            'active_products': active_products,
            'inactive_products': total_products - active_products,
            'draft_products': Product.objects.filter(status='draft').count(),
            'out_of_stock': Product.objects.filter(
                track_inventory=True,
                stock_quantity=0
            ).count(),
            'low_stock': Product.objects.filter(
                track_inventory=True,
                stock_quantity__gt=0,
                stock_quantity__lte=F('low_stock_threshold')
            ).count(),
            'categories_count': Category.objects.filter(is_active=True).count(),
            'brands_count': Brand.objects.filter(is_active=True).count(),
            'total_reviews': ProductReview.objects.count(),
            'pending_reviews': ProductReview.objects.filter(is_approved=False).count(),
        }

    def get_recent_reviews(self, limit: int = 5):
        """Get recent product reviews"""
        return ProductReview.objects.select_related(
            'product', 'user'
        ).order_by('-created_at')[:limit]

    def get_low_stock_products(self, limit: int = 10):
        """Get products with low stock"""
        return Product.objects.filter(
            track_inventory=True,
            stock_quantity__gt=0,
            stock_quantity__lte=F('low_stock_threshold'),
            is_active=True
        ).select_related('category', 'brand').order_by('stock_quantity')[:limit]

    def get_pending_reviews(self, limit: int = 10):
        """Get pending reviews for approval"""
        return ProductReview.objects.filter(
            is_approved=False
        ).select_related('product', 'user').order_by('-created_at')[:limit]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the last 30 days"""
        from django.utils import timezone
        last_30_days = timezone.now() - timedelta(days=30)

        # This would typically come from order/sales data
        # For now, return mock data
        return {
            'total_sales': 0,  # Would come from Order model
            'total_revenue': 0,  # Would come from Order model
            'avg_order_value': 0,
            'conversion_rate': 0,
            'top_selling_products': self.get_top_selling_products(),
            'most_viewed_products': self.get_most_viewed_products(),
        }

    def get_top_selling_products(self, limit: int = 5):
        """Get top selling products"""
        return Product.objects.filter(
            is_active=True,
            sales_count__gt=0
        ).order_by('-sales_count')[:limit]

    def get_most_viewed_products(self, limit: int = 5):
        """Get most viewed products"""
        return Product.objects.filter(
            is_active=True,
            views_count__gt=0
        ).order_by('-views_count')[:limit]


@method_decorator(staff_member_required, name='dispatch')
class ProductBulkEditView(TemplateView):
    """
    Bulk edit products view
    """
    template_name = 'admin/products/bulk_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get product IDs from session or query params
        product_ids = self.request.session.get('bulk_edit_products', [])
        if not product_ids:
            product_ids = self.request.GET.getlist('ids')
            if product_ids:
                self.request.session['bulk_edit_products'] = product_ids

        if product_ids:
            products = Product.objects.filter(id__in=product_ids)
            context['products'] = products
            context['products_count'] = products.count()
        else:
            context['products'] = Product.objects.none()
            context['products_count'] = 0

        # Filter options
        context['categories'] = Category.objects.filter(is_active=True)
        context['brands'] = Brand.objects.filter(is_active=True)
        context['tags'] = Tag.objects.all()

        context['title'] = _('تعديل المنتجات بالجملة')

        return context

    def post(self, request):
        """Handle bulk edit form submission"""
        product_ids = request.session.get('bulk_edit_products', [])
        if not product_ids:
            messages.error(request, _('لم يتم تحديد منتجات للتعديل'))
            return redirect('admin:products_product_changelist')

        action = request.POST.get('action')

        try:
            with transaction.atomic():
                products = Product.objects.filter(id__in=product_ids)
                updated_count = 0

                if action == 'update_category':
                    category_id = request.POST.get('category')
                    if category_id:
                        category = get_object_or_404(Category, id=category_id)
                        updated_count = products.update(category=category)

                elif action == 'update_brand':
                    brand_id = request.POST.get('brand')
                    if brand_id:
                        brand = get_object_or_404(Brand, id=brand_id)
                        updated_count = products.update(brand=brand)

                elif action == 'update_status':
                    status = request.POST.get('status')
                    if status in ['draft', 'published', 'archived']:
                        updated_count = products.update(status=status)

                elif action == 'update_featured':
                    is_featured = request.POST.get('is_featured') == 'on'
                    updated_count = products.update(is_featured=is_featured)

                elif action == 'update_new':
                    is_new = request.POST.get('is_new') == 'on'
                    updated_count = products.update(is_new=is_new)

                elif action == 'update_tags':
                    tag_ids = request.POST.getlist('tags')
                    if tag_ids:
                        tags = Tag.objects.filter(id__in=tag_ids)
                        for product in products:
                            product.tags.set(tags)
                        updated_count = products.count()

                elif action == 'apply_discount':
                    discount_type = request.POST.get('discount_type')
                    discount_value = request.POST.get('discount_value')

                    if discount_type and discount_value:
                        try:
                            discount_value = float(discount_value)
                            if discount_type == 'percentage':
                                updated_count = products.update(discount_percentage=discount_value)
                            elif discount_type == 'amount':
                                updated_count = products.update(discount_amount=discount_value)
                        except ValueError:
                            messages.error(request, _('قيمة الخصم غير صحيحة'))
                            return redirect('products:admin_bulk_edit')

                # Clear session
                if 'bulk_edit_products' in request.session:
                    del request.session['bulk_edit_products']

                messages.success(
                    request,
                    _('تم تحديث {} منتج بنجاح').format(updated_count)
                )

                # Log the action
                logger.info(f"Admin {request.user.id} bulk edited {updated_count} products with action: {action}")

        except Exception as e:
            logger.error(f"Error in bulk edit: {e}")
            messages.error(request, _('حدث خطأ أثناء التحديث'))

        return redirect('admin:products_product_changelist')


class ReviewModerationView(AdminRequiredMixin, ListView):
    """
    Review moderation interface for admins
    """
    model = ProductReview
    template_name = 'admin/products/review_moderation.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        """Get reviews based on filter"""
        queryset = ProductReview.objects.select_related(
            'product', 'user'
        ).order_by('-created_at')

        # Filter by status
        status = self.request.GET.get('status', 'pending')
        if status == 'pending':
            queryset = queryset.filter(is_approved=False)
        elif status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif status == 'reported':
            queryset = queryset.filter(report_count__gt=0)

        # Filter by rating
        rating = self.request.GET.get('rating')
        if rating:
            try:
                rating = int(rating)
                queryset = queryset.filter(rating=rating)
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistics
        context['pending_count'] = ProductReview.objects.filter(is_approved=False).count()
        context['approved_count'] = ProductReview.objects.filter(is_approved=True).count()
        context['reported_count'] = ProductReview.objects.filter(report_count__gt=0).count()

        # Current filter
        context['current_status'] = self.request.GET.get('status', 'pending')
        context['current_rating'] = self.request.GET.get('rating')

        context['title'] = _('إدارة المراجعات')

        return context


class ReviewModerationAPIView(BaseAPIView):
    """
    API for review moderation actions
    """

    def post(self, request):
        """Handle review moderation actions"""
        if not request.user.is_staff:
            return self.error_response(_('غير مصرح'), 403)

        action = request.POST.get('action')
        review_ids = request.POST.getlist('review_ids[]')

        if not action or not review_ids:
            return self.error_response(_('معاملات مفقودة'))

        try:
            with transaction.atomic():
                reviews = ProductReview.objects.filter(id__in=review_ids)
                updated_count = 0

                if action == 'approve':
                    updated_count = reviews.update(is_approved=True)
                elif action == 'reject':
                    updated_count = reviews.update(is_approved=False)
                elif action == 'delete':
                    updated_count = reviews.count()
                    reviews.delete()
                elif action == 'mark_spam':
                    updated_count = reviews.update(is_approved=False, is_spam=True)

                # Log the action
                logger.info(f"Admin {request.user.id} performed {action} on {updated_count} reviews")

                return self.success_response({
                    'message': _('تم تنفيذ العملية بنجاح'),
                    'updated_count': updated_count,
                    'action': action
                })

        except Exception as e:
            logger.error(f"Error in review moderation: {e}")
            return self.error_response(_('حدث خطأ أثناء العملية'), 500)


@method_decorator(staff_member_required, name='dispatch')
class ProductAnalyticsView(TemplateView):
    """
    Product analytics and reports view
    """
    template_name = 'admin/products/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Date range
        date_range = self.request.GET.get('range', '30')
        try:
            days = int(date_range)
        except ValueError:
            days = 30

        from django.utils import timezone
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Analytics data
        context['analytics_data'] = self.get_analytics_data(start_date, end_date)
        context['top_products'] = self.get_top_products()
        context['category_performance'] = self.get_category_performance()
        context['brand_performance'] = self.get_brand_performance()

        context['date_range'] = days
        context['title'] = _('تحليلات المنتجات')

        return context

    def get_analytics_data(self, start_date, end_date) -> Dict[str, Any]:
        """Get analytics data for date range"""
        # Product views (would come from tracking data)
        total_views = Product.objects.aggregate(
            total_views=Sum('views_count')
        )['total_views'] or 0

        # Most viewed products
        most_viewed = Product.objects.filter(
            views_count__gt=0
        ).order_by('-views_count')[:10]

        # Most reviewed products
        most_reviewed = Product.objects.annotate(
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        ).filter(review_count__gt=0).order_by('-review_count')[:10]

        # Best rated products
        best_rated = Product.objects.annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        ).filter(
            review_count__gte=5,  # At least 5 reviews
            avg_rating__gte=4.0  # Rating 4.0 or higher
        ).order_by('-avg_rating')[:10]

        return {
            'total_views': total_views,
            'most_viewed': most_viewed,
            'most_reviewed': most_reviewed,
            'best_rated': best_rated,
        }

    def get_top_products(self, limit: int = 10):
        """Get top performing products"""
        return Product.objects.filter(
            is_active=True,
            sales_count__gt=0
        ).order_by('-sales_count')[:limit]

    def get_category_performance(self):
        """Get category performance metrics"""
        return Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            )),
            total_views=Sum('products__views_count'),
            avg_rating=Avg('products__reviews__rating', filter=Q(
                products__reviews__is_approved=True
            ))
        ).filter(product_count__gt=0).order_by('-total_views')[:10]

    def get_brand_performance(self):
        """Get brand performance metrics"""
        return Brand.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            )),
            total_views=Sum('products__views_count'),
            avg_rating=Avg('products__reviews__rating', filter=Q(
                products__reviews__is_approved=True
            ))
        ).filter(product_count__gt=0).order_by('-total_views')[:10]


@staff_member_required
@require_http_methods(["POST"])
def bulk_action_products(request):
    """
    Handle bulk actions on products
    """
    action = request.POST.get('action')
    product_ids = request.POST.getlist('product_ids[]')

    if not action or not product_ids:
        return JsonResponse({
            'success': False,
            'message': _('معاملات مفقودة')
        })

    try:
        with transaction.atomic():
            products = Product.objects.filter(id__in=product_ids)
            updated_count = 0

            if action == 'activate':
                updated_count = products.update(is_active=True)
            elif action == 'deactivate':
                updated_count = products.update(is_active=False)
            elif action == 'publish':
                updated_count = products.update(status='published')
            elif action == 'draft':
                updated_count = products.update(status='draft')
            elif action == 'archive':
                updated_count = products.update(status='archived')
            elif action == 'delete':
                updated_count = products.count()
                products.delete()
            elif action == 'feature':
                updated_count = products.update(is_featured=True)
            elif action == 'unfeature':
                updated_count = products.update(is_featured=False)

            # Log the action
            logger.info(f"Admin {request.user.id} performed bulk {action} on {updated_count} products")

            return JsonResponse({
                'success': True,
                'message': _('تم تنفيذ العملية على {} منتج').format(updated_count),
                'updated_count': updated_count
            })

    except Exception as e:
        logger.error(f"Error in bulk action: {e}")
        return JsonResponse({
            'success': False,
            'message': _('حدث خطأ أثناء العملية')
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def reset_product_stats(request, product_id):
    """
    Reset product statistics (views, sales count, etc.)
    """
    try:
        product = get_object_or_404(Product, id=product_id)

        with transaction.atomic():
            product.views_count = 0
            product.sales_count = 0
            product.save(update_fields=['views_count', 'sales_count'])

            # Log the action
            logger.info(f"Admin {request.user.id} reset stats for product {product_id}")

            return JsonResponse({
                'success': True,
                'message': _('تم إعادة تعيين الإحصائيات بنجاح')
            })

    except Exception as e:
        logger.error(f"Error resetting product stats: {e}")
        return JsonResponse({
            'success': False,
            'message': _('حدث خطأ أثناء العملية')
        }, status=500)


@staff_member_required
def duplicate_product(request, product_id):
    """
    Duplicate a product
    """
    try:
        original_product = get_object_or_404(Product, id=product_id)

        with transaction.atomic():
            # Create a copy
            new_product = Product.objects.get(id=product_id)
            new_product.pk = None  # This will create a new instance
            new_product.name = f"{original_product.name} (نسخة)"
            new_product.slug = f"{original_product.slug}-copy"
            new_product.sku = f"{original_product.sku}-COPY"
            new_product.status = 'draft'
            new_product.is_active = False
            new_product.views_count = 0
            new_product.sales_count = 0
            new_product.save()

            # Copy tags
            new_product.tags.set(original_product.tags.all())

            # Copy related products
            new_product.related_products.set(original_product.related_products.all())

            # Log the action
            logger.info(f"Admin {request.user.id} duplicated product {product_id} to {new_product.id}")

            messages.success(request, _('تم نسخ المنتج بنجاح'))

    except Exception as e:
        logger.error(f"Error duplicating product: {e}")
        messages.error(request, _('حدث خطأ أثناء نسخ المنتج'))

    return redirect('admin:products_product_changelist')