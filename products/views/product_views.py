# File: products/views/product_views.py
"""
Product and Category views
Handles product and category listings, details, and related functionality
"""

from typing import Optional, Dict, Any
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.db.models import Q, Avg, Count, Min, Max, Prefetch, Q, F
from django.utils.translation import gettext as _
from django.http import Http404
import logging

from .base_views import BaseProductListView, BaseProductDetailView
from ..models import Product, Category, Brand, ProductImage, Tag

logger = logging.getLogger(__name__)


# =============================================
# ============ عروض التصنيفات ===============
# =============================================

class CategoryListView(ListView):
    """
    عرض قائمة الفئات مع دعم لشجرة الفئات
    """
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        """الحصول على الفئات الرئيسية مع عدد المنتجات"""
        return Category.objects.filter(
            parent=None,
            is_active=True
        ).annotate(
            total_products=Count(
                'products',
                filter=Q(products__is_active=True, products__status='published')
            ) + Count(
                'children__products',
                filter=Q(children__products__is_active=True, children__products__status='published')
            )
        ).order_by('sort_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة جميع الفئات للشجرة (بما في ذلك الفئات الفرعية)
        context['all_categories'] = Category.objects.filter(
            is_active=True
        ).select_related('parent')

        # بناء هيكل الشجرة للفئات
        context['category_tree'] = self.build_category_tree()

        # الفئات المميزة
        context['featured_categories'] = Category.objects.filter(
            is_featured=True,
            is_active=True
        ).order_by('sort_order')[:6]

        context['title'] = _('جميع الفئات')
        return context

    def build_category_tree(self):
        """بناء هيكل الشجرة للفئات"""
        # الحصول على جميع الفئات النشطة مع حساب عدد المنتجات المباشرة
        all_categories = Category.objects.filter(
            is_active=True
        ).select_related('parent').annotate(
            direct_products_count=Count(
                'products',
                filter=Q(products__is_active=True, products__status='published')
            )
        ).order_by('sort_order', 'name')

        # بناء قاموس للفئات الفرعية
        children_map = {}
        for category in all_categories:
            parent_id = category.parent_id if category.parent_id else None
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(category)

        # بناء شجرة الفئات بشكل تكراري وحساب إجمالي المنتجات
        def build_tree(parent_id=None):
            if parent_id not in children_map:
                return [], 0  # ترجع قائمة فارغة وعدد منتجات 0

            result = []
            total_products_in_subtree = 0  # إجمالي المنتجات في الشجرة الفرعية

            for category in children_map[parent_id]:
                # التحقق من وجود أطفال وحساب المنتجات في الفئات الفرعية
                children, children_products_count = build_tree(category.id)

                # حساب إجمالي المنتجات = المنتجات المباشرة + منتجات الفئات الفرعية
                total_category_products = category.direct_products_count + children_products_count

                # إضافة عدد منتجات هذه الفئة إلى المجموع الكلي للشجرة الفرعية
                total_products_in_subtree += total_category_products

                result.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'children': children,
                    'products_count': total_category_products,  # العدد الإجمالي للمنتجات
                    'has_children': bool(children)
                })

            return result, total_products_in_subtree

        # بناء الشجرة بدءاً من الفئات الرئيسية
        tree, _ = build_tree()

        return tree


# =============================================
# ============= عروض المنتجات ===============
# =============================================

