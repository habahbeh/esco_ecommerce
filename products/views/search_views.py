# File: products/views/search_views.py
"""
Search views for products
Handles search functionality, advanced search, and search analytics
"""

from typing import Dict, Any, List, Optional
from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q, Count, Avg, Min, Max, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page, never_cache
from django.http import JsonResponse
from django.conf import settings
import logging
import os
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
                    Q(short_description__icontains=term) |
                    Q(sku__icontains=term) |
                    Q(barcode__icontains=term) |
                    Q(variants__sku__icontains=term) |
                    Q(variants__name__icontains=term) |
                    Q(tags__name__icontains=term) |
                    Q(category__name__icontains=term) |
                    Q(category__name_en__icontains=term) |
                    Q(brand__name__icontains=term) |
                    Q(brand__name_en__icontains=term)
            )

            main_query &= term_query

        return main_query

    def save_search_query(self, request, query: str, results_count: int = 0):
        """Save search query to session and database"""
        if not query or len(query.strip()) < 2:
            return

        session_key = 'recent_searches'
        recent_searches = request.session.get(session_key, [])

        if query in recent_searches:
            recent_searches.remove(query)
        recent_searches.insert(0, query)

        recent_searches = recent_searches[:10]
        request.session[session_key] = recent_searches

        try:
            from ..models import SearchQuery
            obj, created = SearchQuery.objects.get_or_create(
                query=query.lower().strip(),
                defaults={'results_count': results_count}
            )
            if not created:
                obj.count = F('count') + 1
                obj.results_count = results_count
                obj.save(update_fields=['count', 'results_count', 'last_searched'])
        except Exception:
            pass


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
            # Use paginator count to avoid duplicate queryset evaluation
            paginator = context.get('paginator')
            results_count = paginator.count if paginator else 0
            self.save_search_query(self.request, query, results_count)

            # "Did you mean?" and search suggestions if no results
            if results_count == 0:
                context['search_suggestions'] = self.get_search_suggestions(query)
                try:
                    from ..search import SearchService
                    service = SearchService()
                    did_you_mean = service.did_you_mean(query)
                    if did_you_mean:
                        context['did_you_mean'] = did_you_mean
                except Exception:
                    pass

            # Popular searches
            context['popular_searches'] = self.get_popular_searches()

            # Recent searches from session
            context['recent_searches'] = self.request.session.get('recent_searches', [])[:5]

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
        """Get popular search terms from database"""
        try:
            from ..models import SearchQuery
            return list(
                SearchQuery.objects.filter(results_count__gt=0)
                .order_by('-count')
                .values_list('query', flat=True)[:8]
            )
        except Exception:
            return []


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
            if 'avg_rating' not in queryset.query.annotations:
                queryset = queryset.annotate(
                    avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
                )
            queryset = queryset.order_by('-avg_rating')
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

        total_results = paginator.count

        if query:
            self.save_search_query(self.request, query, total_results)

        return {
            'products': products_page,
            'page_obj': products_page,
            'paginator': paginator,
            'is_paginated': products_page.has_other_pages(),
            'total_results': total_results
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


class QuickSearchView(ListView, OptimizedQueryMixin):
    """
    البحث السريع - للبحث السريع في الرأس
    Quick search - for quick search in header
    """
    template_name = 'products/quick_search.html'
    context_object_name = 'products'
    paginate_by = 8

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()

        if not query:
            return Product.objects.none()

        return Product.objects.filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query) |
            Q(variants__sku__icontains=query) |
            Q(variants__name__icontains=query),
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images').distinct()[:20]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


