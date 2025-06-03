# File: products/views/category_views.py
"""
Category views module
Handles displaying categories with hierarchical support
"""

from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.db.models import Q, Count, Min, Max
from django.utils.translation import gettext as _

from ..models import Category, Product


class CategoryDetailView(DetailView):
    """
    Enhanced Category detail view with subcategories and products
    """
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'

    def get_queryset(self):
        """Get active categories"""
        return Category.objects.filter(is_active=True).select_related('parent')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        # Get all root categories for sidebar
        context['root_categories'] = Category.objects.filter(
            parent=None,
            is_active=True
        ).prefetch_related('children')

        # Get direct subcategories
        subcategories = category.children.filter(is_active=True).annotate(
            products_count=Count(
                'products',
                filter=Q(
                    products__is_active=True,
                    products__status='published'
                )
            )
        ).order_by('sort_order', 'name')

        context['subcategories'] = subcategories
        context['subcategories_count'] = subcategories.count()

        # Get featured products from this category
        category_products = Product.objects.filter(
            Q(category=category) | Q(category__parent=category),
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images')[:8]

        context['category_products'] = category_products

        # Get total products count
        context['total_products'] = Product.objects.filter(
            Q(category=category) | Q(category__parent=category),
            is_active=True,
            status='published'
        ).count()

        # Get price range
        price_range = Product.objects.filter(
            Q(category=category) | Q(category__parent=category),
            is_active=True,
            status='published'
        ).aggregate(
            min_price=Min('base_price'),
            max_price=Max('base_price')
        )
        context['price_range'] = price_range

        # Increment view count
        if not self.request.user.is_staff:
            self.object.increment_views()

        return context


class CategoryListView(ListView):
    """
    Category listing view
    """
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        """Get main categories with product counts"""
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
        context['title'] = _('جميع الفئات')
        return context