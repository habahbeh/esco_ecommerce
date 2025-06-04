# File: products/views/category_views.py

from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.db.models import Q, Count, Min, Max
from django.utils.translation import gettext as _

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
        context['category_tree'] = "test" #self.build_category_tree()

        # الفئات المميزة
        context['featured_categories'] = Category.objects.filter(
            is_featured=True,
            is_active=True
        ).order_by('sort_order')[:6]

        context['title'] = _('جميع الفئات')
        return context


    def build_category_tree(self):
        """بناء هيكل الشجرة للفئات"""
        # الحصول على جميع الفئات النشطة
        all_categories = Category.objects.filter(
            is_active=True
        ).select_related('parent').order_by('sort_order', 'name')

        # بناء قاموس للفئات الفرعية
        children_map = {}
        for category in all_categories:
            parent_id = category.parent_id if category.parent_id else None  # استخدام None بدلاً من 0
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(category)

        # بناء شجرة الفئات بشكل تكراري
        def build_tree(parent_id=None):  # استخدام None بدلاً من 0
            if parent_id not in children_map:
                return []

            result = []
            for category in children_map[parent_id]:
                # استخدام products_count المخزن مسبقًا
                products_count = category.products_count

                # التحقق من وجود أطفال
                children = build_tree(category.id)

                result.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'children': children,
                    'products_count': products_count,
                    'has_children': bool(children)
                })
            return result

        # بناء الشجرة بدءاً من الفئات الرئيسية
        tree = build_tree()

        # طباعة معلومات التصحيح إذا كانت الشجرة فارغة
        if not tree and children_map:
            print("WARNING: Tree is empty but children_map has data:")
            print(f"Keys in children_map: {list(children_map.keys())}")
            if None in children_map:
                print(f"Root categories count: {len(children_map[None])}")

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
        # مسح الكاش المتعلق بالفئات
        view = CategoryListView()

        return Category.objects.filter(is_active=True).select_related('parent')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        # شجرة الفئات الكاملة
        view = CategoryListView()
        view.request = self.request  # تمرير الطلب الحالي للعرض
        context['category_tree'] = "test"#view.build_category_tree()
        print("#"*100)

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

        context['products'] = products_queryset
        context['products_count'] = products_queryset.count()
        context['subcategories_count'] = context['subcategories'].count()

        return context