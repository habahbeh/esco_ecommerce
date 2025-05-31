# File: products/views/review_views.py
"""
Product review and rating views
Handles review submission, voting, and reporting
"""

from typing import Dict, Any, Optional
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.contrib import messages
from django.db.models import F, Q, Count, Avg
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
import logging

from .api_views import BaseAPIView
from .base_views import OptimizedQueryMixin, PaginationMixin
from ..models import Product, ProductReview
from ..forms import ProductReviewForm

logger = logging.getLogger(__name__)


class ReviewMixin:
    """Mixin for review operations"""

    def can_user_review(self, user, product) -> bool:
        """Check if user can review the product"""
        if not user.is_authenticated:
            return False

        # Check if user has purchased the product (implement based on your order system)
        # For now, return True for authenticated users
        return product.can_review(user)

    def has_user_reviewed(self, user, product) -> bool:
        """Check if user has already reviewed the product"""
        if not user.is_authenticated:
            return False

        return ProductReview.objects.filter(
            user=user,
            product=product
        ).exists()


@method_decorator(login_required, name='dispatch')
class ProductReviewListView(ListView, OptimizedQueryMixin, PaginationMixin):
    """
    Display reviews for a specific product
    """
    model = ProductReview
    template_name = 'products/product_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        """Get reviews for the product"""
        self.product = get_object_or_404(
            Product,
            slug=self.kwargs['product_slug'],
            is_active=True,
            status='published'
        )

        return ProductReview.objects.filter(
            product=self.product,
            is_approved=True
        ).select_related('user').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product

        # Review statistics
        reviews = self.get_queryset()
        context['total_reviews'] = reviews.count()
        context['avg_rating'] = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        context['rating_breakdown'] = self.get_rating_breakdown(reviews)

        # Filter options
        context['sort_by'] = self.request.GET.get('sort', 'newest')
        context['rating_filter'] = self.request.GET.get('rating')

        return context

    def get_rating_breakdown(self, reviews):
        """Calculate rating breakdown"""
        breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
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


@method_decorator(login_required, name='dispatch')
class SubmitReviewView(BaseAPIView, ReviewMixin):
    """
    Submit a product review via AJAX
    """

    def post(self, request, product_id):
        """Submit product review"""
        try:
            product = get_object_or_404(
                Product,
                id=product_id,
                is_active=True,
                status='published'
            )

            # Check if user can review
            if not self.can_user_review(request.user, product):
                return self.error_response(_('يجب شراء المنتج أولاً لتتمكن من تقييمه'))

            # Check if already reviewed
            if self.has_user_reviewed(request.user, product):
                return self.error_response(_('لقد قمت بتقييم هذا المنتج مسبقاً'))

            form = ProductReviewForm(request.POST, request.FILES)
            if form.is_valid():
                with transaction.atomic():
                    review = form.save(commit=False)
                    review.product = product
                    review.user = request.user
                    review.ip_address = self.get_client_ip(request)
                    review.save()

                    # Log the action
                    logger.info(f"User {request.user.id} submitted review for product {product.id}")

                    return self.success_response({
                        'message': str(_('تم إرسال التقييم بنجاح. سيتم نشره بعد المراجعة')),
                        'review_id': review.id,
                        'requires_approval': not review.is_approved
                    })
            else:
                return self.error_response(
                    _('يرجى تصحيح الأخطاء في النموذج'),
                    400,
                    {'errors': form.errors}
                )

        except Product.DoesNotExist:
            return self.error_response(_('المنتج غير موجود'), 404)
        except Exception as e:
            logger.error(f"Error submitting review: {e}")
            return self.error_response(_('حدث خطأ أثناء إرسال التقييم'), 500)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def error_response(self, message: str, status: int = 400, extra_data: Dict = None):
        """Enhanced error response for form validation"""
        response_data = {'success': False, 'message': message}
        if extra_data:
            response_data.update(extra_data)
        return self.json_response(response_data, status)


