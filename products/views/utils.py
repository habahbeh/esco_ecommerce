# File: products/views/utils.py
"""
Utility functions and classes for product views
Contains common helper functions, decorators, and utilities
"""

from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.translation import gettext as _
from django.db.models import QuerySet, Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def ajax_required(view_func: Callable) -> Callable:
    """
    Decorator to ensure the request is an AJAX request
    """

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': _('هذا الطلب يتطلب AJAX')
            }, status=400)
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def rate_limit(rate: str = '10/m'):
    """
    Simple rate limiting decorator
    Format: 'requests/period' where period can be 's', 'm', 'h', 'd'
    Example: '10/m' = 10 requests per minute
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            # Parse rate limit
            try:
                requests, period = rate.split('/')
                requests = int(requests)

                # Convert period to seconds
                period_seconds = {
                    's': 1,
                    'm': 60,
                    'h': 3600,
                    'd': 86400
                }.get(period, 60)

                # Create cache key based on IP and view
                client_ip = get_client_ip(request)
                cache_key = f'rate_limit:{view_func.__name__}:{client_ip}'

                # Check current count
                current_count = cache.get(cache_key, 0)

                if current_count >= requests:
                    return JsonResponse({
                        'success': False,
                        'error': _('تم تجاوز الحد المسموح من الطلبات')
                    }, status=429)

                # Increment counter
                cache.set(cache_key, current_count + 1, period_seconds)

            except (ValueError, AttributeError):
                # If rate parsing fails, proceed without rate limiting
                logger.warning(f"Invalid rate limit format: {rate}")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def cache_result(timeout: int = 300, key_prefix: str = None):
    """
    Decorator to cache view results
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            # Generate cache key
            cache_key_parts = [
                key_prefix or view_func.__name__,
                str(hash(frozenset(request.GET.items()))),
                str(hash(tuple(args))),
                str(hash(frozenset(kwargs.items())))
            ]
            cache_key = ':'.join(filter(None, cache_key_parts))

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute view and cache result
            result = view_func(request, *args, **kwargs)
            if hasattr(result, 'status_code') and result.status_code == 200:
                cache.set(cache_key, result, timeout)

            return result

        return _wrapped_view

    return decorator


def get_client_ip(request: HttpRequest) -> str:
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def validate_price(price: Union[str, Decimal, float]) -> Optional[Decimal]:
    """
    Validate and convert price to Decimal
    """
    if price is None or price == '':
        return None

    try:
        if isinstance(price, str):
            # Remove currency symbols and spaces
            price = re.sub(r'[^\d.,]', '', price)
            # Handle different decimal separators
            if ',' in price and '.' in price:
                # Assume comma is thousands separator
                price = price.replace(',', '')
            elif ',' in price:
                # Assume comma is decimal separator
                price = price.replace(',', '.')

        decimal_price = Decimal(str(price))

        # Validate range
        if decimal_price < 0:
            raise ValidationError(_('السعر لا يمكن أن يكون سالباً'))
        if decimal_price > 999999999:
            raise ValidationError(_('السعر كبير جداً'))

        return decimal_price

    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(_('صيغة السعر غير صحيحة'))


def validate_integer(value: Union[str, int], min_val: int = 0, max_val: int = None) -> Optional[int]:
    """
    Validate and convert integer value
    """
    if value is None or value == '':
        return None

    try:
        int_value = int(value)

        if int_value < min_val:
            raise ValidationError(f'القيمة يجب أن تكون أكبر من أو تساوي {min_val}')

        if max_val is not None and int_value > max_val:
            raise ValidationError(f'القيمة يجب أن تكون أصغر من أو تساوي {max_val}')

        return int_value

    except (ValueError, TypeError):
        raise ValidationError(_('صيغة الرقم غير صحيحة'))


def clean_search_query(query: str) -> str:
    """
    Clean and normalize search query
    """
    if not query:
        return ''

    # Remove extra whitespace
    query = re.sub(r'\s+', ' ', query.strip())

    # Remove special characters but keep Arabic and English letters, numbers
    query = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', query)

    # Remove very short words (less than 2 characters)
    words = [word for word in query.split() if len(word) >= 2]

    return ' '.join(words)


