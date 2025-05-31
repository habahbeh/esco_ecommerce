# File: products/views/search_views.py
"""
Search views for products
Handles search functionality, advanced search, and search analytics
"""

from typing import Dict, Any, List, Optional
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q, Count, Avg, Min, Max
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings
import logging
import re

from .base_views import BaseProductListView, CachedMixin, OptimizedQueryMixin
from ..models import Product, Category, Brand, Tag

logger = logging.getLogger(__name__)


class SearchMixin:
    """Mixin for search functionality"""

    def process_search_query(self, query: str) -> str:
        """Process and clean search query"""
        if not query:
            return ''

        # Clean and normalize query
        query = query.strip()

        # Remove special characters but keep Arabic and English letters, numbers, and spaces
        query = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', query)

        # Normalize multiple spaces
        query = re.sub(r'\s+', ' ', query).strip()

        return query

    def get_search_terms(self, query: str) -> List[str]:
        """Split query into search terms"""
        if not query:
            return []

        # Split by spaces and filter empty terms
        terms = [term.strip() for term in query.split() if term.strip()]

        # Remove very short terms (less than 2 characters)
        terms = [term for term in terms if len(term) >= 2]

        return terms

    def build_search_query(self, terms: List[str]) -> Q:
        """Build Django Q object for search"""
        if not terms:
            return Q()

        main_query = Q()

        for term in terms:
            term_query = (
                    Q(name__icontains=term) |
                    Q(name_en__icontains=term) |
                    Q(description__icontains=term) |
                    Q(description_en__icontains=term) |
                    Q(short_description__icontains=term) |
                    Q(sku__icontains=term) |
                    Q(tags__name__icontains=term) |
                    Q(category__name__icontains=term) |
                    Q(brand__name__icontains=term)
            )

            main_query &= term_query

        return main_query

    def save_search_query(self, request, query: str, results_count: int = 0):
        """Save search query to session and analytics"""
        if not query or len(query.strip()) < 2:
            return

        # Save to recent searches in session
        session_key = 'recent_searches'
        recent_searches = request.session.get(session_key, [])

        # Remove if already exists and add to beginning
        if query in recent_searches:
            recent_searches.remove(query)
        recent_searches.insert(0, query)

        # Keep only last 10 searches
        recent_searches = recent_searches[:10]
        request.session[session_key] = recent_searches

        # Log search for analytics (implement SearchLog model if needed)
        logger.info(f"Search query: '{query}' - Results: {results_count}")


