# File: products/views/wishlist_views.py
"""
Wishlist views for handling user wishlists
Includes adding/removing products and displaying wishlist
"""

from typing import Dict, Any, Optional
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, IntegrityError
import logging

from .api_views import BaseAPIView
from .base_views import OptimizedQueryMixin, PaginationMixin
from ..models import Product, Wishlist

logger = logging.getLogger(__name__)


class WishlistMixin:
    """Mixin for wishlist operations"""

    def get_user_wishlist_count(self, user) -> int:
        """Get user's wishlist count"""
        if not user.is_authenticated:
            return 0
        return user.wishlists.count()

    def is_in_wishlist(self, user, product) -> bool:
        """Check if product is in user's wishlist"""
        if not user.is_authenticated:
            return False
        return Wishlist.objects.filter(user=user, product=product).exists()


@method_decorator(login_required, name='dispatch')
class WishlistView(ListView, OptimizedQueryMixin, PaginationMixin, WishlistMixin):
    """
    Display user's wishlist with pagination and sorting
    """
    template_name = 'products/wishlist.html'
    context_object_name = 'wishlist_items'
    paginate_by = 12

    def get_queryset(self):
        """Get user's wishlist items"""
        return Wishlist.objects.filter(
            user=self.request.user
        ).select_related(
            'product__category',
            'product__brand'
        ).prefetch_related(
            Prefetch(
                'product__images',
                queryset=self.get_optimized_product_images()
            )
        ).order_by('-created_at')

    def get_optimized_product_images(self):
        """Get optimized product images queryset"""
        from ..models import ProductImage
        return ProductImage.objects.filter(is_primary=True).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Wishlist statistics
        wishlist_items = self.get_queryset()
        context['wishlist_count'] = wishlist_items.count()

        # Calculate total value
        total_value = sum(
            item.product.current_price for item in wishlist_items
            if item.product.current_price
        )
        context['total_value'] = total_value

        # Check availability
        available_items = [
            item for item in wishlist_items
            if item.product.in_stock
        ]
        context['available_count'] = len(available_items)
        context['unavailable_count'] = context['wishlist_count'] - len(available_items)

        # Sort options
        context['sort_by'] = self.request.GET.get('sort', 'newest')

        context['title'] = _('قائمة الأمنيات')

        return context


@method_decorator(login_required, name='dispatch')
class AddToWishlistView(BaseAPIView, WishlistMixin):
    """
    Add product to wishlist via AJAX
    """

    def post(self, request, product_id):
        """Add product to wishlist"""
        try:
            with transaction.atomic():
                product = get_object_or_404(
                    Product,
                    id=product_id,
                    is_active=True,
                    status='published'
                )

                wishlist, created = Wishlist.objects.get_or_create(
                    user=request.user,
                    product=product,
                    defaults={'created_at': timezone.now()}
                )

                if created:
                    message = _('تمت إضافة المنتج إلى قائمة الأمنيات')
                    status = 'added'

                    # Log the action
                    logger.info(f"User {request.user.id} added product {product.id} to wishlist")
                else:
                    message = _('المنتج موجود بالفعل في قائمة الأمنيات')
                    status = 'exists'

                return self.success_response({
                    'status': status,
                    'message': str(message),
                    'wishlist_count': self.get_user_wishlist_count(request.user),
                    'product_id': product.id,
                    'in_wishlist': True
                })

        except Product.DoesNotExist:
            return self.error_response(_('المنتج غير موجود'), 404)
        except IntegrityError:
            return self.error_response(_('المنتج موجود بالفعل في قائمة الأمنيات'))
        except Exception as e:
            logger.error(f"Error adding to wishlist: {e}")
            return self.error_response(_('حدث خطأ أثناء الإضافة'), 500)


@method_decorator(login_required, name='dispatch')
class RemoveFromWishlistView(BaseAPIView, WishlistMixin):
    """
    Remove product from wishlist via AJAX
    """

    def post(self, request, product_id):
        """Remove product from wishlist"""
        try:
            with transaction.atomic():
                wishlist = get_object_or_404(
                    Wishlist,
                    user=request.user,
                    product_id=product_id
                )

                product_name = wishlist.product.name
                wishlist.delete()

                # Log the action
                logger.info(f"User {request.user.id} removed product {product_id} from wishlist")

                return self.success_response({
                    'message': str(_('تمت إزالة المنتج من قائمة الأمنيات')),
                    'wishlist_count': self.get_user_wishlist_count(request.user),
                    'product_id': product_id,
                    'product_name': product_name,
                    'in_wishlist': False
                })

        except Wishlist.DoesNotExist:
            return self.error_response(_('المنتج غير موجود في قائمة الأمنيات'), 404)
        except Exception as e:
            logger.error(f"Error removing from wishlist: {e}")
            return self.error_response(_('حدث خطأ أثناء الإزالة'), 500)


