from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Avg, Count, Min, Max, F, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    Product, Category, Brand, ProductImage, ProductVariant,
    ProductReview, Tag, Wishlist, ProductComparison
)
from .forms import ProductReviewForm, ProductFilterForm
from cart.models import Cart


class ProductListView(ListView):
    """
    عرض قائمة المنتجات مع دعم الفلترة والترتيب المتقدم
    """
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        # Base queryset with optimizations
        queryset = Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related(
            'category', 'brand', 'created_by'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(is_primary=True)),
            'tags',
            'reviews'
        ).annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )

        # Category filter
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            # Include subcategories
            categories = [category] + category.get_descendants()
            queryset = queryset.filter(category__in=categories)

        # Search query
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(name_en__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(description_en__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()

        # Filters
        filters = self.get_filters()

        # Brand filter
        brand_ids = filters.get('brands', [])
        if brand_ids:
            queryset = queryset.filter(brand__id__in=brand_ids)

        # Price range filter
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        # Feature filters
        if filters.get('is_new'):
            queryset = queryset.filter(is_new=True)
        if filters.get('is_featured'):
            queryset = queryset.filter(is_featured=True)
        if filters.get('on_sale'):
            # Products with active discounts
            now = timezone.now()
            queryset = queryset.filter(
                Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
            ).filter(
                Q(discount_start__isnull=True) | Q(discount_start__lte=now)
            ).filter(
                Q(discount_end__isnull=True) | Q(discount_end__gte=now)
            )
        if filters.get('in_stock'):
            queryset = queryset.filter(
                Q(track_inventory=False, stock_status='in_stock') |
                Q(track_inventory=True, stock_quantity__gt=0)
            )

        # Tag filter
        tag_ids = filters.get('tags', [])
        if tag_ids:
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()

        # Rating filter
        min_rating = filters.get('min_rating')
        if min_rating:
            queryset = queryset.filter(avg_rating__gte=min_rating)

        # Sorting
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'price_low':
            queryset = queryset.order_by('base_price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-base_price')
        elif sort_by == 'name_az':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_za':
            queryset = queryset.order_by('-name')
        elif sort_by == 'best_selling':
            queryset = queryset.order_by('-sales_count')
        elif sort_by == 'most_viewed':
            queryset = queryset.order_by('-views_count')
        elif sort_by == 'top_rated':
            queryset = queryset.order_by('-avg_rating', '-review_count')

        return queryset

    def get_filters(self):
        """Extract and validate filters from request"""
        filters = {}

        # Brands
        brands = self.request.GET.getlist('brand')
        if brands:
            filters['brands'] = [int(b) for b in brands if b.isdigit()]

        # Price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price and min_price.replace('.', '').isdigit():
            filters['min_price'] = Decimal(min_price)
        if max_price and max_price.replace('.', '').isdigit():
            filters['max_price'] = Decimal(max_price)

        # Features
        filters['is_new'] = self.request.GET.get('is_new') == '1'
        filters['is_featured'] = self.request.GET.get('is_featured') == '1'
        filters['on_sale'] = self.request.GET.get('on_sale') == '1'
        filters['in_stock'] = self.request.GET.get('in_stock') == '1'

        # Tags
        tags = self.request.GET.getlist('tag')
        if tags:
            filters['tags'] = [int(t) for t in tags if t.isdigit()]

        # Rating
        min_rating = self.request.GET.get('min_rating')
        if min_rating and min_rating.isdigit():
            filters['min_rating'] = int(min_rating)

        return filters

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Category context
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['category'] = get_object_or_404(Category, slug=category_slug)
            context['subcategories'] = context['category'].children.filter(is_active=True)
            context['breadcrumbs'] = self.get_breadcrumbs(context['category'])
        else:
            context['category'] = None
            context['subcategories'] = Category.objects.filter(parent=None, is_active=True)

        # Filter options
        context['brands'] = Brand.objects.filter(
            is_active=True,
            products__is_active=True,
            products__status='published'
        ).annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        ).filter(product_count__gt=0).order_by('name')

        # Price range for filters
        price_stats = self.get_queryset().aggregate(
            min_price=Min('base_price'),
            max_price=Max('base_price')
        )
        context['price_range'] = {
            'min': price_stats['min_price'] or 0,
            'max': price_stats['max_price'] or 1000
        }

        # Popular tags
        context['popular_tags'] = Tag.objects.annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        ).filter(product_count__gt=0).order_by('-product_count')[:20]

        # Active filters for display
        context['active_filters'] = self.get_active_filters()

        # Search query
        context['search_query'] = self.request.GET.get('q', '')

        # View type (grid/list)
        context['view_type'] = self.request.GET.get('view', 'grid')

        # Sort option
        context['sort_by'] = self.request.GET.get('sort', 'newest')

        # Results count
        context['total_count'] = self.get_queryset().count()

        return context

    def get_breadcrumbs(self, category):
        """Generate breadcrumbs for category"""
        breadcrumbs = []
        ancestors = category.get_ancestors()

        for ancestor in ancestors:
            breadcrumbs.append({
                'name': ancestor.name,
                'url': ancestor.get_absolute_url()
            })

        breadcrumbs.append({
            'name': category.name,
            'url': None  # Current page
        })

        return breadcrumbs

    def get_active_filters(self):
        """Get active filters for display"""
        filters = []

        # Brand filters
        brand_ids = self.request.GET.getlist('brand')
        if brand_ids:
            brands = Brand.objects.filter(id__in=brand_ids)
            for brand in brands:
                filters.append({
                    'type': 'brand',
                    'label': _('العلامة التجارية'),
                    'value': str(brand.id),
                    'display': brand.name
                })

        # Price filters
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price or max_price:
            price_display = []
            if min_price:
                price_display.append(f"من {min_price}")
            if max_price:
                price_display.append(f"إلى {max_price}")
            filters.append({
                'type': 'price',
                'label': _('السعر'),
                'value': 'price',
                'display': ' '.join(price_display)
            })

        # Feature filters
        if self.request.GET.get('is_new') == '1':
            filters.append({
                'type': 'is_new',
                'label': _('الحالة'),
                'value': '1',
                'display': _('منتجات جديدة')
            })

        if self.request.GET.get('on_sale') == '1':
            filters.append({
                'type': 'on_sale',
                'label': _('العروض'),
                'value': '1',
                'display': _('منتجات مخفضة')
            })

        return filters


