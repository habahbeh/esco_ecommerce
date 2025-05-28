from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, Category, ProductVariant, ProductImage

class CategoryListView(ListView):
    """
    عرض قائمة التصنيفات - يعرض قائمة التصنيفات الرئيسية
    Category list view - displays a list of main categories
    """
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        # الحصول على التصنيفات الرئيسية فقط (المستوى 1)
        # Get only main categories (level 1)
        return Category.objects.filter(level=1, is_active=True).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # إضافة بعض المنتجات المميزة
        # Add some featured products
        context['featured_products'] = Product.objects.filter(
            is_featured=True,
            status='published',
            is_active=True
        ).order_by('-published_at')[:4]
        return context

class CategoryDetailView(DetailView):
    """
    عرض تفاصيل التصنيف - يعرض تفاصيل تصنيف معين ومنتجاته
    Category detail view - displays details of a specific category and its products
    """
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()

        # الحصول على المنتجات في هذا التصنيف - Get products in this category
        products = Product.objects.filter(
            category=category,
            status='published',
            is_active=True
        ).order_by('-published_at')

        # الحصول على التصنيفات الفرعية - Get subcategories
        subcategories = Category.objects.filter(
            parent=category,
            is_active=True
        ).order_by('name')

        # تطبيق التصفية إذا تم تقديمها - Apply filtering if provided
        sort_by = self.request.GET.get('sort_by', 'newest')

        if sort_by == 'price_low':
            products = products.order_by('base_price')
        elif sort_by == 'price_high':
            products = products.order_by('-base_price')
        elif sort_by == 'name':
            products = products.order_by('name')
        else:  # newest
            products = products.order_by('-published_at')

        context['products'] = products
        context['subcategories'] = subcategories
        context['sort_by'] = sort_by
        return context

class ProductDetailView(DetailView):
    """
    عرض تفاصيل المنتج - يعرض تفاصيل منتج معين
    Product detail view - displays details of a specific product
    """
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        # الحصول على المنتجات المنشورة والنشطة فقط
        # Get only published and active products
        return Product.objects.filter(status='published', is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        # الحصول على المنتجات ذات الصلة - Get related products
        related_products = Product.objects.filter(
            category=product.category,
            status='published',
            is_active=True
        ).exclude(id=product.id).order_by('-published_at')[:4]

        # الحصول على جميع صور المنتج - Get all product images
        product_images = product.images.all().order_by('sort_order')

        # الحصول على جميع متغيرات المنتج النشطة - Get all active product variants
        product_variants = product.variants.filter(is_active=True)

        context['related_products'] = related_products
        context['product_images'] = product_images
        context['product_variants'] = product_variants

        return context

class ProductSearchView(ListView):
    """
    عرض البحث عن المنتجات - يعرض نتائج البحث عن المنتجات
    Product search view - displays product search results
    """
    model = Product
    template_name = 'products/product_search.html'
    context_object_name = 'products'
    paginate_by = 16

    def get_queryset(self):
        query = self.request.GET.get('q', '')

        if query:
            # البحث في اسم المنتج ووصفه - Search in product name and description
            return Product.objects.filter(
                Q(name__icontains=query) |
                Q(name_ar__icontains=query) |
                Q(name_en__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query),
                status='published',
                is_active=True
            ).order_by('-published_at')
        else:
            return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

class SpecialOffersView(ListView):
    """
    عرض العروض الخاصة - يعرض المنتجات التي عليها خصومات
    Special offers view - displays products with discounts
    """
    model = Product
    template_name = 'products/special_offers.html'
    context_object_name = 'products'
    paginate_by = 16

    def get_queryset(self):
        from django.utils import timezone

        # الحصول على المنتجات التي لها خصومات سارية المفعول
        # Get products with valid discounts
        products_with_discount = []
        products = Product.objects.filter(status='published', is_active=True)

        for product in products:
            if product.has_discount:
                products_with_discount.append(product)

        # تحويل القائمة إلى QuerySet
        # Convert list to QuerySet
        product_ids = [p.id for p in products_with_discount]
        return Product.objects.filter(id__in=product_ids).order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('العروض الخاصة')
        return context