@method_decorator(login_required, name='dispatch')
class ToggleWishlistView(BaseAPIView, WishlistMixin):
    """
    Toggle product in wishlist (add if not exists, remove if exists)
    """

    def post(self, request, product_id):
        """Toggle product in wishlist"""
        try:
            with transaction.atomic():
                product = get_object_or_404(
                    Product,
                    id=product_id,
                    is_active=True,
                    status='published'
                )

                wishlist, created = Wishlist.objects.get_or_create(
                    user=request.user,
                    product=product
                )

                if not created:
                    # Product was already in wishlist, remove it
                    wishlist.delete()
                    in_wishlist = False
                    message = _('تمت إزالة المنتج من قائمة الأمنيات')
                    action = 'removed'
                else:
                    # Product was added to wishlist
                    in_wishlist = True
                    message = _('تمت إضافة المنتج إلى قائمة الأمنيات')
                    action = 'added'

                # Log the action
                logger.info(f"User {request.user.id} {action} product {product.id} in wishlist")

                return self.success_response({
                    'in_wishlist': in_wishlist,
                    'action': action,
                    'message': str(message),
                    'wishlist_count': self.get_user_wishlist_count(request.user),
                    'product_id': product.id
                })

        except Product.DoesNotExist:
            return self.error_response(_('المنتج غير موجود'), 404)
        except Exception as e:
            logger.error(f"Error toggling wishlist: {e}")
            return self.error_response(_('حدث خطأ في العملية'), 500)


@method_decorator(login_required, name='dispatch')
class ClearWishlistView(BaseAPIView, WishlistMixin):
    """
    Clear all items from user's wishlist
    """

    def post(self, request):
        """Clear all wishlist items"""
        try:
            with transaction.atomic():
                deleted_count = Wishlist.objects.filter(user=request.user).count()
                Wishlist.objects.filter(user=request.user).delete()

                # Log the action
                logger.info(f"User {request.user.id} cleared wishlist ({deleted_count} items)")

                return self.success_response({
                    'message': str(_('تم مسح قائمة الأمنيات')),
                    'deleted_count': deleted_count,
                    'wishlist_count': 0
                })

        except Exception as e:
            logger.error(f"Error clearing wishlist: {e}")
            return self.error_response(_('حدث خطأ أثناء المسح'), 500)


@method_decorator(login_required, name='dispatch')
class WishlistStatusView(BaseAPIView, WishlistMixin):
    """
    Get wishlist status for products
    """

    def get(self, request):
        """Get wishlist status for multiple products"""
        try:
            product_ids = request.GET.getlist('product_ids[]')
            if not product_ids:
                return self.error_response(_('معرفات المنتجات مطلوبة'))

            # Convert to integers and validate
            try:
                product_ids = [int(pid) for pid in product_ids]
            except (ValueError, TypeError):
                return self.error_response(_('معرفات المنتجات غير صحيحة'))

            # Get wishlist status for products
            wishlist_items = Wishlist.objects.filter(
                user=request.user,
                product_id__in=product_ids
            ).values_list('product_id', flat=True)

            status_data = {}
            for product_id in product_ids:
                status_data[str(product_id)] = product_id in wishlist_items

            return self.success_response({
                'wishlist_status': status_data,
                'wishlist_count': self.get_user_wishlist_count(request.user)
            })

        except Exception as e:
            logger.error(f"Error getting wishlist status: {e}")
            return self.error_response(_('حدث خطأ في جلب البيانات'), 500)


@method_decorator(login_required, name='dispatch')
class WishlistProductsView(BaseAPIView, WishlistMixin):
    """
    Get wishlist products as JSON (for AJAX requests)
    """

    def get(self, request):
        """Get wishlist products"""
        try:
            wishlist_items = Wishlist.objects.filter(
                user=request.user
            ).select_related(
                'product__category',
                'product__brand'
            ).prefetch_related(
                'product__images'
            ).order_by('-created_at')

            # Pagination
            page = request.GET.get('page', 1)
            page_size = int(request.GET.get('page_size', 12))

            paginator = Paginator(wishlist_items, page_size)
            try:
                wishlist_page = paginator.page(page)
            except PageNotAnInteger:
                wishlist_page = paginator.page(1)
            except EmptyPage:
                wishlist_page = paginator.page(paginator.num_pages)

            # Serialize products
            products_data = []
            for wishlist_item in wishlist_page:
                product = wishlist_item.product
                primary_image = product.images.filter(is_primary=True).first()
                if not primary_image:
                    primary_image = product.images.first()

                products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'slug': product.slug,
                    'price': str(product.current_price),
                    'base_price': str(product.base_price),
                    'has_discount': product.has_discount,
                    'discount_percentage': product.discount_percentage,
                    'in_stock': product.in_stock,
                    'image': primary_image.image.url if primary_image else '/static/images/no-image.png',
                    'url': product.get_absolute_url(),
                    'category': product.category.name if product.category else '',
                    'brand': product.brand.name if product.brand else '',
                    'added_at': wishlist_item.created_at.isoformat()
                })

            return self.success_response({
                'products': products_data,
                'pagination': {
                    'current_page': wishlist_page.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': wishlist_page.has_next(),
                    'has_previous': wishlist_page.has_previous()
                }
            })

        except Exception as e:
            logger.error(f"Error getting wishlist products: {e}")
            return self.error_response(_('حدث خطأ في جلب المنتجات'), 500)


# Legacy function-based views for backward compatibility
@login_required
def wishlist_view(request):
    """Legacy function view for wishlist"""
    view = WishlistView.as_view()
    return view(request)


@login_required
@require_http_methods(["POST"])
def add_to_wishlist(request, product_id):
    """Legacy function view for adding to wishlist"""
    view = AddToWishlistView()
    view.request = request
    return view.post(request, product_id)


@login_required
@require_http_methods(["POST"])
def remove_from_wishlist(request, product_id):
    """Legacy function view for removing from wishlist"""
    view = RemoveFromWishlistView()
    view.request = request
    return view.post(request, product_id)


@login_required
@require_http_methods(["POST"])
def toggle_wishlist(request, product_id):
    """Legacy function view for toggling wishlist"""
    view = ToggleWishlistView()
    view.request = request
    return view.post(request, product_id)