class ProductDetailView(DetailView):
    """
    عرض تفاصيل المنتج
    """
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related(
            'category', 'brand', 'created_by'
        ).prefetch_related(
            'images',
            'tags',
            'variants',
            'related_products',
            Prefetch('reviews',
                queryset=ProductReview.objects.filter(is_approved=True).select_related('user')
            )
        )

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increment view count
        self.object.increment_views()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Breadcrumbs
        context['breadcrumbs'] = self.get_breadcrumbs(product)

        # Reviews
        reviews = product.reviews.filter(is_approved=True)
        context['reviews'] = reviews[:5]  # Latest 5 reviews
        context['total_reviews'] = reviews.count()
        context['rating_breakdown'] = self.get_rating_breakdown(reviews)

        # Review form
        context['can_review'] = product.can_review(self.request.user)
        if context['can_review']:
            context['review_form'] = ProductReviewForm()

        # Related products
        context['related_products'] = self.get_related_products(product)

        # Recently viewed products
        context['recently_viewed'] = self.get_recently_viewed(product)

        # Product variants
        context['variants'] = product.variants.filter(is_active=True)

        # Check if in wishlist
        if self.request.user.is_authenticated:
            context['in_wishlist'] = Wishlist.objects.filter(
                user=self.request.user,
                product=product
            ).exists()

        # Specifications
        context['specifications'] = product.specifications or {}

        return context

    def get_breadcrumbs(self, product):
        """Generate breadcrumbs"""
        breadcrumbs = []

        # Category breadcrumbs
        for ancestor in product.category.get_ancestors():
            breadcrumbs.append({
                'name': ancestor.name,
                'url': ancestor.get_absolute_url()
            })

        breadcrumbs.append({
            'name': product.category.name,
            'url': product.category.get_absolute_url()
        })

        breadcrumbs.append({
            'name': product.name,
            'url': None
        })

        return breadcrumbs

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

    def get_related_products(self, product):
        """Get related products"""
        # Manual related products
        related = product.related_products.filter(
            is_active=True,
            status='published'
        )[:4]

        if related.count() < 4:
            # Auto-suggest from same category
            auto_related = Product.objects.filter(
                category=product.category,
                is_active=True,
                status='published'
            ).exclude(id=product.id).order_by('-sales_count')[:4-related.count()]

            related = list(related) + list(auto_related)

        return related

    def get_recently_viewed(self, product):
        """Get recently viewed products from session"""
        session_key = 'recently_viewed'
        recently_viewed = self.request.session.get(session_key, [])

        # Add current product
        if product.id not in recently_viewed:
            recently_viewed.insert(0, product.id)
            recently_viewed = recently_viewed[:5]  # Keep only 5
            self.request.session[session_key] = recently_viewed

        # Get products
        if len(recently_viewed) > 1:
            return Product.objects.filter(
                id__in=recently_viewed,
                is_active=True,
                status='published'
            ).exclude(id=product.id)[:4]

        return []


