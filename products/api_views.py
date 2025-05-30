from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg, Count, F, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    Product, Category, Brand, ProductImage, ProductVariant,
    ProductReview, Tag, Wishlist, ProductComparison
)
from .serializers import (
    ProductSerializer, ProductDetailSerializer, ProductListSerializer,
    CategorySerializer, BrandSerializer, TagSerializer,
    ProductReviewSerializer, WishlistSerializer,
    ProductVariantSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet للمنتجات
    """
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_en', 'description', 'sku', 'barcode']
    ordering_fields = ['created_at', 'base_price', 'sales_count', 'views_count', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'tags', 'variants'
        ).annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )

        # Filters
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        brand_id = self.request.query_params.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)

        # Price range
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        # Features
        if self.request.query_params.get('on_sale'):
            now = timezone.now()
            queryset = queryset.filter(
                Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
            ).filter(
                Q(discount_start__isnull=True) | Q(discount_start__lte=now)
            ).filter(
                Q(discount_end__isnull=True) | Q(discount_end__gte=now)
            )

        if self.request.query_params.get('in_stock'):
            queryset = queryset.filter(
                Q(track_inventory=False, stock_status='in_stock') |
                Q(track_inventory=True, stock_quantity__gt=0)
            )

        if self.request.query_params.get('is_new'):
            queryset = queryset.filter(is_new=True)

        if self.request.query_params.get('is_featured'):
            queryset = queryset.filter(is_featured=True)

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment views
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get product reviews"""
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ProductReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_review(self, request, pk=None):
        """Add product review"""
        product = self.get_object()

        # Check if user can review
        if not product.can_review(request.user):
            return Response(
                {'error': 'يجب شراء المنتج أولاً لتتمكن من تقييمه'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if already reviewed
        if ProductReview.objects.filter(product=product, user=request.user).exists():
            return Response(
                {'error': 'لقد قمت بتقييم هذا المنتج مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        """Get product variants"""
        product = self.get_object()
        variants = product.variants.filter(is_active=True)
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Get related products"""
        product = self.get_object()

        # Manual related products
        related = product.related_products.filter(
            is_active=True,
            status='published'
        )[:6]

        # If not enough, get from same category
        if related.count() < 6:
            category_products = Product.objects.filter(
                category=product.category,
                is_active=True,
                status='published'
            ).exclude(id=product.id).order_by('-sales_count')[:6 - related.count()]

            related = list(related) + list(category_products)

        serializer = ProductListSerializer(related, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = self.get_queryset().filter(is_featured=True)[:12]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def best_sellers(self, request):
        """Get best selling products"""
        products = self.get_queryset().order_by('-sales_count')[:12]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        """Get new products"""
        products = self.get_queryset().filter(is_new=True).order_by('-created_at')[:12]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def on_sale(self, request):
        """Get products on sale"""
        now = timezone.now()
        products = self.get_queryset().filter(
            Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
        ).filter(
            Q(discount_start__isnull=True) | Q(discount_start__lte=now)
        ).filter(
            Q(discount_end__isnull=True) | Q(discount_end__gte=now)
        ).order_by('-discount_percentage')[:12]

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet للفئات
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter root categories only
        if self.request.query_params.get('root_only'):
            queryset = queryset.filter(parent=None)

        # Include product counts
        queryset = queryset.annotate(
            products_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        )

        return queryset.order_by('sort_order', 'name')

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products in category"""
        category = self.get_object()
        products = Product.objects.filter(
            category=category,
            is_active=True,
            status='published'
        )

        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(products, request)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Get subcategories"""
        category = self.get_object()
        subcategories = category.children.filter(is_active=True)
        serializer = CategorySerializer(subcategories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increment category views"""
        category = self.get_object()
        category.increment_views()
        return Response({'views_count': category.views_count})


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet للعلامات التجارية
    """
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()

        # Include product counts
        queryset = queryset.annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        )

        # Filter featured only
        if self.request.query_params.get('featured_only'):
            queryset = queryset.filter(is_featured=True)

        return queryset.order_by('order', 'name')

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products by brand"""
        brand = self.get_object()
        products = Product.objects.filter(
            brand=brand,
            is_active=True,
            status='published'
        )

        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(products, request)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet للوسوم
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()

        # Include product counts
        queryset = queryset.annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        )

        # Filter by minimum product count
        min_count = self.request.query_params.get('min_products', 0)
        queryset = queryset.filter(product_count__gte=min_count)

        return queryset.order_by('-product_count', 'name')


class WishlistViewSet(viewsets.ModelViewSet):
    """
    API ViewSet لقائمة الأمنيات
    """
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Wishlist.objects.filter(
            user=self.request.user
        ).select_related('product__category', 'product__brand')

    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': 'المنتج غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already in wishlist
        if Wishlist.objects.filter(user=request.user, product=product).exists():
            return Response(
                {'error': 'المنتج موجود بالفعل في قائمة الأمنيات'},
                status=status.HTTP_400_BAD_REQUEST
            )

        wishlist = Wishlist.objects.create(user=request.user, product=product)
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle product in wishlist"""
        product_id = request.data.get('product_id')

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': 'المنتج غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )

        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            wishlist.delete()
            return Response({
                'status': 'removed',
                'message': 'تمت إزالة المنتج من قائمة الأمنيات',
                'in_wishlist': False,
                'wishlist_count': request.user.wishlists.count()
            })

        return Response({
            'status': 'added',
            'message': 'تمت إضافة المنتج إلى قائمة الأمنيات',
            'in_wishlist': True,
            'wishlist_count': request.user.wishlists.count()
        })

    @action(detail=False, methods=['get'])
    def check(self, request):
        """Check if products are in wishlist"""
        product_ids = request.query_params.getlist('product_ids[]')

        if not product_ids:
            return Response({'products': {}})

        wishlist_products = Wishlist.objects.filter(
            user=request.user,
            product_id__in=product_ids
        ).values_list('product_id', flat=True)

        result = {
            str(pid): pid in wishlist_products
            for pid in product_ids
        }

        return Response({'products': result})


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    """
    API endpoint للحصول على اقتراحات البحث
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return Response({'suggestions': []})

    suggestions = []

    # Search products
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(name_en__icontains=query) |
        Q(sku__icontains=query),
        is_active=True,
        status='published'
    )[:5]

    for product in products:
        suggestions.append({
            'type': 'product',
            'id': product.id,
            'name': product.name,
            'image': product.default_image.image.url if product.default_image else None,
            'price': str(product.current_price),
            'url': product.get_absolute_url()
        })

    # Search categories
    categories = Category.objects.filter(
        Q(name__icontains=query) | Q(name_en__icontains=query),
        is_active=True
    )[:3]

    for category in categories:
        suggestions.append({
            'type': 'category',
            'id': category.id,
            'name': category.name,
            'icon': category.icon,
            'url': category.get_absolute_url()
        })

    # Search brands
    brands = Brand.objects.filter(
        Q(name__icontains=query) | Q(name_en__icontains=query),
        is_active=True
    )[:2]

    for brand in brands:
        suggestions.append({
            'type': 'brand',
            'id': brand.id,
            'name': brand.name,
            'logo': brand.logo.url if brand.logo else None,
            'url': f"/products/?brand={brand.id}"
        })

    return Response({'suggestions': suggestions})


@api_view(['POST'])
@permission_classes([AllowAny])
def compare_products(request):
    """
    API endpoint لمقارنة المنتجات
    """
    product_ids = request.data.get('product_ids', [])

    if not product_ids:
        return Response(
            {'error': 'لم يتم تحديد منتجات للمقارنة'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(product_ids) < 2:
        return Response(
            {'error': 'يجب اختيار منتجين على الأقل للمقارنة'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(product_ids) > 4:
        return Response(
            {'error': 'لا يمكن مقارنة أكثر من 4 منتجات'},
            status=status.HTTP_400_BAD_REQUEST
        )

    products = Product.objects.filter(
        id__in=product_ids,
        is_active=True,
        status='published'
    ).select_related('category', 'brand').prefetch_related('images')

    if products.count() != len(product_ids):
        return Response(
            {'error': 'بعض المنتجات غير موجودة'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Serialize products
    serializer = ProductDetailSerializer(products, many=True, context={'request': request})

    # Get all specifications
    all_specs = set()
    for product in products:
        if product.specifications:
            all_specs.update(product.specifications.keys())

    # Build comparison matrix
    comparison = {
        'products': serializer.data,
        'specifications': list(all_specs),
        'comparison_data': build_comparison_matrix(products, all_specs)
    }

    return Response(comparison)


def build_comparison_matrix(products, specifications):
    """Build comparison matrix for products"""
    matrix = {}

    # Basic attributes
    matrix['price'] = [str(p.current_price) for p in products]
    matrix['brand'] = [p.brand.name if p.brand else '-' for p in products]
    matrix['category'] = [p.category.name for p in products]
    matrix['rating'] = [p.rating or 0 for p in products]
    matrix['in_stock'] = [p.in_stock for p in products]
    matrix['weight'] = [f"{p.weight} كجم" if p.weight else '-' for p in products]

    # Specifications
    for spec in specifications:
        matrix[spec] = []
        for product in products:
            if product.specifications and spec in product.specifications:
                matrix[spec].append(product.specifications[spec])
            else:
                matrix[spec].append('-')

    return matrix


@api_view(['GET'])
@permission_classes([AllowAny])
def product_filters(request):
    """
    Get available filters for products
    """
    category_id = request.GET.get('category')

    # Base queryset
    products_qs = Product.objects.filter(
        is_active=True,
        status='published'
    )

    if category_id:
        products_qs = products_qs.filter(category_id=category_id)

    # Get available brands
    brands = Brand.objects.filter(
        products__in=products_qs
    ).distinct().annotate(
        product_count=Count('products', filter=Q(products__in=products_qs))
    ).order_by('name')

    # Get price range
    price_stats = products_qs.aggregate(
        min_price=Min('base_price'),
        max_price=Max('base_price')
    )

    # Get available attributes
    # This would need to be implemented based on your attribute system
    attributes = []

    filters = {
        'brands': BrandSerializer(brands, many=True).data,
        'price_range': {
            'min': float(price_stats['min_price'] or 0),
            'max': float(price_stats['max_price'] or 1000)
        },
        'attributes': attributes
    }

    return Response(filters)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_review(request, review_id):
    """
    Report a review as inappropriate
    """
    try:
        review = ProductReview.objects.get(id=review_id, is_approved=True)
    except ProductReview.DoesNotExist:
        return Response(
            {'error': 'المراجعة غير موجودة'},
            status=status.HTTP_404_NOT_FOUND
        )

    reason = request.data.get('reason', 'inappropriate')
    description = request.data.get('description', '')

    # Create report (this would need a ReviewReport model)
    # For now, just mark the review for moderation
    review.is_approved = False
    review.save()

    # Log the report
    # ReviewReport.objects.create(
    #     review=review,
    #     reported_by=request.user,
    #     reason=reason,
    #     description=description
    # )

    return Response({
        'success': True,
        'message': 'تم الإبلاغ عن المراجعة وسيتم مراجعتها'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def vote_review(request, review_id):
    """
    Vote on review helpfulness
    """
    try:
        review = ProductReview.objects.get(id=review_id, is_approved=True)
    except ProductReview.DoesNotExist:
        return Response(
            {'error': 'المراجعة غير موجودة'},
            status=status.HTTP_404_NOT_FOUND
        )

    vote_type = request.data.get('type', 'helpful')

    # Track votes in session
    session_key = f'review_vote_{review_id}'
    if session_key in request.session:
        return Response({
            'error': 'لقد قمت بالتصويت مسبقاً',
            'already_voted': True
        }, status=status.HTTP_400_BAD_REQUEST)

    if vote_type == 'helpful':
        review.helpful_count = F('helpful_count') + 1
    else:
        review.not_helpful_count = F('not_helpful_count') + 1

    review.save()
    review.refresh_from_db()

    # Mark as voted
    request.session[session_key] = vote_type

    return Response({
        'success': True,
        'helpful_count': review.helpful_count,
        'not_helpful_count': review.not_helpful_count,
        'percentage': review.helpful_percentage
    })