class VoteReviewHelpfulView(BaseAPIView):
    """
    Vote on review helpfulness
    """

    def post(self, request, review_id):
        """Vote on review"""
        try:
            review = get_object_or_404(
                ProductReview,
                id=review_id,
                is_approved=True
            )

            vote_type = request.POST.get('type', 'helpful')
            if vote_type not in ['helpful', 'not_helpful']:
                return self.error_response(_('نوع التصويت غير صحيح'))

            # Check if user has already voted (using session for anonymous users)
            session_key = f'review_vote_{review_id}'

            if request.user.is_authenticated:
                # For logged-in users, check database (implement ReviewVote model if needed)
                # For now, use session
                user_session_key = f'review_vote_{review_id}_user_{request.user.id}'
                if user_session_key in request.session:
                    return self.error_response(_('لقد قمت بالتصويت مسبقاً'))
                vote_session_key = user_session_key
            else:
                if session_key in request.session:
                    return self.error_response(_('لقد قمت بالتصويت مسبقاً'))
                vote_session_key = session_key

            with transaction.atomic():
                if vote_type == 'helpful':
                    review.helpful_count = F('helpful_count') + 1
                else:
                    review.not_helpful_count = F('not_helpful_count') + 1

                review.save(update_fields=[f'{vote_type}_count'])
                review.refresh_from_db()

                # Mark as voted
                request.session[vote_session_key] = True

                # Log the action
                user_id = request.user.id if request.user.is_authenticated else 'anonymous'
                logger.info(f"User {user_id} voted {vote_type} on review {review_id}")

                return self.success_response({
                    'helpful_count': review.helpful_count,
                    'not_helpful_count': review.not_helpful_count,
                    'total_votes': review.helpful_count + review.not_helpful_count,
                    'helpful_percentage': review.helpful_percentage
                })

        except ProductReview.DoesNotExist:
            return self.error_response(_('المراجعة غير موجودة'), 404)
        except Exception as e:
            logger.error(f"Error voting on review: {e}")
            return self.error_response(_('حدث خطأ أثناء التصويت'), 500)


class ReportReviewView(BaseAPIView):
    """
    Report inappropriate review
    """

    def post(self, request, review_id):
        """Report review"""
        try:
            review = get_object_or_404(
                ProductReview,
                id=review_id,
                is_approved=True
            )

            reason = request.POST.get('reason', 'inappropriate')
            description = request.POST.get('description', '').strip()

            # Valid reasons
            valid_reasons = [
                'inappropriate', 'spam', 'fake', 'offensive',
                'irrelevant', 'copyright', 'other'
            ]

            if reason not in valid_reasons:
                return self.error_response(_('سبب الإبلاغ غير صحيح'))

            # Check if already reported by this user/session
            session_key = f'review_report_{review_id}'
            if request.user.is_authenticated:
                user_session_key = f'review_report_{review_id}_user_{request.user.id}'
                if user_session_key in request.session:
                    return self.error_response(_('لقد قمت بالإبلاغ عن هذه المراجعة مسبقاً'))
                report_session_key = user_session_key
            else:
                if session_key in request.session:
                    return self.error_response(_('لقد قمت بالإبلاغ عن هذه المراجعة مسبقاً'))
                report_session_key = session_key

            with transaction.atomic():
                # Create report record (implement ReviewReport model if needed)
                # For now, just mark the review for moderation
                review.report_count = F('report_count') + 1
                review.save(update_fields=['report_count'])

                # If too many reports, auto-hide
                review.refresh_from_db()
                if review.report_count >= 5:  # Configurable threshold
                    review.is_approved = False
                    review.save(update_fields=['is_approved'])

                # Mark as reported
                request.session[report_session_key] = True

                # Log the action
                user_id = request.user.id if request.user.is_authenticated else 'anonymous'
                logger.warning(f"User {user_id} reported review {review_id} for {reason}: {description}")

                return self.success_response({
                    'message': str(_('شكراً لك. سيتم مراجعة البلاغ')),
                    'reported': True
                })

        except ProductReview.DoesNotExist:
            return self.error_response(_('المراجعة غير موجودة'), 404)
        except Exception as e:
            logger.error(f"Error reporting review: {e}")
            return self.error_response(_('حدث خطأ أثناء الإبلاغ'), 500)