class CategoryListView(ListView):
    """
    عرض قائمة الفئات
    """
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(
            parent=None,
            is_active=True
        ).prefetch_related(
            Prefetch('children', queryset=Category.objects.filter(is_active=True))
        ).annotate(
            total_products=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        ).order_by('order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Featured categories
        context['featured_categories'] = Category.objects.filter(
            is_featured=True,
            is_active=True
        ).order_by('order')[:6]

        return context


@require_http_methods(["GET"])
def search_suggestions(request):
    """
    API endpoint للحصول على اقتراحات البحث
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'suggestions': []})

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

    suggestions = []

    # Add products
    for product in products:
        suggestions.append({
            'type': 'product',
            'name': product['name'],
            'url': reverse('products:product_detail', kwargs={'slug': product['slug']})
        })

    # Add categories
    for category in categories:
        suggestions.append({
            'type': 'category',
            'name': category['name'],
            'url': reverse('products:category_products', kwargs={'category_slug': category['slug']})
        })

    # Add brands
    for brand in brands:
        suggestions.append({
            'type': 'brand',
            'name': brand['name'],
            'url': f"{reverse('products:product_list')}?brand={brand['slug']}"
        })

    return JsonResponse({'suggestions': suggestions})


@require_http_methods(["GET"])
def product_quick_view(request, product_id):
    """
    API endpoint للعرض السريع للمنتج
    """
    try:
        product = Product.objects.get(
            id=product_id,
            is_active=True,
            status='published'
        )

        # Get primary image
        primary_image = product.images.filter(is_primary=True).first()
        if not primary_image:
            primary_image = product.images.first()

        data = {
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': str(product.current_price),
            'base_price': str(product.base_price),
            'has_discount': product.has_discount,
            'discount_percentage': product.discount_percentage,
            'short_description': product.short_description,
            'in_stock': product.in_stock,
            'stock_quantity': product.stock_quantity if product.track_inventory else None,
            'image': primary_image.image.url if primary_image else '/static/images/no-image.png',
            'url': product.get_absolute_url(),
            'rating': float(product.rating) if product.rating else 0,
            'review_count': product.review_count,
            'category': {
                'name': product.category.name,
                'url': product.category.get_absolute_url()
            }
        }

        return JsonResponse(data)

    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def add_to_wishlist(request, product_id):
    """
    إضافة منتج إلى قائمة الأمنيات
    """
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:
            message = _('تمت إضافة المنتج إلى قائمة الأمنيات')
            status = 'added'
        else:
            message = _('المنتج موجود بالفعل في قائمة الأمنيات')
            status = 'exists'

        return JsonResponse({
            'success': True,
            'status': status,
            'message': str(message),
            'wishlist_count': request.user.wishlists.count()
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': str(_('المنتج غير موجود'))
        }, status=404)


@login_required
@require_http_methods(["POST"])
def remove_from_wishlist(request, product_id):
    """
    إزالة منتج من قائمة الأمنيات
    """
    try:
        wishlist = Wishlist.objects.get(
            user=request.user,
            product_id=product_id
        )
        wishlist.delete()

        return JsonResponse({
            'success': True,
            'message': str(_('تمت إزالة المنتج من قائمة الأمنيات')),
            'wishlist_count': request.user.wishlists.count()
        })

    except Wishlist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': str(_('المنتج غير موجود في قائمة الأمنيات'))
        }, status=404)


@login_required
def wishlist_view(request):
    """
    عرض قائمة الأمنيات
    """
    wishlists = Wishlist.objects.filter(
        user=request.user
    ).select_related(
        'product__category',
        'product__brand'
    ).prefetch_related(
        'product__images'
    )

    context = {
        'wishlists': wishlists,
        'title': _('قائمة الأمنيات')
    }

    return render(request, 'products/wishlist.html', context)


@require_http_methods(["POST"])
def add_to_comparison(request):
    """
    إضافة منتج للمقارنة
    """
    product_id = request.POST.get('product_id')
    session_key = request.session.session_key

    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    try:
        product = Product.objects.get(id=product_id, is_active=True)

        # Get or create comparison
        comparison, created = ProductComparison.objects.get_or_create(
            session_key=session_key
        )

        # Check limit (max 4 products)
        if comparison.products.count() >= 4:
            return JsonResponse({
                'success': False,
                'message': str(_('يمكن مقارنة 4 منتجات كحد أقصى'))
            })

        # Add product
        comparison.products.add(product)

        return JsonResponse({
            'success': True,
            'message': str(_('تمت إضافة المنتج للمقارنة')),
            'comparison_count': comparison.products.count()
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': str(_('المنتج غير موجود'))
        }, status=404)


def comparison_view(request):
    """
    عرض صفحة المقارنة
    """
    session_key = request.session.session_key

    if not session_key:
        products = []
    else:
        try:
            comparison = ProductComparison.objects.get(session_key=session_key)
            products = comparison.products.all()
        except ProductComparison.DoesNotExist:
            products = []

    # Get product IDs from URL if provided
    product_ids = request.GET.getlist('id')
    if product_ids:
        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            status='published'
        )[:4]

    context = {
        'products': products,
        'title': _('مقارنة المنتجات')
    }

    return render(request, 'products/comparison.html', context)


@login_required
@require_http_methods(["POST"])
def submit_review(request, product_id):
    """
    إرسال تقييم للمنتج
    """
    try:
        product = Product.objects.get(id=product_id)

        # Check if user can review
        if not product.can_review(request.user):
            return JsonResponse({
                'success': False,
                'message': str(_('يجب شراء المنتج أولاً لتتمكن من تقييمه'))
            })

        # Check if already reviewed
        if ProductReview.objects.filter(product=product, user=request.user).exists():
            return JsonResponse({
                'success': False,
                'message': str(_('لقد قمت بتقييم هذا المنتج مسبقاً'))
            })

        form = ProductReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

            messages.success(request, _('شكراً لك! سيتم نشر تقييمك بعد المراجعة'))

            return JsonResponse({
                'success': True,
                'message': str(_('تم إرسال التقييم بنجاح'))
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': str(_('المنتج غير موجود'))
        }, status=404)


def special_offers_view(request):
    """
    عرض العروض الخاصة
    """
    now = timezone.now()

    products = Product.objects.filter(
        is_active=True,
        status='published'
    ).filter(
        Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
    ).filter(
        Q(discount_start__isnull=True) | Q(discount_start__lte=now)
    ).filter(
        Q(discount_end__isnull=True) | Q(discount_end__gte=now)
    ).select_related(
        'category', 'brand'
    ).prefetch_related(
        'images'
    ).order_by('-discount_percentage', '-created_at')

    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'products': products,
        'title': _('العروض الخاصة'),
        'page_obj': products,
        'paginator': paginator
    }

    return render(request, 'products/special_offers.html', context)


class CategoryDetailView(DetailView):
    """
    عرض تفاصيل الفئة مع المنتجات
    """
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'

    def get_queryset(self):
        return Category.objects.filter(is_active=True).select_related('parent')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increment view count
        self.object.increment_views()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        # Get subcategories
        context['subcategories'] = category.children.filter(is_active=True).annotate(
            products_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        )

        # Get products in this category
        products = Product.objects.filter(
            category=category,
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images')

        # Apply sorting
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'price_low':
            products = products.order_by('base_price')
        elif sort_by == 'price_high':
            products = products.order_by('-base_price')
        elif sort_by == 'best_selling':
            products = products.order_by('-sales_count')
        elif sort_by == 'top_rated':
            products = products.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).order_by('-avg_rating')

        # Pagination
        paginator = Paginator(products, 12)
        page = self.request.GET.get('page')
        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

        context['products'] = products_page
        context['page_obj'] = products_page
        context['is_paginated'] = products_page.has_other_pages()

        # Get statistics
        context['products_count'] = category.products.filter(
            is_active=True, status='published'
        ).count()
        context['subcategories_count'] = context['subcategories'].count()

        # Get top brands in this category
        context['top_brands'] = Brand.objects.filter(
            products__category=category,
            products__is_active=True,
            products__status='published',
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(
                products__category=category,
                products__is_active=True,
                products__status='published'
            ))
        ).order_by('-product_count')[:10]

        context['brands_count'] = context['top_brands'].count()

        return context


def advanced_search_view(request):
    """
    صفحة البحث المتقدم
    """
    template_name = 'products/advanced_search.html'

    # Get categories with product counts
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        products_count=Count('products', filter=Q(
            products__is_active=True,
            products__status='published'
        ))
    ).filter(products_count__gt=0).order_by('level', 'name')

    # Get brands with product counts
    brands = Brand.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(
            products__is_active=True,
            products__status='published'
        ))
    ).filter(product_count__gt=0).order_by('name')

    # Get recent searches from session
    recent_searches = request.session.get('recent_searches', [])[:5]

    # Get saved searches for logged in users
    saved_searches = []
    if request.user.is_authenticated:
        # This would require a SavedSearch model
        pass

    # Process search if query exists
    products = None
    if request.GET:
        products_qs = Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images')

        # Apply filters
        q = request.GET.get('q', '').strip()
        if q:
            products_qs = products_qs.filter(
                Q(name__icontains=q) |
                Q(name_en__icontains=q) |
                Q(description__icontains=q) |
                Q(sku__icontains=q) |
                Q(tags__name__icontains=q)
            ).distinct()

            # Save to recent searches
            if q not in recent_searches:
                recent_searches.insert(0, q)
                recent_searches = recent_searches[:10]
                request.session['recent_searches'] = recent_searches

        # Category filter
        category_ids = request.GET.getlist('category')
        if category_ids:
            products_qs = products_qs.filter(category__id__in=category_ids)

        # Brand filter
        brand_ids = request.GET.getlist('brand')
        if brand_ids:
            products_qs = products_qs.filter(brand__id__in=brand_ids)

        # Price range
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            products_qs = products_qs.filter(base_price__gte=min_price)
        if max_price:
            products_qs = products_qs.filter(base_price__lte=max_price)

        # Additional filters
        if request.GET.get('on_sale'):
            now = timezone.now()
            products_qs = products_qs.filter(
                Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
            ).filter(
                Q(discount_start__isnull=True) | Q(discount_start__lte=now)
            ).filter(
                Q(discount_end__isnull=True) | Q(discount_end__gte=now)
            )

        if request.GET.get('in_stock'):
            products_qs = products_qs.filter(
                Q(track_inventory=False, stock_status='in_stock') |
                Q(track_inventory=True, stock_quantity__gt=0)
            )

        if request.GET.get('is_new'):
            products_qs = products_qs.filter(is_new=True)

        if request.GET.get('is_featured'):
            products_qs = products_qs.filter(is_featured=True)

        # Rating filter
        min_rating = request.GET.get('min_rating')
        if min_rating:
            products_qs = products_qs.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).filter(avg_rating__gte=min_rating)

        # Sorting
        sort_by = request.GET.get('sort', 'relevance')
        if sort_by == 'newest':
            products_qs = products_qs.order_by('-created_at')
        elif sort_by == 'price_low':
            products_qs = products_qs.order_by('base_price')
        elif sort_by == 'price_high':
            products_qs = products_qs.order_by('-base_price')
        elif sort_by == 'best_selling':
            products_qs = products_qs.order_by('-sales_count')
        elif sort_by == 'top_rated':
            products_qs = products_qs.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).order_by('-avg_rating')

        # Pagination
        paginator = Paginator(products_qs, 12)
        page = request.GET.get('page')
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

    context = {
        'categories': categories,
        'brands': brands,
        'recent_searches': recent_searches,
        'saved_searches': saved_searches,
        'products': products,
        'page_obj': products,
        'paginator': paginator if products else None,
        'is_paginated': products.has_other_pages() if products else False,
    }

    return render(request, template_name, context)


@require_http_methods(["POST"])
def increment_category_views(request, category_id):
    """
    API endpoint لزيادة عدد مشاهدات الفئة
    """
    try:
        category = Category.objects.get(id=category_id)
        category.increment_views()
        return JsonResponse({'success': True})
    except Category.DoesNotExist:
        return JsonResponse({'success': False}, status=404)


@login_required
@require_http_methods(["POST"])
def toggle_wishlist(request, product_id):
    """
    تبديل حالة المنتج في قائمة الأمنيات
    """
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            wishlist.delete()
            in_wishlist = False
            message = _('تمت إزالة المنتج من قائمة الأمنيات')
        else:
            in_wishlist = True
            message = _('تمت إضافة المنتج إلى قائمة الأمنيات')

        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist,
            'message': str(message),
            'wishlist_count': request.user.wishlists.count()
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': str(_('المنتج غير موجود'))
        }, status=404)


@require_http_methods(["GET"])
def export_products(request):
    """
    تصدير المنتجات إلى CSV
    """
    # Check permissions
    if not request.user.is_staff:
        return HttpResponseForbidden()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
    response.write('\ufeff'.encode('utf8'))  # BOM for Excel

    writer = csv.writer(response)

    # Header
    writer.writerow([
        'ID', 'اسم المنتج', 'Product Name', 'SKU', 'الفئة', 'العلامة التجارية',
        'السعر الأساسي', 'نسبة الخصم', 'السعر الحالي', 'المخزون', 'الحالة',
        'مميز', 'جديد', 'الأكثر مبيعاً', 'عدد المبيعات', 'عدد المشاهدات',
        'تاريخ الإنشاء'
    ])

    # Data
    products = Product.objects.all().select_related('category', 'brand')

    for product in products:
        writer.writerow([
            product.id,
            product.name,
            product.name_en,
            product.sku,
            product.category.name if product.category else '',
            product.brand.name if product.brand else '',
            product.base_price,
            product.discount_percentage,
            product.current_price,
            product.stock_quantity,
            product.get_status_display(),
            'نعم' if product.is_featured else 'لا',
            'نعم' if product.is_new else 'لا',
            'نعم' if product.is_best_seller else 'لا',
            product.sales_count,
            product.views_count,
            product.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    return response


@require_http_methods(["GET"])
def get_variant_details(request, variant_id):
    """
    الحصول على تفاصيل متغير المنتج
    """
    try:
        variant = ProductVariant.objects.get(id=variant_id, is_active=True)

        data = {
            'id': variant.id,
            'name': variant.name,
            'sku': variant.sku,
            'price': str(variant.current_price),
            'stock_quantity': variant.stock_quantity,
            'available_quantity': variant.available_quantity,
            'in_stock': variant.is_in_stock,
            'attributes': variant.display_attributes,
            'images': [
                {
                    'url': img.image.url,
                    'alt': img.alt_text
                } for img in variant.get_images()
            ]
        }

        return JsonResponse(data)

    except ProductVariant.DoesNotExist:
        return JsonResponse({'error': 'Variant not found'}, status=404)


@require_http_methods(["POST"])
def report_review(request, review_id):
    """
    الإبلاغ عن مراجعة مسيئة
    """
    try:
        review = ProductReview.objects.get(id=review_id, is_approved=True)

        # Create report (requires ReviewReport model)
        reason = request.POST.get('reason', 'inappropriate')
        description = request.POST.get('description', '')

        # For now, just mark the review for moderation
        review.is_approved = False
        review.save()

        messages.warning(request, _('تم الإبلاغ عن المراجعة وسيتم مراجعتها'))

        return JsonResponse({
            'success': True,
            'message': str(_('شكراً لك. سيتم مراجعة البلاغ'))
        })

    except ProductReview.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': str(_('المراجعة غير موجودة'))
        }, status=404)


@require_http_methods(["POST"])
def vote_review_helpful(request, review_id):
    """
    التصويت على مراجعة كمفيدة أو غير مفيدة
    """
    try:
        review = ProductReview.objects.get(id=review_id, is_approved=True)
        vote_type = request.POST.get('type', 'helpful')

        # Track user votes (requires ReviewVote model or session tracking)
        session_key = f'review_vote_{review_id}'

        if session_key in request.session:
            return JsonResponse({
                'success': False,
                'message': str(_('لقد قمت بالتصويت مسبقاً'))
            })

        if vote_type == 'helpful':
            review.helpful_count = F('helpful_count') + 1
        else:
            review.not_helpful_count = F('not_helpful_count') + 1

        review.save()
        review.refresh_from_db()

        # Mark as voted
        request.session[session_key] = True

        return JsonResponse({
            'success': True,
            'helpful_count': review.helpful_count,
            'not_helpful_count': review.not_helpful_count,
            'percentage': review.helpful_percentage
        })

    except ProductReview.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': str(_('المراجعة غير موجودة'))
        }, status=404)


def get_products_by_tag(request, tag_slug):
    """
    عرض المنتجات حسب الوسم
    """
    try:
        tag = Tag.objects.get(slug=tag_slug)
    except Tag.DoesNotExist:
        messages.error(request, _('الوسم غير موجود'))
        return redirect('products:product_list')

    products = Product.objects.filter(
        tags=tag,
        is_active=True,
        status='published'
    ).select_related('category', 'brand').prefetch_related('images')

    # Apply filters and sorting similar to ProductListView
    # ... (same filtering logic)

    paginator = Paginator(products, 12)
    page = request.GET.get('page')

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    context = {
        'tag': tag,
        'products': products_page,
        'page_obj': products_page,
        'paginator': paginator,
    }

    return render(request, 'products/tag_products.html', context)


def product_360_view(request, product_id):
    """
    عرض 360 درجة للمنتج
    """
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        images_360 = product.images.filter(is_360=True).order_by('order')

        if not images_360.exists():
            return JsonResponse({
                'error': 'No 360 images available'
            }, status=404)

        data = {
            'product_name': product.name,
            'images': [
                {
                    'url': img.image.url,
                    'order': img.order
                } for img in images_360
            ]
        }

        return JsonResponse(data)

    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)