@never_cache
def search_suggestions(request):
    """
    اقتراحات البحث عبر AJAX - يعطي اقتراحات سريعة للبحث
    AJAX search suggestions - provides quick search suggestions
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'suggestions': []})

    try:
        # الحصول على اللغة من الصفحة التي جاء منها الطلب
        current_lang = 'ar'
        referer = request.META.get('HTTP_REFERER', '')
        if '/en/' in referer:
            current_lang = 'en'
        lang_prefix = '/en' if current_lang == 'en' else ''

        # البحث في المنتجات
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query) |
            Q(sku__icontains=query) | Q(barcode__icontains=query) |
            Q(variants__sku__icontains=query) | Q(variants__name__icontains=query) |
            Q(category__name__icontains=query) | Q(category__name_en__icontains=query) |
            Q(brand__name__icontains=query) | Q(brand__name_en__icontains=query),
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images').distinct()[:5]

        # البحث في الفئات
        categories = Category.objects.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query),
            is_active=True
        )[:3]

        # البحث في العلامات التجارية
        brands = Brand.objects.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query),
            is_active=True
        )[:3]

        suggestions = []

        # إضافة المنتجات
        default_image = settings.STATIC_URL + 'images/no-image.png'

        for product in products:
            main_image_url = default_image
            all_images = list(product.images.all())
            if all_images:
                primary = next((img for img in all_images if img.is_primary), None)
                img = primary or all_images[0]
                if img and img.image:
                    try:
                        if os.path.isfile(img.image.path):
                            main_image_url = img.image.url
                    except Exception:
                        pass

            # السعر الحالي - فقط إذا كان مسموح بعرضه
            current_price = None
            if product.is_price_visible:
                if hasattr(product, 'current_price'):
                    current_price = f"{product.current_price:.2f}"
                elif hasattr(product, 'base_price'):
                    current_price = f"{product.base_price:.2f}"

            # إضافة language prefix للـ URL
            product_url = product.get_absolute_url() if hasattr(product, 'get_absolute_url') else '#'
            if product_url != '#' and not product_url.startswith(('/en/', '/ar/')):
                product_url = lang_prefix + product_url

            # Use English name if language is English and name_en exists
            product_title = product.name_en if current_lang == 'en' and product.name_en else product.name

            suggestions.append({
                'type': 'product',
                'title': product_title,
                'url': product_url,
                'image': main_image_url,
                'price': current_price,
                'sku': product.sku or '',
            })

        # إضافة الفئات
        for category in categories:
            try:
                category_url = category.get_absolute_url() if hasattr(category, 'get_absolute_url') else '#'
            except Exception:
                category_url = '#'
            if category_url != '#' and not category_url.startswith(('/en/', '/ar/')):
                category_url = lang_prefix + category_url

            # Use English name if language is English and name_en exists
            category_title = category.name_en if current_lang == 'en' and category.name_en else category.name

            suggestions.append({
                'type': 'category',
                'title': category_title,
                'url': category_url,
                'count': category.products.filter(
                    is_active=True,
                    status='published'
                ).count(),
            })

        # إضافة العلامات التجارية
        for brand in brands:
            brand_url = '#'
            try:
                if hasattr(brand, 'get_absolute_url'):
                    brand_url = brand.get_absolute_url()
            except Exception:
                pass
            if brand_url == '#' and hasattr(brand, 'slug'):
                brand_url = f'/products/brand/{brand.slug}/'

            if brand_url != '#' and not brand_url.startswith(('/en/', '/ar/')):
                brand_url = lang_prefix + brand_url

            # Use English name if language is English and name_en exists
            brand_title = brand.name_en if current_lang == 'en' and brand.name_en else brand.name

            suggestions.append({
                'type': 'brand',
                'title': brand_title,
                'url': brand_url,
                'count': brand.products.filter(
                    is_active=True,
                    status='published'
                ).count(),
            })

        return JsonResponse({'suggestions': suggestions})

    except Exception as e:
        logger.error(f"Error in search suggestions: {e}")
        return JsonResponse({'suggestions': []})


def quick_search_simple(request):
    """
    عرض بسيط للبحث السريع
    Simple quick search view
    """
    query = request.GET.get('q', '').strip()
    products = []

    if query and len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query) |
            Q(variants__sku__icontains=query) |
            Q(variants__name__icontains=query),
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images').distinct()[:10]

    return render(request, 'products/quick_search.html', {
        'query': query,
        'products': products,
        'results_count': len(products),
    })


def recent_popular_searches(request):
    """API endpoint for recent and popular searches (shown on search focus)"""
    recent = request.session.get('recent_searches', [])[:5]

    popular = []
    try:
        from ..models import SearchQuery
        popular = list(
            SearchQuery.objects.filter(results_count__gt=0)
            .order_by('-count')
            .values_list('query', flat=True)[:6]
        )
    except Exception:
        pass

    return JsonResponse({
        'recent': recent,
        'popular': popular,
    })


# أسماء الدوال للتوافق مع urls.py
advanced_search_view = AdvancedSearchView.as_view()