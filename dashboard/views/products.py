# views/products.py
# عروض إدارة المنتجات والتصنيفات

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify
import uuid
import json
from django.views.decorators.http import require_POST
from decimal import Decimal

from products.models import (
    Product, Category, Brand, Tag, ProductImage,
    ProductVariant, ProductAttribute, ProductAttributeValue,
    ProductReview, ProductDiscount
)
from .dashboard import DashboardAccessMixin


# ========================= إدارة المنتجات =========================

class ProductListView(DashboardAccessMixin, View):
    """عرض قائمة المنتجات مع البحث والتصفية"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        category_filter = request.GET.get('category', '')
        brand_filter = request.GET.get('brand', '')
        status_filter = request.GET.get('status', '')

        # قائمة المنتجات مع استعلام مُحسّن
        products = Product.objects.select_related('category', 'brand').prefetch_related('images').order_by(
            '-created_at')

        # تطبيق البحث
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query) |
                Q(description__icontains=query) |
                Q(search_keywords__icontains=query)
            )

        # تطبيق التصفية
        if category_filter:
            category = Category.objects.get(id=category_filter)
            # الحصول على جميع الفئات الفرعية أيضًا
            subcategories = category.get_all_children(include_self=True)
            products = products.filter(category__in=subcategories)

        if brand_filter:
            products = products.filter(brand_id=brand_filter)

        if status_filter:
            products = products.filter(status=status_filter)

        # التصفح الجزئي
        paginator = Paginator(products, 20)  # 20 منتج في كل صفحة
        page = request.GET.get('page', 1)
        products_page = paginator.get_page(page)

        # جلب قوائم التصفية
        categories = Category.objects.filter(level=0)  # الفئات الرئيسية فقط
        brands = Brand.objects.all().order_by('name')

        # الإحصائيات
        stats = {
            'total': Product.objects.count(),
            'active': Product.objects.filter(is_active=True).count(),
            'out_of_stock': Product.objects.filter(stock_status='out_of_stock').count(),
            'featured': Product.objects.filter(is_featured=True).count(),
        }

        context = {
            'products': products_page,
            'categories': categories,
            'brands': brands,
            'query': query,
            'category_filter': category_filter,
            'brand_filter': brand_filter,
            'status_filter': status_filter,
            'stats': stats,
            'status_choices': Product.STATUS_CHOICES,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/products/products_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': products_page.has_next(),
                'has_prev': products_page.has_previous(),
                'page': products_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/products/product_list.html', context)


class ProductDetailView(DashboardAccessMixin, View):
    """عرض تفاصيل المنتج"""

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        # جلب البيانات المرتبطة
        variants = product.variants.all()
        images = product.images.all().order_by('sort_order')
        reviews = product.reviews.select_related('user').order_by('-created_at')[:10]
        attributes = product.attribute_values.select_related('attribute').all()
        related_products = product.related_products.all()

        # إحصائيات المبيعات
        sales_data = {
            'total_sales': product.sales_count,
            'avg_rating': product.rating,
            'review_count': product.review_count,
            'views': product.views_count,
            'wishlist_count': product.wishlist_count,
        }

        # معلومات المخزون
        stock_info = {
            'available': product.available_quantity,
            'reserved': product.reserved_quantity,
            'total': product.stock_quantity,
            'status': product.stock_status,
            'low_stock': product.low_stock,
        }

        context = {
            'product': product,
            'variants': variants,
            'images': images,
            'reviews': reviews,
            'attributes': attributes,
            'related_products': related_products,
            'sales_data': sales_data,
            'stock_info': stock_info,
        }

        return render(request, 'dashboard/products/product_detail.html', context)


class ProductFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث المنتج"""

    def get(self, request, product_id=None):
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            form_title = 'تحديث المنتج'
            images = product.images.all().order_by('sort_order')
            variants = product.variants.all()
            attributes = product.attribute_values.select_related('attribute').all()
        else:
            product = None
            form_title = 'إنشاء منتج جديد'
            images = []
            variants = []
            attributes = []

        # جلب البيانات اللازمة للنموذج
        categories = Category.objects.all()
        brands = Brand.objects.all().order_by('name')
        tags = Tag.objects.all().order_by('name')
        product_attributes = ProductAttribute.objects.all()

        context = {
            'product': product,
            'form_title': form_title,
            'categories': categories,
            'brands': brands,
            'tags': tags,
            'images': images,
            'variants': variants,
            'attributes': attributes,
            'product_attributes': product_attributes,
            'status_choices': Product.STATUS_CHOICES,
            'stock_status_choices': Product.STOCK_STATUS_CHOICES,
            'condition_choices': Product.CONDITION_CHOICES,
        }

        return render(request, 'dashboard/products/product_form.html', context)

    def post(self, request, product_id=None):
        # جمع البيانات الأساسية من النموذج
        name = request.POST.get('name')
        name_en = request.POST.get('name_en', '')
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand') or None
        sku = request.POST.get('sku', '')
        barcode = request.POST.get('barcode', '')
        description = request.POST.get('description', '')
        short_description = request.POST.get('short_description', '')

        # معالجة الأسعار والقيم العددية
        try:
            # تحويل القيم إلى أرقام عشرية وإدارة الأخطاء
            base_price_str = request.POST.get('base_price', '0').replace(',', '.')
            base_price = Decimal(base_price_str)

            if base_price < Decimal('0.01'):
                base_price = Decimal('0.01')

            compare_price_str = request.POST.get('compare_price', '') or None
            compare_price = round(float(compare_price_str.replace(',', '.')), 2) if compare_price_str else None

            cost_str = request.POST.get('cost', '') or None
            cost = round(float(cost_str.replace(',', '.')), 2) if cost_str else None

            tax_rate_str = request.POST.get('tax_rate', '16').replace(',', '.')
            tax_rate = round(float(tax_rate_str), 2) if tax_rate_str else 16.00

            stock_quantity_str = request.POST.get('stock_quantity', '0')
            stock_quantity = int(stock_quantity_str) if stock_quantity_str.strip() else 0

        except ValueError as e:
            messages.error(request, f'خطأ في تنسيق الأرقام: {str(e)}')
            return redirect(request.path)

        # الخصائص والحالة
        track_inventory = request.POST.get('track_inventory') == 'on'
        status = request.POST.get('status', 'draft')
        stock_status = request.POST.get('stock_status', 'in_stock')
        condition = request.POST.get('condition', 'new')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'

        # الخصائص البوليانية الأخرى
        is_new = request.POST.get('is_new') == 'on'
        is_digital = request.POST.get('is_digital') == 'on'
        requires_shipping = request.POST.get('requires_shipping') == 'on'
        is_best_seller = request.POST.get('is_best_seller') == 'on'

        # الأبعاد والوزن - معالجة القيم الفارغة
        weight_str = request.POST.get('weight', '') or None
        weight = float(weight_str.replace(',', '.')) if weight_str else None

        length_str = request.POST.get('length', '') or None
        length = float(length_str.replace(',', '.')) if length_str else None

        width_str = request.POST.get('width', '') or None
        width = float(width_str.replace(',', '.')) if width_str else None

        height_str = request.POST.get('height', '') or None
        height = float(height_str.replace(',', '.')) if height_str else None

        # التحقق من البيانات المطلوبة
        if not name or not category_id or base_price is None:
            messages.error(request, 'الرجاء ملء جميع الحقول المطلوبة: الاسم، الفئة، السعر الأساسي')
            return redirect(request.path)

        # إنشاء أو تحديث المنتج
        try:
            if product_id:
                product = get_object_or_404(Product, id=product_id)
                was_published = product.status == 'published'

                # تحديث الحقول
                product.name = name
                product.name_en = name_en
                product.category_id = category_id
                product.brand_id = brand_id
                product.sku = sku
                product.barcode = barcode
                product.description = description
                product.short_description = short_description
                product.base_price = base_price
                product.compare_price = compare_price
                product.cost = cost
                product.tax_rate = tax_rate
                product.stock_quantity = stock_quantity
                product.track_inventory = track_inventory
                product.status = status
                product.stock_status = stock_status
                product.condition = condition
                product.is_active = is_active
                product.is_featured = is_featured
                product.is_new = is_new
                product.is_best_seller = is_best_seller
                product.is_digital = is_digital
                product.requires_shipping = requires_shipping
                product.weight = weight
                product.length = length
                product.width = width
                product.height = height

                # تعيين تاريخ النشر إذا تم تغيير الحالة إلى منشور
                if status == 'published' and not was_published:
                    product.published_at = timezone.now()

                product.save()
                messages.success(request, 'تم تحديث المنتج بنجاح')
            else:
                # إنشاء سلج (slug) من الاسم
                slug = slugify(name, allow_unicode=True)

                # التحقق من فريدية السلج
                if Product.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                # إنشاء منتج جديد
                product = Product.objects.create(
                    name=name,
                    name_en=name_en,
                    slug=slug,
                    category_id=category_id,
                    brand_id=brand_id,
                    sku=sku or Product().generate_sku(),  # استخدام الدالة المساعدة لتوليد SKU
                    barcode=barcode,
                    description=description,
                    short_description=short_description,
                    base_price=base_price,
                    compare_price=compare_price,
                    cost=cost,
                    tax_rate=tax_rate,
                    stock_quantity=stock_quantity,
                    track_inventory=track_inventory,
                    status=status,
                    stock_status=stock_status,
                    condition=condition,
                    is_active=is_active,
                    is_featured=is_featured,
                    is_new=is_new,
                    is_best_seller=is_best_seller,
                    is_digital=is_digital,
                    requires_shipping=requires_shipping,
                    weight=weight,
                    length=length,
                    width=width,
                    height=height,
                    created_by=request.user,
                )

                if status == 'published':
                    product.published_at = timezone.now()
                    product.save()

                messages.success(request, 'تم إنشاء المنتج بنجاح')

            # معالجة الوسوم
            tag_ids = request.POST.getlist('tags')
            if tag_ids:
                product.tags.set(Tag.objects.filter(id__in=tag_ids))
            else:
                product.tags.clear()

            # معالجة خصائص المنتج
            attribute_data = {}
            for key, value in request.POST.items():
                if key.startswith('attribute_'):
                    attr_id = key.replace('attribute_', '')
                    attribute_data[attr_id] = value

            # حفظ الخصائص
            for attr_id, value in attribute_data.items():
                if value:  # لا تحفظ القيم الفارغة
                    try:
                        attribute = ProductAttribute.objects.get(id=attr_id)
                        attr_value, created = ProductAttributeValue.objects.update_or_create(
                            product=product,
                            attribute=attribute,
                            defaults={'value': value}
                        )
                    except Exception as e:
                        messages.warning(request, f'حدث خطأ في حفظ الخاصية: {str(e)}')

            # معالجة صور المنتج
            images = request.FILES.getlist('product_images')
            if images:
                for i, image_file in enumerate(images):
                    # إنشاء صورة جديدة
                    is_primary = i == 0 and not product.images.filter(is_primary=True).exists()
                    ProductImage.objects.create(
                        product=product,
                        image=image_file,
                        alt_text=product.name,
                        is_primary=is_primary,
                        sort_order=i
                    )

            # إذا تم تعيين صورة رئيسية جديدة
            primary_image_id = request.POST.get('primary_image')
            if primary_image_id:
                # إلغاء تحديد جميع الصور الرئيسية
                product.images.update(is_primary=False)
                # تعيين الصورة الجديدة كرئيسية
                ProductImage.objects.filter(id=primary_image_id).update(is_primary=True)

            # معالجة المواصفات (specifications) كبيانات JSON
            specs_data = request.POST.get('specifications_json', '{}')
            try:
                if specs_data.strip():
                    product.specifications = json.loads(specs_data)
                    product.save(update_fields=['specifications'])
            except json.JSONDecodeError:
                messages.warning(request, 'حدث خطأ في معالجة بيانات المواصفات')

            # معالجة الميزات (features)
            features_data = request.POST.get('features', '[]')
            try:
                if features_data.strip():
                    if features_data.startswith('{') or features_data.startswith('['):
                        # JSON format
                        product.features = json.loads(features_data)
                    else:
                        # Line-by-line format
                        product.features = [line.strip() for line in features_data.split('\n') if line.strip()]
                    product.save(update_fields=['features'])
            except json.JSONDecodeError:
                messages.warning(request, 'حدث خطأ في معالجة بيانات الميزات')

            # تحديث المنتجات ذات الصلة
            related_product_ids = request.POST.getlist('related_products')
            if related_product_ids:
                product.related_products.set(Product.objects.filter(id__in=related_product_ids))
            else:
                product.related_products.clear()

            return redirect('dashboard:dashboard_product_detail', product_id=str(product.id))

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ المنتج: {str(e)}')
            return redirect(request.path)