@method_decorator(login_required, name='dispatch')
class UserReviewsView(ListView, PaginationMixin):
    """
    Display user's own reviews
    """
    model = ProductReview
    template_name = 'products/user_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        """Get user's reviews"""
        return ProductReview.objects.filter(
            user=self.request.user
        ).select_related('product').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # User review statistics
        reviews = self.get_queryset()
        context['total_reviews'] = reviews.count()
        context['approved_reviews'] = reviews.filter(is_approved=True).count()
        context['pending_reviews'] = reviews.filter(is_approved=False).count()
        context['avg_rating'] = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

        context['title'] = _('مراجعاتي')

        return context


@method_decorator(login_required, name='dispatch')
class EditReviewView(BaseAPIView, ReviewMixin):
    """
    Edit user's own review
    """

    def post(self, request, review_id):
        """Edit review"""
        try:
            review = get_object_or_404(
                ProductReview,
                id=review_id,
                user=request.user
            )

            # Check if review can be edited (e.g., within 24 hours)
            from django.utils import timezone
            from datetime import timedelta

            edit_deadline = review.created_at + timedelta(hours=24)
            if timezone.now() > edit_deadline:
                return self.error_response(_('انتهت مهلة تعديل المراجعة'))

            form = ProductReviewForm(request.POST, request.FILES, instance=review)
            if form.is_valid():
                with transaction.atomic():
                    updated_review = form.save(commit=False)
                    updated_review.is_approved = False  # Re-approve after edit
                    updated_review.updated_at = timezone.now()
                    updated_review.save()

                    # Log the action
                    logger.info(f"User {request.user.id} edited review {review_id}")

                    return self.success_response({
                        'message': str(_('تم تحديث المراجعة بنجاح')),
                        'review_id': review.id,
                        'requires_approval': True
                    })
            else:
                return self.error_response(
                    _('يرجى تصحيح الأخطاء في النموذج'),
                    400,
                    {'errors': form.errors}
                )

        except ProductReview.DoesNotExist:
            return self.error_response(_('المراجعة غير موجودة'), 404)
        except Exception as e:
            logger.error(f"Error editing review: {e}")
            return self.error_response(_('حدث خطأ أثناء التحديث'), 500)


@method_decorator(login_required, name='dispatch')
class DeleteReviewView(BaseAPIView):
    """
    Delete user's own review
    """

    def post(self, request, review_id):
        """Delete review"""
        try:
            review = get_object_or_404(
                ProductReview,
                id=review_id,
                user=request.user
            )

            product_name = review.product.name

            with transaction.atomic():
                review.delete()

                # Log the action
                logger.info(f"User {request.user.id} deleted review {review_id}")

                return self.success_response({
                    'message': str(_('تم حذف المراجعة بنجاح')),
                    'product_name': product_name
                })

        except ProductReview.DoesNotExist:
            return self.error_response(_('المراجعة غير موجودة'), 404)
        except Exception as e:
            logger.error(f"Error deleting review: {e}")
            return self.error_response(_('حدث خطأ أثناء الحذف'), 500)


# Legacy function-based views for backward compatibility
@login_required
@require_http_methods(["POST"])
def submit_review(request, product_id):
    """Legacy function view for submitting review"""
    view = SubmitReviewView()
    view.request = request
    return view.post(request, product_id)


@require_http_methods(["POST"])
def vote_review_helpful(request, review_id):
    """Legacy function view for voting on review"""
    view = VoteReviewHelpfulView()
    view.request = request
    return view.post(request, review_id)


@require_http_methods(["POST"])
def report_review(request, review_id):
    """Legacy function view for reporting review"""
    view = ReportReviewView()
    view.request = request
    return view.post(request, review_id)