class ProductListView(BaseProductListView):
    """
    Enhanced product list view with advanced filtering and category tree sidebar
    """
    template_name = 'products/product_list.html'

    def get_queryset(self):
        """Get queryset with filtering options"""
        queryset = super().get_queryset()

        # Category filter
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                # Get current category and all its children
                categories = category.get_all_children(include_self=True)
                queryset = queryset.filter(category__in=categories)
                # Store category for context
                self.category = category
            except Category.DoesNotExist:
                raise Http404(_("الفئة غير موجودة"))
        else:
            self.category = None

        # Multiple categories filter (for advanced filtering)
        category_ids = self.request.GET.getlist('category')
        if category_ids:
            queryset = queryset.filter(category_id__in=category_ids)

        # Brand filter
        brand_ids = self.request.GET.getlist('brand')
        if brand_ids:
            queryset = queryset.filter(brand_id__in=brand_ids)

        # Price range filter - تعديل لاستخدام base_price بدلاً من current_price
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            # نفترض أن المنتجات المخفضة يمكن أن تكون أقل من سعر الأساس
            # لذلك نبحث في المنتجات التي:
            # - سعرها الأساسي أكبر من الحد الأدنى و ليس لها خصم
            # - أو سعرها بعد الخصم أكبر من الحد الأدنى
            min_price_value = float(min_price)
            discount_condition = Q(
                # منتجات بخصم نسبة مئوية والسعر بعد الخصم أكبر من الحد الأدنى
                Q(discount_percentage__gt=0) &
                Q(base_price__gte=min_price_value / (1 - F('discount_percentage') / 100))
            ) | Q(
                # منتجات بخصم ثابت والسعر بعد الخصم أكبر من الحد الأدنى
                Q(discount_amount__gt=0) &
                Q(base_price__gte=min_price_value + F('discount_amount'))
            ) | Q(
                # منتجات بدون خصم وسعرها الأساسي أكبر من الحد الأدنى
                Q(discount_percentage=0) &
                Q(discount_amount=0) &
                Q(base_price__gte=min_price_value)
            )
            queryset = queryset.filter(discount_condition)

        if max_price:
            # نبحث في المنتجات التي سعرها الأساسي أقل من الحد الأقصى
            # أو سعرها بعد الخصم أقل من الحد الأقصى
            max_price_value = float(max_price)
            # للتبسيط، سنفترض أن السعر الأساسي هو الأهم
            queryset = queryset.filter(base_price__lte=max_price_value)

        # Feature filters
        if self.request.GET.get('is_new'):
            queryset = queryset.filter(is_new=True)
        if self.request.GET.get('on_sale'):
            # منتجات بخصم: إما لها نسبة خصم أو مبلغ خصم
            queryset = queryset.filter(Q(discount_percentage__gt=0) | Q(discount_amount__gt=0))
        if self.request.GET.get('in_stock'):
            queryset = queryset.filter(stock_quantity__gt=F('reserved_quantity'))
        # إضافة: منتجات مميزة
        if self.request.GET.get('is_featured'):
            queryset = queryset.filter(is_featured=True)

        # إضافة: فلترة حسب التقييم
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).filter(avg_rating__gte=min_rating)

        # Sort products
        sort_by = self.request.GET.get('sort', 'newest')
        queryset = self.apply_sorting(queryset, sort_by)

        return queryset

    def apply_sorting(self, queryset, sort_by: str):
        """Apply sorting to product queryset"""
        if sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'price_low':
            # للتبسيط، نرتب حسب السعر الأساسي
            return queryset.order_by('base_price')
        elif sort_by == 'price_high':
            return queryset.order_by('-base_price')
        elif sort_by == 'name_az':
            return queryset.order_by('name')
        elif sort_by == 'best_rated':
            return queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).order_by('-avg_rating', '-created_at')
        # إضافة: ترتيب حسب الأكثر مبيعاً
        elif sort_by == 'best_selling':
            return queryset.order_by('-sales_count', '-created_at')
        # إضافة: ترتيب حسب الأكثر مشاهدة
        elif sort_by == 'most_viewed':
            return queryset.order_by('-views_count', '-created_at')

        # Default to newest
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add enhanced context data for product list with category tree"""
        context = super().get_context_data(**kwargs)

        # Get total products count
        context['products_count'] = self.get_queryset().count()

        # Get category tree using the CategoryListView implementation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        # Current category path for highlighting active category
        if hasattr(self, 'category') and self.category:
            context['category'] = self.category

            # Build current category path
            current_category_path = []
            current = self.category
            while current:
                current_category_path.append(current.id)
                current = current.parent
            context['current_category_path'] = current_category_path

        # Get available brands with product counts for filtering
        context['brands'] = Brand.objects.filter(
            is_active=True,
            products__is_active=True,
            products__status='published'
        ).annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__status='published'
            ))
        ).filter(product_count__gt=0).order_by('-product_count')

        # إضافة معلومات للفلاتر النشطة
        context['active_filters'] = self.get_active_filters()

        # إضافة نطاق السعر للمنتجات - تعديل لاستخدام base_price
        price_range = Product.objects.filter(
            is_active=True,
            status='published'
        ).aggregate(
            min_price=Min('base_price'),
            max_price=Max('base_price')
        )
        context['price_range'] = price_range

        return context

    def get_active_filters(self):
        """Get active filters for display"""
        active_filters = []

        # نطاق السعر
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price or max_price:
            active_filters.append({
                'type': 'price',
                'label': _('السعر'),
                'display': f"{min_price or '0'} - {max_price or '∞'} {_('د.أ')}"
            })

        # العلامات التجارية
        brand_ids = self.request.GET.getlist('brand')
        if brand_ids:
            brands = Brand.objects.filter(id__in=brand_ids)
            for brand in brands:
                active_filters.append({
                    'type': 'brand',
                    'value': str(brand.id),
                    'label': _('العلامة التجارية'),
                    'display': brand.name
                })

        # الفئات
        category_ids = self.request.GET.getlist('category')
        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            for category in categories:
                active_filters.append({
                    'type': 'category',
                    'value': str(category.id),
                    'label': _('الفئة'),
                    'display': category.name
                })

        # المميزات
        if self.request.GET.get('is_new'):
            active_filters.append({
                'type': 'is_new',
                'label': _('المميزات'),
                'display': _('منتجات جديدة')
            })

        if self.request.GET.get('on_sale'):
            active_filters.append({
                'type': 'on_sale',
                'label': _('المميزات'),
                'display': _('منتجات بخصم')
            })

        if self.request.GET.get('in_stock'):
            active_filters.append({
                'type': 'in_stock',
                'label': _('المميزات'),
                'display': _('متوفر في المخزون')
            })

        if self.request.GET.get('is_featured'):
            active_filters.append({
                'type': 'is_featured',
                'label': _('المميزات'),
                'display': _('منتجات مميزة')
            })

        # التقييم
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            active_filters.append({
                'type': 'min_rating',
                'label': _('التقييم'),
                'display': f"{min_rating}+ ⭐"
            })

        return active_filters

class ProductDetailView(BaseProductDetailView):
    """
    Enhanced product detail view with performance optimizations
    """
    template_name = 'products/product_detail.html'

    def get_context_data(self, **kwargs):
        """Add additional context for product detail"""
        context = super().get_context_data(**kwargs)

        # Add review form if user can review
        if context.get('can_review'):
            from ..forms import ProductReviewForm
            context['review_form'] = ProductReviewForm()

        # Add category tree for sidebar navigation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        # Current category path for highlighting in tree
        product = self.object
        current_category_path = []
        current = product.category
        while current:
            current_category_path.append(current.id)
            current = current.parent
        context['current_category_path'] = current_category_path

        return context


class SpecialOffersView(BaseProductListView):
    """
    Special offers and discounted products view
    """
    template_name = 'products/special_offers.html'

    def get_queryset(self):
        """Get products with active discounts"""
        from django.utils import timezone
        now = timezone.now()

        return self.get_optimized_product_queryset().filter(
            Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
        ).filter(
            Q(discount_start__isnull=True) | Q(discount_start__lte=now)
        ).filter(
            Q(discount_end__isnull=True) | Q(discount_end__gte=now)
        ).order_by('-discount_percentage', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('العروض الخاصة')

        # Add category tree for sidebar navigation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        # Calculate total savings
        products = self.get_queryset()
        total_savings = sum(
            (product.base_price - product.current_price)
            for product in products
            if product.has_discount
        )
        context['total_savings'] = total_savings
        context['products_count'] = products.count()

        return context


class TagProductsView(BaseProductListView):
    """
    Products filtered by tag
    """
    template_name = 'products/product_list.html'  # Use same template as main product list

    def get_queryset(self):
        """Get products filtered by tag"""
        tag_slug = self.kwargs.get('tag_slug')

        try:
            self.tag = Tag.objects.get(slug=tag_slug)
        except Tag.DoesNotExist:
            raise Http404(_("الوسم غير موجود"))

        return super().get_queryset().filter(tags=self.tag)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['title'] = f'{_("منتجات بوسم")}: {self.tag.name}'

        # Add category tree for sidebar navigation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        context['products_count'] = self.get_queryset().count()

        return context


class BrandProductsView(BaseProductListView):
    """
    Products filtered by brand
    """
    template_name = 'products/product_list.html'  # Use same template as main product list

    def get_queryset(self):
        """Get products filtered by brand"""
        brand_slug = self.kwargs.get('brand_slug')

        try:
            self.brand = Brand.objects.get(slug=brand_slug, is_active=True)
        except Brand.DoesNotExist:
            raise Http404(_("العلامة التجارية غير موجودة"))

        return super().get_queryset().filter(brand=self.brand)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand'] = self.brand
        context['title'] = f'{_("منتجات")}: {self.brand.name}'

        # Add category tree for sidebar navigation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        context['products_count'] = self.get_queryset().count()

        # Brand statistics
        context['brand_stats'] = {
            'total_products': self.brand.products.filter(
                is_active=True,
                status='published'
            ).count(),
            'categories_count': self.brand.products.filter(
                is_active=True,
                status='published'
            ).values('category').distinct().count(),
            'avg_rating': self.brand.products.filter(
                is_active=True,
                status='published'
            ).aggregate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            )['avg_rating'] or 0
        }

        return context


class NewProductsView(BaseProductListView):
    """
    View for new products
    """
    template_name = 'products/product_list.html'  # Use same template as main product list

    def get_queryset(self):
        """Get new products"""
        return super().get_queryset().filter(is_new=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('المنتجات الجديدة')

        # Add category tree for sidebar navigation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        context['products_count'] = self.get_queryset().count()

        return context


class FeaturedProductsView(BaseProductListView):
    """
    View for featured products
    """
    template_name = 'products/product_list.html'  # Use same template as main product list

    def get_queryset(self):
        """Get featured products"""
        return super().get_queryset().filter(is_featured=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('المنتجات المميزة')

        # Add category tree for sidebar navigation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        context['products_count'] = self.get_queryset().count()

        return context


class BestSellersView(BaseProductListView):
    """
    View for best selling products
    """
    template_name = 'products/product_list.html'  # Use same template as main product list

    def get_queryset(self):
        """Get best selling products"""
        return super().get_queryset().filter(
            sales_count__gt=0
        ).order_by('-sales_count')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('الأكثر مبيعاً')

        # Add category tree for sidebar navigation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        context['products_count'] = self.get_queryset().count()

        return context


class ProductVariantDetailView(BaseProductDetailView):
    """
    Product variant detail view
    """
    template_name = 'products/variant_detail.html'

    def get_object(self, queryset=None):
        """Get product variant"""
        from ..models import ProductVariant

        variant_id = self.kwargs.get('variant_id')
        try:
            variant = ProductVariant.objects.select_related('product').get(
                id=variant_id,
                is_active=True,
                product__is_active=True,
                product__status='published'
            )
            return variant.product
        except ProductVariant.DoesNotExist:
            raise Http404(_("متغير المنتج غير موجود"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the specific variant
        variant_id = self.kwargs.get('variant_id')
        try:
            variant = self.object.variants.get(id=variant_id, is_active=True)
            context['selected_variant'] = variant
        except:
            context['selected_variant'] = None

        # Add category tree for sidebar navigation
        category_view = CategoryListView()
        category_view.request = self.request
        context['category_tree'] = category_view.build_category_tree()

        return context