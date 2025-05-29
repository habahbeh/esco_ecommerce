from rest_framework import serializers
from .models import (
    Category, Brand, Product, ProductImage, ProductVariant,
    Tag, ProductReview, Wishlist
)


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer للفئات
    """
    products_count = serializers.IntegerField(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'name_en', 'slug', 'description',
            'description_en', 'image', 'icon', 'parent',
            'is_active', 'is_featured', 'products_count',
            'children', 'level'
        ]

    def get_children(self, obj):
        if obj.children.filter(is_active=True).exists():
            return CategorySerializer(
                obj.children.filter(is_active=True),
                many=True,
                context=self.context
            ).data
        return []


class BrandSerializer(serializers.ModelSerializer):
    """
    Serializer للعلامات التجارية
    """

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'name_en', 'slug', 'logo',
            'website', 'description', 'country',
            'is_featured', 'is_active'
        ]


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer للوسوم
    """

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer لصور المنتجات
    """

    class Meta:
        model = ProductImage
        fields = [
            'id', 'image', 'alt_text', 'caption',
            'is_primary', 'order'
        ]


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Serializer لمتغيرات المنتج
    """
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'size', 'color', 'material',
            'price_adjustment', 'price', 'stock_quantity',
            'in_stock', 'is_active'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer لقائمة المنتجات (معلومات مختصرة)
    """
    category = serializers.StringRelatedField()
    brand = serializers.StringRelatedField()
    primary_image = serializers.SerializerMethodField()
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'category', 'brand',
            'short_description', 'base_price', 'current_price',
            'has_discount', 'discount_percentage', 'in_stock',
            'is_featured', 'is_new', 'primary_image',
            'rating', 'review_count'
        ]

    def get_primary_image(self, obj):
        image = obj.default_image
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.image.url)
            return image.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer لتفاصيل المنتج الكاملة
    """
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    savings_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    savings_percentage = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    low_stock = serializers.BooleanField(read_only=True)
    rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'name_en', 'slug', 'sku', 'barcode',
            'category', 'brand', 'tags', 'short_description',
            'short_description_en', 'description', 'description_en',
            'specifications', 'base_price', 'current_price',
            'discount_percentage', 'discount_amount', 'has_discount',
            'savings_amount', 'savings_percentage', 'tax_rate',
            'stock_quantity', 'stock_status', 'in_stock', 'low_stock',
            'min_stock_level', 'max_order_quantity', 'track_inventory',
            'weight', 'length', 'width', 'height', 'is_featured',
            'is_new', 'is_best_seller', 'is_digital', 'requires_shipping',
            'show_price', 'images', 'variants', 'rating', 'review_count',
            'views_count', 'sales_count', 'created_at', 'updated_at'
        ]


class ProductReviewSerializer(serializers.ModelSerializer):
    """
    Serializer لتقييمات المنتجات
    """
    user = serializers.StringRelatedField()
    helpful_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductReview
        fields = [
            'id', 'user', 'rating', 'title', 'comment',
            'image1', 'image2', 'image3', 'is_approved',
            'is_featured', 'helpful_count', 'not_helpful_count',
            'helpful_percentage', 'created_at'
        ]
        read_only_fields = [
            'user', 'is_approved', 'is_featured',
            'helpful_count', 'not_helpful_count'
        ]


class WishlistSerializer(serializers.ModelSerializer):
    """
    Serializer لقائمة الأمنيات
    """
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'created_at']


class ProductComparisonSerializer(serializers.Serializer):
    """
    Serializer لمقارنة المنتجات
    """
    products = ProductDetailSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        """
        تنظيم البيانات للمقارنة السهلة
        """
        products = instance.get('products', [])
        if not products:
            return {'products': []}

        # جمع جميع المواصفات الموجودة
        all_specs = set()
        for product in products:
            if product.specifications:
                all_specs.update(product.specifications.keys())

        # تنظيم البيانات للمقارنة
        comparison_data = {
            'products': ProductDetailSerializer(products, many=True, context=self.context).data,
            'specifications': list(all_specs),
            'comparison_matrix': self._build_comparison_matrix(products, all_specs)
        }

        return comparison_data

    def _build_comparison_matrix(self, products, specifications):
        """
        بناء جدول المقارنة
        """
        matrix = {}

        # Basic info
        matrix['name'] = [p.name for p in products]
        matrix['price'] = [str(p.current_price) for p in products]
        matrix['brand'] = [p.brand.name if p.brand else '-' for p in products]
        matrix['rating'] = [p.rating or 0 for p in products]
        matrix['in_stock'] = [p.in_stock for p in products]

        # Specifications
        for spec in specifications:
            matrix[spec] = []
            for product in products:
                if product.specifications and spec in product.specifications:
                    matrix[spec].append(product.specifications[spec])
                else:
                    matrix[spec].append('-')

        return matrix


# ViewSets API endpoints
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet للمنتجات
    """
    queryset = Product.objects.filter(is_active=True, status='published')
    serializer_class = ProductListSerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'is_featured', 'is_new']
    search_fields = ['name', 'name_en', 'description', 'sku']
    ordering_fields = ['created_at', 'base_price', 'sales_count', 'views_count']
    ordering = ['-created_at']

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
    def reviews(self, request, slug=None):
        """Get product reviews"""
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True)
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def add_review(self, request, slug=None):
        """Add product review"""
        product = self.get_object()

        # Check if user can review
        if not product.can_review(request.user):
            return Response(
                {'error': 'You must purchase this product to review it'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if already reviewed
        if ProductReview.objects.filter(product=product, user=request.user).exists():
            return Response(
                {'error': 'You have already reviewed this product'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)