# File: products/views/category_views.py

from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.db.models import Q, Count, Min, Max
from django.utils.translation import gettext as _
from django.http import Http404

from ..models import Category, Product


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


class CategoryDetailView(DetailView):
    """
    عرض تفاصيل الفئة مع المنتجات
    تم استبدالها بالاعتماد على ProductListView مع فلتر الفئة
    """
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'

    def get_queryset(self):
        """الحصول على الفئات النشطة"""
        return Category.objects.filter(is_active=True).select_related('parent')

    def get(self, request, *args, **kwargs):
        """تمت إعادة توجيه هذا العرض إلى ProductListView"""
        # يمكن إضافة رمز هنا للتعامل مع الحالات الخاصة إذا لزم الأمر
        from django.shortcuts import redirect
        from django.urls import reverse

        # الحصول على الكائن
        self.object = self.get_object()

        # زيادة عدد مشاهدات الفئة
        try:
            self.object.increment_views()
        except Exception as e:
            pass

        # إعادة التوجيه إلى عرض المنتجات مع فلتر الفئة
        return redirect(reverse('products:category_products', kwargs={'category_slug': self.object.slug}))