class SearchView(BaseProductListView, SearchMixin):
    """
    Enhanced search view with auto-complete and suggestions
    """
    template_name = 'products/search_results.html'

    def get_queryset(self):
        """Get search results"""
        query = self.request.GET.get('q', '').strip()

        if not query:
            return Product.objects.none()

        # Process search query
        processed_query = self.process_search_query(query)
        search_terms = self.get_search_terms(processed_query)

        if not search_terms:
            return Product.objects.none()

        # Get base queryset
        queryset = self.get_optimized_product_queryset()

        # Apply search filter
        search_q = self.build_search_query(search_terms)
        queryset = queryset.filter(search_q).distinct()

        # Apply additional filters
        filters = self.get_filters_from_request()
        queryset = self.apply_filters(queryset, filters)

        # Apply sorting with search relevance
        queryset = self.apply_search_sorting(queryset, search_terms)

        return queryset

    def apply_search_sorting(self, queryset, search_terms):
        """Apply sorting with search relevance"""
        sort_by = self.request.GET.get('sort', 'relevance')

        if sort_by == 'relevance' and search_terms:
            # Simple relevance scoring
            # Prefer exact matches in name, then partial matches
            from django.db.models import Case, When, IntegerField, Value

            relevance_cases = []
            for i, term in enumerate(search_terms):
                # Exact name match gets highest score
                relevance_cases.append(
                    When(name__iexact=term, then=Value(100 - i))
                )
                # Name contains term gets medium score
                relevance_cases.append(
                    When(name__icontains=term, then=Value(50 - i))
                )
                # SKU match gets high score
                relevance_cases.append(
                    When(sku__icontains=term, then=Value(75 - i))
                )

            queryset = queryset.annotate(
                relevance_score=Case(
                    *relevance_cases,
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-relevance_score', '-created_at')
        else:
            # Use standard sorting
            queryset = self.apply_sorting(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        query = self.request.GET.get('q', '').strip()
        context['search_query'] = query

        if query:
            # Save search query
            results_count = self.get_queryset().count()
            self.save_search_query(self.request, query, results_count)

            # Search suggestions if no results
            if results_count == 0:
                context['search_suggestions'] = self.get_search_suggestions(query)

            # Popular searches
            context['popular_searches'] = self.get_popular_searches()

            context['results_count'] = results_count

        context['title'] = _('نتائج البحث')
        if query:
            context['title'] = f'{_("نتائج البحث عن")}: {query}'

        return context

    def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions for no results"""
        suggestions = []

        # Get similar product names
        similar_products = Product.objects.filter(
            Q(name__icontains=query[:3]) |  # First 3 characters
            Q(name_en__icontains=query[:3]),
            is_active=True,
            status='published'
        ).values_list('name', flat=True)[:5]

        suggestions.extend(similar_products)

        # Get similar categories
        similar_categories = Category.objects.filter(
            Q(name__icontains=query[:3]) |
            Q(name_en__icontains=query[:3]),
            is_active=True
        ).values_list('name', flat=True)[:3]

        suggestions.extend(similar_categories)

        return list(set(suggestions))[:5]

    def get_popular_searches(self) -> List[str]:
        """Get popular search terms"""
        # This would come from search analytics
        # For now, return some common searches
        return [
            _('هواتف ذكية'),
            _('لابتوب'),
            _('ساعات ذكية'),
            _('سماعات'),
            _('كاميرات')
        ]


class AdvancedSearchView(TemplateView, OptimizedQueryMixin, SearchMixin):
    """
    Advanced search page with detailed filters
    """
    template_name = 'products/advanced_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filter options
        context.update(self.get_advanced_search_options())

        # Get recent searches
        context['recent_searches'] = self.request.session.get('recent_searches', [])[:5]

        # Process search if query exists
        if self.request.GET:
            context['results'] = self.perform_advanced_search()

        context['title'] = _('البحث المتقدم')

        return context

    def get_advanced_search_options(self) -> Dict[str, Any]:
        """Get options for advanced search form"""
        # Cache these options
        cache_key = 'advanced_search_options'
        cached_options = getattr(self, '_cached_options', None)

        if cached_options is None:
            # Categories with hierarchy
            categories = Category.objects.filter(
                is_active=True
            ).annotate(
                products_count=Count(
                    'products',
                    filter=Q(
                        products__is_active=True,
                        products__status='published'
                    )
                )
            ).filter(products_count__gt=0).order_by('level', 'name')

            # Brands with product counts
            brands = Brand.objects.filter(
                is_active=True
            ).annotate(
                product_count=Count(
                    'products',
                    filter=Q(
                        products__is_active=True,
                        products__status='published'
                    )
                )
            ).filter(product_count__gt=0).order_by('name')

            # Price ranges
            price_stats = Product.objects.filter(
                is_active=True,
                status='published'
            ).aggregate(
                min_price=Min('base_price'),
                max_price=Max('base_price')
            )

            # Popular tags
            tags = Tag.objects.annotate(
                product_count=Count(
                    'products',
                    filter=Q(
                        products__is_active=True,
                        products__status='published'
                    )
                )
            ).filter(product_count__gt=0).order_by('-product_count')[:20]

            cached_options = {
                'categories': categories,
                'brands': brands,
                'tags': tags,
                'price_range': {
                    'min': float(price_stats['min_price'] or 0),
                    'max': float(price_stats['max_price'] or 1000),
                    'step': 10
                }
            }

            self._cached_options = cached_options

        return cached_options

    def perform_advanced_search(self):
        """Perform advanced search based on form data"""
        # Get base queryset
        queryset = Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images')

        # Text search
        query = self.request.GET.get('q', '').strip()
        if query:
            processed_query = self.process_search_query(query)
            search_terms = self.get_search_terms(processed_query)
            if search_terms:
                search_q = self.build_search_query(search_terms)
                queryset = queryset.filter(search_q).distinct()

        # Category filter
        category_ids = self.request.GET.getlist('category')
        if category_ids:
            try:
                category_ids = [int(cid) for cid in category_ids if cid.isdigit()]
                queryset = queryset.filter(category__id__in=category_ids)
            except (ValueError, TypeError):
                pass

        # Brand filter
        brand_ids = self.request.GET.getlist('brand')
        if brand_ids:
            try:
                brand_ids = [int(bid) for bid in brand_ids if bid.isdigit()]
                queryset = queryset.filter(brand__id__in=brand_ids)
            except (ValueError, TypeError):
                pass

        # Price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            try:
                queryset = queryset.filter(base_price__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                queryset = queryset.filter(base_price__lte=float(max_price))
            except (ValueError, TypeError):
                pass

        # Additional filters
        if self.request.GET.get('on_sale'):
            from django.utils import timezone
            now = timezone.now()
            queryset = queryset.filter(
                Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
            ).filter(
                Q(discount_start__isnull=True) | Q(discount_start__lte=now)
            ).filter(
                Q(discount_end__isnull=True) | Q(discount_end__gte=now)
            )

        if self.request.GET.get('in_stock'):
            queryset = queryset.filter(
                Q(track_inventory=False, stock_status='in_stock') |
                Q(track_inventory=True, stock_quantity__gt=0)
            )

        if self.request.GET.get('is_new'):
            queryset = queryset.filter(is_new=True)

        if self.request.GET.get('is_featured'):
            queryset = queryset.filter(is_featured=True)

        # Rating filter
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            try:
                min_rating = int(min_rating)
                queryset = queryset.annotate(
                    avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
                ).filter(avg_rating__gte=min_rating)
            except (ValueError, TypeError):
                pass

        # Tag filter
        tag_ids = self.request.GET.getlist('tag')
        if tag_ids:
            try:
                tag_ids = [int(tid) for tid in tag_ids if tid.isdigit()]
                queryset = queryset.filter(tags__id__in=tag_ids).distinct()
            except (ValueError, TypeError):
                pass

        # Sorting
        sort_by = self.request.GET.get('sort', 'relevance')
        if sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'price_low':
            queryset = queryset.order_by('base_price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-base_price')
        elif sort_by == 'best_selling':
            queryset = queryset.order_by('-sales_count')
        elif sort_by == 'top_rated':
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).order_by('-avg_rating')
        else:
            queryset = queryset.order_by('-created_at')

        # Pagination
        paginator = Paginator(queryset, 12)
        page = self.request.GET.get('page')

        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

        # Save search if there's a query
        if query:
            self.save_search_query(self.request, query, queryset.count())

        return {
            'products': products_page,
            'page_obj': products_page,
            'paginator': paginator,
            'is_paginated': products_page.has_other_pages(),
            'total_results': queryset.count()
        }


@method_decorator(cache_page(300), name='dispatch')  # Cache for 5 minutes
class SearchSuggestionsPageView(TemplateView):
    """
    Search suggestions page for SEO and user experience
    """
    template_name = 'products/search_suggestions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Popular categories
        context['popular_categories'] = Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(
                    products__is_active=True,
                    products__status='published'
                )
            )
        ).filter(product_count__gt=0).order_by('-product_count')[:12]

        # Popular brands
        context['popular_brands'] = Brand.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(
                    products__is_active=True,
                    products__status='published'
                )
            )
        ).filter(product_count__gt=0).order_by('-product_count')[:12]

        # Popular search terms (would come from analytics)
        context['popular_searches'] = [
            _('هواتف ذكية'),
            _('لابتوب'),
            _('ساعات ذكية'),
            _('سماعات'),
            _('كاميرات'),
            _('أجهزة منزلية'),
            _('ملابس'),
            _('أحذية'),
            _('إكسسوارات'),
            _('كتب'),
        ]

        context['title'] = _('اقتراحات البحث')

        return context


# Legacy function-based view for backward compatibility
def advanced_search_view(request):
    """Legacy function view for advanced search"""
    view = AdvancedSearchView.as_view()
    return view(request)