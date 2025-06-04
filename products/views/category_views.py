# File: products/views/category_views.py

from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.db.models import Q, Count, Min, Max, Avg, Prefetch
from django.utils.translation import gettext as _
from django.http import Http404
import logging

from ..models import Category, Product, Brand

logger = logging.getLogger(__name__)


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
        ).prefetch_related(
            Prefetch(
                'children',
                queryset=Category.objects.filter(is_active=True)
            )
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


class CategoryDetailView(DetailView):
    """
    عرض تفاصيل الفئة مع المنتجات
    """
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'

    def get_queryset(self):
        """الحصول على الفئات النشطة"""
        return Category.objects.filter(is_active=True).select_related('parent')

    def get(self, request, *args, **kwargs):
        """معالجة طلب GET وزيادة عدد المشاهدات"""
        response = super().get(request, *args, **kwargs)

        # زيادة عدد مشاهدات الفئة
        try:
            self.object.increment_views()
        except Exception as e:
            logger.warning(f"فشل في زيادة عدد المشاهدات للفئة {self.object.id}: {e}")

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        # شجرة الفئات الكاملة
        view = CategoryListView()
        view.request = self.request  # تمرير الطلب الحالي للعرض
        context['category_tree'] = view.build_category_tree()  # استدعاء build_category_tree بدلاً من "test"

        # المسار الحالي للفئة (لتمييز الفئة الحالية في الشجرة)
        current_category_path = []
        current = category
        while current:
            current_category_path.append(current.id)
            current = current.parent

        context['current_category_path'] = current_category_path

        # الفئات الفرعية المباشرة
        context['subcategories'] = category.children.filter(is_active=True).annotate(
            subcategory_products_count=Count(
                'products',
                filter=Q(
                    products__is_active=True,
                    products__status='published'
                )
            )
        ).order_by('sort_order', 'name')

        # المنتجات في هذه الفئة
        products_queryset = Product.objects.filter(
            category=category,
            is_active=True,
            status='published'
        ).select_related('category', 'brand').prefetch_related('images')

        # تطبيق الترتيب
        sort_by = self.request.GET.get('sort', 'newest')

        if sort_by == 'newest':
            products_queryset = products_queryset.order_by('-created_at')
        elif sort_by == 'price_low':
            products_queryset = products_queryset.order_by('base_price')
        elif sort_by == 'price_high':
            products_queryset = products_queryset.order_by('-base_price')
        elif sort_by == 'best_selling':
            products_queryset = products_queryset.order_by('-sales_count')
        elif sort_by == 'top_rated':
            products_queryset = products_queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
            ).order_by('-avg_rating')

        context['products'] = products_queryset
        context['products_count'] = products_queryset.count()
        context['subcategories_count'] = context['subcategories'].count()

        # العلامات التجارية الأكثر شيوعاً في هذه الفئة
        context['top_brands'] = Brand.objects.filter(
            products__category=category,
            products__is_active=True,
            products__status='published',
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(
                    products__category=category,
                    products__is_active=True,
                    products__status='published'
                )
            )
        ).order_by('-product_count')[:10]

        context['brands_count'] = context['top_brands'].count()

        return context