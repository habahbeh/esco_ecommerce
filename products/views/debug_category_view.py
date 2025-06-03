# File: products/views/debug_category_view.py
"""
عرض تصحيح لمشكلة الفئات - أضف هذا الملف إلى مشروعك وقم باستدعائه في urls.py للاختبار
"""

from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.db import connection

from ..models import Category, Product


class DebugCategoryView(View):
    """عرض تصحيح لفحص الفئات"""

    def get(self, request):
        """عرض جميع الفئات بطريقة مباشرة للتشخيص"""
        output = "<h1>تشخيص الفئات</h1>"

        # 1. اختبار الاتصال بقاعدة البيانات
        output += "<h2>اختبار الاتصال بقاعدة البيانات</h2>"
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM products_category")
            row = cursor.fetchone()
            output += f"<p>عدد الفئات في قاعدة البيانات: {row[0]}</p>"

        # 2. عرض جميع الفئات - بدون تصفية
        output += "<h2>جميع الفئات (بدون تصفية)</h2>"
        all_categories = Category.objects.all()
        output += f"<p>عدد الفئات الكلي: {all_categories.count()}</p>"

        if all_categories.exists():
            output += "<ul>"
            for cat in all_categories:
                output += f"<li>ID: {cat.id} | الاسم: {cat.name} | نشط: {cat.is_active} | الأب: {cat.parent_id or 'لا يوجد'}</li>"
            output += "</ul>"
        else:
            output += "<p>لا توجد فئات في قاعدة البيانات!</p>"

        # 3. الفئات النشطة فقط
        output += "<h2>الفئات النشطة فقط</h2>"
        active_categories = Category.objects.filter(is_active=True)
        output += f"<p>عدد الفئات النشطة: {active_categories.count()}</p>"

        if active_categories.exists():
            output += "<ul>"
            for cat in active_categories:
                output += f"<li>ID: {cat.id} | الاسم: {cat.name} | الأب: {cat.parent_id or 'لا يوجد'}</li>"
            output += "</ul>"
        else:
            output += "<p>لا توجد فئات نشطة!</p>"

        # 4. الفئات الرئيسية
        output += "<h2>الفئات الرئيسية</h2>"
        root_categories = Category.objects.filter(parent=None)
        output += f"<p>عدد الفئات الرئيسية: {root_categories.count()}</p>"

        if root_categories.exists():
            output += "<ul>"
            for cat in root_categories:
                output += f"<li>ID: {cat.id} | الاسم: {cat.name} | نشط: {cat.is_active}</li>"
            output += "</ul>"
        else:
            output += "<p>لا توجد فئات رئيسية!</p>"

        # 5. فحص تعداد الفئات الفرعية
        output += "<h2>تعداد الفئات الفرعية</h2>"
        root_cats = Category.objects.filter(parent=None, is_active=True)

        if root_cats.exists():
            output += "<ul>"
            for cat in root_cats:
                child_count = Category.objects.filter(parent=cat).count()
                output += f"<li>الفئة: {cat.name} | عدد الفئات الفرعية: {child_count}</li>"
            output += "</ul>"

        # 6. بناء شجرة مبسطة
        output += "<h2>شجرة الفئات المبسطة</h2>"

        # بناء قاموس البيانات
        categories_dict = {}
        categories_by_parent = {}

        for cat in all_categories:
            categories_dict[cat.id] = {
                'id': cat.id,
                'name': cat.name,
                'is_active': cat.is_active,
                'parent_id': cat.parent_id,
                'children': []
            }

            parent_id = cat.parent_id or 0
            if parent_id not in categories_by_parent:
                categories_by_parent[parent_id] = []
            categories_by_parent[parent_id].append(cat.id)

        # بناء الشجرة
        def build_simple_tree(parent_id=0, level=0):
            if parent_id not in categories_by_parent:
                return ""

            tree_html = "<ul>"
            for cat_id in categories_by_parent[parent_id]:
                cat = categories_dict[cat_id]
                active_class = "" if cat['is_active'] else " (غير نشط)"
                tree_html += f"<li>{cat['name']}{active_class}"

                # إضافة الفئات الفرعية
                if cat_id in categories_by_parent:
                    tree_html += build_simple_tree(cat_id, level + 1)

                tree_html += "</li>"
            tree_html += "</ul>"
            return tree_html

        # عرض الشجرة
        if 0 in categories_by_parent:
            output += build_simple_tree()
        else:
            output += "<p>لا يمكن بناء الشجرة: لا توجد فئات رئيسية!</p>"

        # 7. معلومات إضافية
        output += "<h2>معلومات إضافية</h2>"
        output += f"<p>عدد المنتجات: {Product.objects.count()}</p>"
        output += f"<p>عدد المنتجات النشطة: {Product.objects.filter(is_active=True).count()}</p>"

        # نصائح للإصلاح
        output += "<h2>نصائح للإصلاح</h2>"
        output += "<ol>"
        output += "<li>تأكد من وجود فئات نشطة (is_active=True).</li>"
        output += "<li>تأكد من وجود فئات رئيسية (parent=None).</li>"
        output += "<li>تأكد من عدم وجود تناقضات في علاقات parent-child.</li>"
        output += "<li>امسح الكاش إذا كنت تستخدمه.</li>"
        output += "</ol>"

        return HttpResponse(output)