class ProductDeleteView(DashboardAccessMixin, View):
    """حذف المنتج"""

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        try:
            product_name = product.name
            product.delete()
            messages.success(request, f'تم حذف المنتج "{product_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف المنتج: {str(e)}')

        return redirect('dashboard_products')


class ProductBulkActionsView(DashboardAccessMixin, View):
    """عمليات مجمعة على المنتجات"""

    def post(self, request):
        action = request.POST.get('action')
        product_ids = request.POST.getlist('selected_products')

        if not product_ids:
            messages.error(request, 'لم يتم تحديد أي منتجات')
            return redirect('dashboard_products')

        products = Product.objects.filter(id__in=product_ids)
        count = products.count()

        if action == 'activate':
            products.update(is_active=True)
            messages.success(request, f'تم تفعيل {count} منتج بنجاح')

        elif action == 'deactivate':
            products.update(is_active=False)
            messages.success(request, f'تم إلغاء تفعيل {count} منتج بنجاح')

        elif action == 'publish':
            products.update(status='published', published_at=timezone.now())
            messages.success(request, f'تم نشر {count} منتج بنجاح')

        elif action == 'draft':
            products.update(status='draft')
            messages.success(request, f'تم تحويل {count} منتج إلى مسودة بنجاح')

        elif action == 'delete':
            try:
                products.delete()
                messages.success(request, f'تم حذف {count} منتج بنجاح')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حذف المنتجات: {str(e)}')

        elif action == 'update_stock':
            # هذا سيعيدنا إلى صفحة تحديث المخزون للمنتجات المحددة
            product_ids_str = ','.join(product_ids)
            return redirect(f'dashboard_update_stock?products={product_ids_str}')

        return redirect('dashboard_products')