def build_search_filters(query: str, fields: List[str]) -> Q:
    """
    Build Django Q object for search across multiple fields
    """
    if not query or not fields:
        return Q()

    terms = clean_search_query(query).split()
    if not terms:
        return Q()

    main_query = Q()

    for term in terms:
        term_query = Q()
        for field in fields:
            term_query |= Q(**{f"{field}__icontains": term})
        main_query &= term_query

    return main_query


def paginate_queryset(queryset: QuerySet, request: HttpRequest,
                      per_page: int = 12) -> Dict[str, Any]:
    """
    Paginate queryset and return pagination data
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return {
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'page_range': get_page_range(paginator, page_obj.number)
    }


def get_page_range(paginator, current_page: int,
                   adjacent_pages: int = 2) -> List[int]:
    """
    Get smart page range for pagination
    """
    start_page = max(current_page - adjacent_pages, 1)
    end_page = min(current_page + adjacent_pages, paginator.num_pages)

    return list(range(start_page, end_page + 1))


def format_currency(amount: Union[Decimal, float, int],
                    currency: str = 'SAR') -> str:
    """
    Format currency amount for display
    """
    try:
        if isinstance(amount, (Decimal, float)):
            if amount == int(amount):
                formatted = f"{int(amount):,}"
            else:
                formatted = f"{amount:,.2f}"
        else:
            formatted = f"{int(amount):,}"

        currency_symbols = {
            'SAR': 'ر.س',
            'USD': '$',
            'EUR': '€',
            'GBP': '£'
        }

        symbol = currency_symbols.get(currency, currency)
        return f"{formatted} {symbol}"

    except (ValueError, TypeError):
        return str(amount)


def calculate_discount(base_price: Decimal, discount_percentage: float = None,
                       discount_amount: Decimal = None) -> Dict[str, Decimal]:
    """
    Calculate discount and final price
    """
    if not base_price:
        return {'discount': Decimal('0'), 'final_price': Decimal('0')}

    discount = Decimal('0')

    if discount_percentage and discount_percentage > 0:
        discount = base_price * (Decimal(str(discount_percentage)) / 100)
    elif discount_amount and discount_amount > 0:
        discount = min(discount_amount, base_price)

    final_price = max(base_price - discount, Decimal('0'))

    return {
        'discount': discount,
        'final_price': final_price,
        'savings_percentage': (discount / base_price * 100) if base_price > 0 else 0
    }


def get_stock_status(product) -> Dict[str, Any]:
    """
    Get comprehensive stock status for a product
    """
    if not product.track_inventory:
        return {
            'in_stock': product.stock_status == 'in_stock',
            'status': product.stock_status,
            'quantity': None,
            'availability': 'unlimited' if product.stock_status == 'in_stock' else 'out_of_stock'
        }

    quantity = product.stock_quantity or 0
    low_threshold = product.low_stock_threshold or 0

    if quantity <= 0:
        status = 'out_of_stock'
        availability = 'out_of_stock'
    elif quantity <= low_threshold:
        status = 'low_stock'
        availability = 'low_stock'
    else:
        status = 'in_stock'
        availability = 'in_stock'

    return {
        'in_stock': quantity > 0,
        'status': status,
        'quantity': quantity,
        'availability': availability,
        'is_low_stock': quantity <= low_threshold and quantity > 0
    }


def generate_sku(name: str, category_code: str = None,
                 sequence: int = None) -> str:
    """
    Generate SKU for product
    """
    # Clean name and get first letters
    name_clean = re.sub(r'[^\w\s]', '', name).strip()
    name_parts = name_clean.split()[:3]  # First 3 words
    name_code = ''.join([part[:2].upper() for part in name_parts])

    # Add category code if provided
    if category_code:
        name_code = f"{category_code}-{name_code}"

    # Add sequence number
    if sequence:
        name_code = f"{name_code}-{sequence:04d}"
    else:
        # Use timestamp as fallback
        timestamp = timezone.now().strftime('%m%d%H%M')
        name_code = f"{name_code}-{timestamp}"

    return name_code


def validate_image_file(file) -> bool:
    """
    Validate uploaded image file
    """
    if not file:
        return False

    # Check file size (max 5MB)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError(_('حجم الصورة كبير جداً (الحد الأقصى 5 ميجابايت)'))

    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_extension = file.name.lower().split('.')[-1]
    if f'.{file_extension}' not in allowed_extensions:
        raise ValidationError(_('صيغة الصورة غير مدعومة'))

    return True


def get_breadcrumbs(obj, home_url: str = '/') -> List[Dict[str, str]]:
    """
    Generate breadcrumbs for an object
    """
    breadcrumbs = [
        {'name': _('الرئيسية'), 'url': home_url}
    ]

    # Handle different object types
    if hasattr(obj, 'category') and obj.category:
        # Product with category
        ancestors = obj.category.get_ancestors() if hasattr(obj.category, 'get_ancestors') else []
        for ancestor in ancestors:
            breadcrumbs.append({
                'name': ancestor.name,
                'url': getattr(ancestor, 'get_absolute_url', lambda: '#')()
            })

        breadcrumbs.append({
            'name': obj.category.name,
            'url': getattr(obj.category, 'get_absolute_url', lambda: '#')()
        })

    elif hasattr(obj, 'get_ancestors'):
        # Category with ancestors
        ancestors = obj.get_ancestors()
        for ancestor in ancestors:
            breadcrumbs.append({
                'name': ancestor.name,
                'url': getattr(ancestor, 'get_absolute_url', lambda: '#')()
            })

    # Add current object
    if hasattr(obj, 'name'):
        breadcrumbs.append({
            'name': obj.name,
            'url': None  # Current page
        })

    return breadcrumbs


def track_user_activity(request: HttpRequest, action: str,
                        object_id: int = None, object_type: str = None,
                        metadata: Dict = None):
    """
    Track user activity for analytics
    """
    try:
        activity_data = {
            'user_id': request.user.id if request.user.is_authenticated else None,
            'session_key': request.session.session_key,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'action': action,
            'object_id': object_id,
            'object_type': object_type,
            'metadata': metadata or {},
            'timestamp': timezone.now().isoformat()
        }

        # Store in cache for batch processing
        cache_key = f'user_activity:{request.session.session_key}:{timezone.now().timestamp()}'
        cache.set(cache_key, activity_data, 3600)  # 1 hour

        logger.info(f"User activity tracked: {action} by {activity_data['user_id'] or 'anonymous'}")

    except Exception as e:
        logger.warning(f"Failed to track user activity: {e}")


def get_popular_products(category=None, limit: int = 10) -> QuerySet:
    """
    Get popular products based on various metrics
    """
    from ..models import Product

    queryset = Product.objects.filter(
        is_active=True,
        status='published'
    )

    if category:
        queryset = queryset.filter(category=category)

    # Order by popularity metrics
    return queryset.order_by(
        '-sales_count',
        '-views_count',
        '-created_at'
    )[:limit]


def get_recommended_products(user=None, product=None, limit: int = 6) -> QuerySet:
    """
    Get recommended products for user or based on a product
    """
    from ..models import Product

    if product:
        # Product-based recommendations
        queryset = Product.objects.filter(
            is_active=True,
            status='published'
        ).exclude(id=product.id)

        # Same category products
        if product.category:
            queryset = queryset.filter(category=product.category)

        return queryset.order_by('-sales_count')[:limit]

    elif user and user.is_authenticated:
        # User-based recommendations (would require order history)
        # For now, return popular products
        return get_popular_products(limit=limit)

    # Default: popular products
    return get_popular_products(limit=limit)


class PerformanceMonitor:
    """
    Context manager for monitoring view performance
    """

    def __init__(self, view_name: str):
        self.view_name = view_name
        self.start_time = None

    def __enter__(self):
        self.start_time = timezone.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (timezone.now() - self.start_time).total_seconds()

            # Log slow views
            if duration > 2:  # 2 seconds threshold
                logger.warning(f"Slow view performance: {self.view_name} took {duration:.2f}s")

            # Store metrics for monitoring
            cache_key = f'view_performance:{self.view_name}:{timezone.now().date()}'
            performance_data = cache.get(cache_key, {
                'total_requests': 0,
                'total_time': 0,
                'max_time': 0,
                'min_time': float('inf')
            })

            performance_data['total_requests'] += 1
            performance_data['total_time'] += duration
            performance_data['max_time'] = max(performance_data['max_time'], duration)
            performance_data['min_time'] = min(performance_data['min_time'], duration)

            cache.set(cache_key, performance_data, 86400)  # 24 hours