# ========================= إدارة الفئات =========================

class CategoryListView(DashboardAccessMixin, View):
    """عرض قائمة الفئات"""

    def get(self, request):
        # الحصول على جميع الفئات مرتبة حسب المستوى
        categories = Category.objects.all().order_by('level', 'sort_order', 'name')

        # الإحصائيات
        stats = {
            'total': categories.count(),
            'active': categories.filter(is_active=True).count(),
            'featured': categories.filter(is_featured=True).count(),
            'root_categories': categories.filter(level=0).count(),
        }

        context = {
            'categories': categories,
            'stats': stats,
        }

        return render(request, 'dashboard/products/category_list.html', context)


class CategoryFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث الفئة"""

    def get(self, request, category_id=None):
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            form_title = 'تحديث الفئة'
        else:
            category = None
            form_title = 'إنشاء فئة جديدة'

        # الحصول على قائمة الفئات للاختيار كأب
        parent_categories = Category.objects.exclude(id=category_id if category_id else None)

        context = {
            'category': category,
            'form_title': form_title,
            'parent_categories': parent_categories,
        }

        return render(request, 'dashboard/products/category_form.html', context)

    def post(self, request, category_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        name_en = request.POST.get('name_en', '')
        parent_id = request.POST.get('parent') or None
        description = request.POST.get('description', '')
        description_en = request.POST.get('description_en', '')
        sort_order = request.POST.get('sort_order', 0)
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        show_in_menu = request.POST.get('show_in_menu') == 'on'

        # الحقول SEO
        meta_title = request.POST.get('meta_title', '')
        meta_description = request.POST.get('meta_description', '')
        meta_keywords = request.POST.get('meta_keywords', '')

        # التحقق من البيانات المطلوبة
        if not name:
            messages.error(request, 'اسم الفئة مطلوب')
            return redirect(request.path)

        # إنشاء سلج (slug) من الاسم
        slug = request.POST.get('slug') or slugify(name, allow_unicode=True)

        try:
            if category_id:
                # تحديث فئة موجودة
                category = get_object_or_404(Category, id=category_id)

                # التحقق من عدم اختيار الفئة نفسها كأب
                if parent_id and int(parent_id) == category.id:
                    messages.error(request, 'لا يمكن اختيار الفئة نفسها كفئة أب')
                    return redirect(request.path)

                # تحديث البيانات
                category.name = name
                category.name_en = name_en
                category.parent_id = parent_id
                category.description = description
                category.description_en = description_en
                category.sort_order = sort_order
                category.is_active = is_active
                category.is_featured = is_featured
                category.show_in_menu = show_in_menu
                category.meta_title = meta_title
                category.meta_description = meta_description
                category.meta_keywords = meta_keywords

                # تحديث السلج إذا تغير
                if slug != category.slug:
                    # التحقق من فريدية السلج
                    if Category.objects.filter(slug=slug).exclude(id=category_id).exists():
                        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
                    category.slug = slug

                category.save()
                messages.success(request, 'تم تحديث الفئة بنجاح')
            else:
                # التحقق من فريدية السلج
                if Category.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                # إنشاء فئة جديدة
                category = Category.objects.create(
                    name=name,
                    name_en=name_en,
                    slug=slug,
                    parent_id=parent_id,
                    description=description,
                    description_en=description_en,
                    sort_order=sort_order,
                    is_active=is_active,
                    is_featured=is_featured,
                    show_in_menu=show_in_menu,
                    meta_title=meta_title,
                    meta_description=meta_description,
                    meta_keywords=meta_keywords,
                    created_by=request.user,
                )
                messages.success(request, 'تم إنشاء الفئة بنجاح')

            # معالجة الصور المرفوعة
            image = request.FILES.get('image')
            if image:
                category.image = image

            banner_image = request.FILES.get('banner_image')
            if banner_image:
                category.banner_image = banner_image

            # حفظ التغييرات على الصور
            if image or banner_image:
                category.save()

            return redirect('dashboard:dashboard_categories')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ الفئة: {str(e)}')
            return redirect(request.path)


class CategoryDeleteView(DashboardAccessMixin, View):
    """حذف الفئة"""

    def post(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)

        # التحقق من وجود منتجات في هذه الفئة
        products_count = category.products.count()
        if products_count > 0:
            messages.error(request, f'لا يمكن حذف الفئة لأنها تحتوي على {products_count} منتج')
            return redirect('dashboard:dashboard_categories')

        # التحقق من وجود فئات فرعية
        if category.children.exists():
            messages.error(request, 'لا يمكن حذف الفئة لأنها تحتوي على فئات فرعية')
            return redirect('dashboard:dashboard_categories')

        try:
            category_name = category.name
            category.delete()
            messages.success(request, f'تم حذف الفئة "{category_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الفئة: {str(e)}')

        return redirect('dashboard:dashboard_categories')


# ========================= إدارة العلامات التجارية =========================

class BrandListView(DashboardAccessMixin, View):
    """عرض قائمة العلامات التجارية"""

    def get(self, request):
        # البحث
        query = request.GET.get('q', '')

        # قائمة العلامات التجارية
        brands = Brand.objects.all().order_by('name')

        # تطبيق البحث
        if query:
            brands = brands.filter(
                Q(name__icontains=query) |
                Q(name_en__icontains=query) |
                Q(country__icontains=query)
            )

        # التصفح الجزئي
        paginator = Paginator(brands, 20)  # 20 علامة تجارية في كل صفحة
        page = request.GET.get('page', 1)
        brands_page = paginator.get_page(page)

        # الإحصائيات
        stats = {
            'total': Brand.objects.count(),
            'featured': Brand.objects.filter(is_featured=True).count(),
            'verified': Brand.objects.filter(is_verified=True).count(),
        }

        context = {
            'brands': brands_page,
            'query': query,
            'stats': stats,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/products/brands_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': brands_page.has_next(),
                'has_prev': brands_page.has_previous(),
                'page': brands_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/products/brand_list.html', context)


class BrandFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث العلامة التجارية"""

    def get(self, request, brand_id=None):
        if brand_id:
            brand = get_object_or_404(Brand, id=brand_id)
            form_title = 'تحديث العلامة التجارية'
        else:
            brand = None
            form_title = 'إنشاء علامة تجارية جديدة'

        context = {
            'brand': brand,
            'form_title': form_title,
        }

        return render(request, 'dashboard/products/brand_form.html', context)

    def post(self, request, brand_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        name_en = request.POST.get('name_en', '')
        description = request.POST.get('description', '')
        country = request.POST.get('country', '')
        city = request.POST.get('city', '')
        website = request.POST.get('website', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        is_verified = request.POST.get('is_verified') == 'on'
        sort_order = request.POST.get('sort_order', 0)

        # الحقول SEO
        meta_title = request.POST.get('meta_title', '')
        meta_description = request.POST.get('meta_description', '')
        meta_keywords = request.POST.get('meta_keywords', '')

        # روابط التواصل الاجتماعي
        social_links = {}
        social_platforms = ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube']
        for platform in social_platforms:
            social_links[platform] = request.POST.get(f'social_{platform}', '')

        # التحقق من البيانات المطلوبة
        if not name:
            messages.error(request, 'اسم العلامة التجارية مطلوب')
            return redirect(request.path)

        # إنشاء سلج (slug) من الاسم
        slug = request.POST.get('slug') or slugify(name, allow_unicode=True)

        try:
            if brand_id:
                # تحديث علامة تجارية موجودة
                brand = get_object_or_404(Brand, id=brand_id)

                # تحديث البيانات
                brand.name = name
                brand.name_en = name_en
                brand.description = description
                brand.country = country
                brand.city = city
                brand.website = website
                brand.email = email
                brand.phone = phone
                brand.is_active = is_active
                brand.is_featured = is_featured
                brand.is_verified = is_verified
                brand.sort_order = sort_order
                brand.meta_title = meta_title
                brand.meta_description = meta_description
                brand.meta_keywords = meta_keywords
                brand.social_links = social_links

                # تحديث السلج إذا تغير
                if slug != brand.slug:
                    # التحقق من فريدية السلج
                    if Brand.objects.filter(slug=slug).exclude(id=brand_id).exists():
                        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
                    brand.slug = slug

                brand.save()
                messages.success(request, 'تم تحديث العلامة التجارية بنجاح')
            else:
                # التحقق من فريدية السلج
                if Brand.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                # إنشاء علامة تجارية جديدة
                brand = Brand.objects.create(
                    name=name,
                    name_en=name_en,
                    slug=slug,
                    description=description,
                    country=country,
                    city=city,
                    website=website,
                    email=email,
                    phone=phone,
                    is_active=is_active,
                    is_featured=is_featured,
                    is_verified=is_verified,
                    sort_order=sort_order,
                    meta_title=meta_title,
                    meta_description=meta_description,
                    meta_keywords=meta_keywords,
                    social_links=social_links,
                    created_by=request.user,
                )
                messages.success(request, 'تم إنشاء العلامة التجارية بنجاح')

            # معالجة الصور المرفوعة
            logo = request.FILES.get('logo')
            if logo:
                brand.logo = logo

            banner_image = request.FILES.get('banner_image')
            if banner_image:
                brand.banner_image = banner_image

            # حفظ التغييرات على الصور
            if logo or banner_image:
                brand.save()

            return redirect('dashboard_brands')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ العلامة التجارية: {str(e)}')
            return redirect(request.path)


class BrandDeleteView(DashboardAccessMixin, View):
    """حذف العلامة التجارية"""

    def post(self, request, brand_id):
        brand = get_object_or_404(Brand, id=brand_id)

        # التحقق من وجود منتجات لهذه العلامة التجارية
        products_count = brand.products.count()
        if products_count > 0:
            messages.error(request, f'لا يمكن حذف العلامة التجارية لأنها مرتبطة بـ {products_count} منتج')
            return redirect('dashboard_brands')

        try:
            brand_name = brand.name
            brand.delete()
            messages.success(request, f'تم حذف العلامة التجارية "{brand_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف العلامة التجارية: {str(e)}')

        return redirect('dashboard_brands')


# ========================= إدارة الخصومات =========================

class DiscountListView(DashboardAccessMixin, View):
    """عرض قائمة الخصومات"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        type_filter = request.GET.get('type', '')
        status_filter = request.GET.get('status', '')

        # قائمة الخصومات
        discounts = ProductDiscount.objects.all().order_by('-priority', '-start_date')

        # تطبيق البحث
        if query:
            discounts = discounts.filter(
                Q(name__icontains=query) |
                Q(code__icontains=query) |
                Q(description__icontains=query)
            )

        # تطبيق التصفية
        if type_filter:
            discounts = discounts.filter(discount_type=type_filter)

        if status_filter == 'active':
            discounts = discounts.filter(is_active=True)
        elif status_filter == 'inactive':
            discounts = discounts.filter(is_active=False)
        elif status_filter == 'expired':
            discounts = discounts.filter(end_date__lt=timezone.now())
        elif status_filter == 'upcoming':
            discounts = discounts.filter(start_date__gt=timezone.now())

        # التصفح الجزئي
        paginator = Paginator(discounts, 20)  # 20 خصم في كل صفحة
        page = request.GET.get('page', 1)
        discounts_page = paginator.get_page(page)

        # الإحصائيات
        stats = {
            'total': ProductDiscount.objects.count(),
            'active': ProductDiscount.objects.filter(is_active=True).count(),
            'expired': ProductDiscount.objects.filter(end_date__lt=timezone.now()).count(),
        }

        context = {
            'discounts': discounts_page,
            'query': query,
            'type_filter': type_filter,
            'status_filter': status_filter,
            'stats': stats,
            'discount_types': ProductDiscount.DISCOUNT_TYPE_CHOICES,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/products/discounts_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': discounts_page.has_next(),
                'has_prev': discounts_page.has_previous(),
                'page': discounts_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/products/discount_list.html', context)


class DiscountFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث الخصم"""

    def get(self, request, discount_id=None):
        if discount_id:
            discount = get_object_or_404(ProductDiscount, id=discount_id)
            form_title = 'تحديث الخصم'
            selected_products = discount.products.all()
        else:
            discount = None
            form_title = 'إنشاء خصم جديد'
            selected_products = []

        # جلب الفئات والمنتجات
        categories = Category.objects.filter(is_active=True)
        products = Product.objects.filter(is_active=True, status='published').order_by('name')[
                   :100]  # عرض أول 100 منتج فقط للاختيار

        context = {
            'discount': discount,
            'form_title': form_title,
            'selected_products': selected_products,
            'categories': categories,
            'products': products,
            'discount_types': ProductDiscount.DISCOUNT_TYPE_CHOICES,
            'application_types': ProductDiscount.APPLICATION_TYPE_CHOICES,
        }

        return render(request, 'dashboard/products/discount_form.html', context)

    def post(self, request, discount_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        code = request.POST.get('code', '')
        discount_type = request.POST.get('discount_type')
        value = request.POST.get('value')
        max_discount_amount = request.POST.get('max_discount_amount') or None

        application_type = request.POST.get('application_type')
        category_id = request.POST.get('category') or None
        product_ids = request.POST.getlist('products')

        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None

        min_purchase_amount = request.POST.get('min_purchase_amount') or None
        min_quantity = request.POST.get('min_quantity') or None
        max_uses = request.POST.get('max_uses') or None
        max_uses_per_user = request.POST.get('max_uses_per_user') or None

        buy_quantity = request.POST.get('buy_quantity') or None
        get_quantity = request.POST.get('get_quantity') or None
        get_discount_percentage = request.POST.get('get_discount_percentage', 100) or 100

        is_active = request.POST.get('is_active') == 'on'
        is_stackable = request.POST.get('is_stackable') == 'on'
        requires_coupon_code = request.POST.get('requires_coupon_code') == 'on'
        priority = request.POST.get('priority', 0)

        # التحقق من البيانات المطلوبة
        if not name or not discount_type or not value:
            messages.error(request, 'الرجاء ملء جميع الحقول المطلوبة: الاسم، نوع الخصم، قيمة الخصم')
            return redirect(request.path)

        # تحويل التواريخ من نص إلى كائنات datetime
        import datetime
        try:
            start_date = timezone.make_aware(datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M'))
            if end_date:
                end_date = timezone.make_aware(datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M'))
        except ValueError:
            messages.error(request, 'صيغة التاريخ غير صحيحة')
            return redirect(request.path)

        try:
            if discount_id:
                # تحديث خصم موجود
                discount = get_object_or_404(ProductDiscount, id=discount_id)

                # تحديث البيانات
                discount.name = name
                discount.description = description
                discount.code = code
                discount.discount_type = discount_type
                discount.value = value
                discount.max_discount_amount = max_discount_amount
                discount.application_type = application_type
                discount.category_id = category_id
                discount.start_date = start_date
                discount.end_date = end_date
                discount.min_purchase_amount = min_purchase_amount
                discount.min_quantity = min_quantity
                discount.max_uses = max_uses
                discount.max_uses_per_user = max_uses_per_user
                discount.buy_quantity = buy_quantity
                discount.get_quantity = get_quantity
                discount.get_discount_percentage = get_discount_percentage
                discount.is_active = is_active
                discount.is_stackable = is_stackable
                discount.requires_coupon_code = requires_coupon_code
                discount.priority = priority

                discount.save()
                messages.success(request, 'تم تحديث الخصم بنجاح')
            else:
                # إنشاء خصم جديد
                discount = ProductDiscount.objects.create(
                    name=name,
                    description=description,
                    code=code,
                    discount_type=discount_type,
                    value=value,
                    max_discount_amount=max_discount_amount,
                    application_type=application_type,
                    category_id=category_id,
                    start_date=start_date,
                    end_date=end_date,
                    min_purchase_amount=min_purchase_amount,
                    min_quantity=min_quantity,
                    max_uses=max_uses,
                    max_uses_per_user=max_uses_per_user,
                    buy_quantity=buy_quantity,
                    get_quantity=get_quantity,
                    get_discount_percentage=get_discount_percentage,
                    is_active=is_active,
                    is_stackable=is_stackable,
                    requires_coupon_code=requires_coupon_code,
                    priority=priority,
                    created_by=request.user,
                )
                messages.success(request, 'تم إنشاء الخصم بنجاح')

            # تحديث المنتجات المرتبطة
            if product_ids and application_type == 'specific_products':
                discount.products.set(Product.objects.filter(id__in=product_ids))
            else:
                discount.products.clear()

            return redirect('dashboard_discounts')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ الخصم: {str(e)}')
            return redirect(request.path)


class DiscountDeleteView(DashboardAccessMixin, View):
    """حذف الخصم"""

    def post(self, request, discount_id):
        discount = get_object_or_404(ProductDiscount, id=discount_id)

        try:
            discount_name = discount.name
            discount.delete()
            messages.success(request, f'تم حذف الخصم "{discount_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الخصم: {str(e)}')

        return redirect('dashboard_discounts')


# ========================= إدارة التقييمات =========================

class ReviewListView(DashboardAccessMixin, View):
    """عرض قائمة تقييمات المنتجات"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        rating_filter = request.GET.get('rating', '')
        status_filter = request.GET.get('status', '')

        # قائمة التقييمات
        reviews = ProductReview.objects.select_related('user', 'product').order_by('-created_at')

        # تطبيق البحث
        if query:
            reviews = reviews.filter(
                Q(product__name__icontains=query) |
                Q(user__username__icontains=query) |
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )

        # تطبيق التصفية
        if rating_filter:
            reviews = reviews.filter(rating=rating_filter)

        if status_filter == 'approved':
            reviews = reviews.filter(is_approved=True)
        elif status_filter == 'pending':
            reviews = reviews.filter(is_approved=False)
        elif status_filter == 'featured':
            reviews = reviews.filter(is_featured=True)
        elif status_filter == 'reported':
            reviews = reviews.filter(report_count__gt=0)

        # التصفح الجزئي
        paginator = Paginator(reviews, 20)  # 20 تقييم في كل صفحة
        page = request.GET.get('page', 1)
        reviews_page = paginator.get_page(page)

        # الإحصائيات
        stats = {
            'total': ProductReview.objects.count(),
            'approved': ProductReview.objects.filter(is_approved=True).count(),
            'pending': ProductReview.objects.filter(is_approved=False).count(),
            'reported': ProductReview.objects.filter(report_count__gt=0).count(),
        }

        context = {
            'reviews': reviews_page,
            'query': query,
            'rating_filter': rating_filter,
            'status_filter': status_filter,
            'stats': stats,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/products/reviews_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': reviews_page.has_next(),
                'has_prev': reviews_page.has_previous(),
                'page': reviews_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/products/review_list.html', context)


class ReviewDetailView(DashboardAccessMixin, View):
    """عرض تفاصيل التقييم"""

    def get(self, request, review_id):
        review = get_object_or_404(ProductReview, id=review_id)

        # جلب الصور المرتبطة بالتقييم
        images = review.images.all()

        context = {
            'review': review,
            'images': images,
            'product': review.product,
        }

        return render(request, 'dashboard/products/review_detail.html', context)


@require_POST
def review_action(request, review_id):
    """إجراءات على التقييم (موافقة، رفض، تمييز)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'غير مصرح لك بهذا الإجراء'}, status=403)

    review = get_object_or_404(ProductReview, id=review_id)
    action = request.POST.get('action')

    if action == 'approve':
        review.is_approved = True
        review.approved_at = timezone.now()
        review.approved_by = request.user
        review.save()
        return JsonResponse({'success': True, 'message': 'تمت الموافقة على التقييم بنجاح'})

    elif action == 'reject':
        review.is_approved = False
        review.save()
        return JsonResponse({'success': True, 'message': 'تم رفض التقييم بنجاح'})

    elif action == 'feature':
        review.is_featured = True
        review.save()
        return JsonResponse({'success': True, 'message': 'تم تمييز التقييم بنجاح'})

    elif action == 'unfeature':
        review.is_featured = False
        review.save()
        return JsonResponse({'success': True, 'message': 'تم إلغاء تمييز التقييم بنجاح'})

    elif action == 'delete':
        review.delete()
        return JsonResponse({'success': True, 'message': 'تم حذف التقييم بنجاح'})

    return JsonResponse({'success': False, 'message': 'إجراء غير صالح'}, status=400)


# ========================= إدارة الوسوم =========================

class TagListView(DashboardAccessMixin, View):
    """عرض قائمة الوسوم"""

    def get(self, request):
        # البحث
        query = request.GET.get('q', '')

        # قائمة الوسوم
        tags = Tag.objects.all().order_by('-usage_count', 'name')

        # تطبيق البحث
        if query:
            tags = tags.filter(name__icontains=query)

        # الإحصائيات
        stats = {
            'total': Tag.objects.count(),
            'featured': Tag.objects.filter(is_featured=True).count(),
            'most_used': Tag.objects.order_by('-usage_count').first(),
        }

        context = {
            'tags': tags,
            'query': query,
            'stats': stats,
        }

        return render(request, 'dashboard/products/tag_list.html', context)


class TagFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث الوسم"""

    def get(self, request, tag_id=None):
        if tag_id:
            tag = get_object_or_404(Tag, id=tag_id)
            form_title = 'تحديث الوسم'
        else:
            tag = None
            form_title = 'إنشاء وسم جديد'

        context = {
            'tag': tag,
            'form_title': form_title,
        }

        return render(request, 'dashboard/products/tag_form.html', context)

    def post(self, request, tag_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '')
        icon = request.POST.get('icon', '')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'

        # التحقق من البيانات المطلوبة
        if not name:
            messages.error(request, 'اسم الوسم مطلوب')
            return redirect(request.path)

        # إنشاء سلج (slug) من الاسم
        slug = slugify(name, allow_unicode=True)

        try:
            if tag_id:
                # تحديث وسم موجود
                tag = get_object_or_404(Tag, id=tag_id)

                # تحديث البيانات
                tag.name = name
                tag.description = description
                tag.color = color
                tag.icon = icon
                tag.is_active = is_active
                tag.is_featured = is_featured

                # تحديث السلج إذا تغير الاسم
                if tag.name != name:
                    # التحقق من فريدية السلج
                    if Tag.objects.filter(slug=slug).exclude(id=tag_id).exists():
                        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
                    tag.slug = slug

                tag.save()
                messages.success(request, 'تم تحديث الوسم بنجاح')
            else:
                # التحقق من فريدية السلج
                if Tag.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                # إنشاء وسم جديد
                tag = Tag.objects.create(
                    name=name,
                    slug=slug,
                    description=description,
                    color=color,
                    icon=icon,
                    is_active=is_active,
                    is_featured=is_featured,
                )
                messages.success(request, 'تم إنشاء الوسم بنجاح')

            return redirect('dashboard_tags')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ الوسم: {str(e)}')
            return redirect(request.path)


class TagDeleteView(DashboardAccessMixin, View):
    """حذف الوسم"""

    def post(self, request, tag_id):
        tag = get_object_or_404(Tag, id=tag_id)

        # التحقق من وجود منتجات مرتبطة بهذا الوسم
        products_count = tag.products.count()
        if products_count > 0:
            messages.error(request, f'لا يمكن حذف الوسم لأنه مرتبط بـ {products_count} منتج')
            return redirect('dashboard_tags')

        try:
            tag_name = tag.name
            tag.delete()
            messages.success(request, f'تم حذف الوسم "{tag_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الوسم: {str(e)}')

        return redirect('dashboard_tags')