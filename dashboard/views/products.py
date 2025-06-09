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
from dashboard.forms.products import ProductForm
from django.utils.translation import gettext as _


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
    """عرض إنشاء وتحديث المنتج باستخدام نموذج Django"""

    def get(self, request, product_id=None):
        """عرض نموذج إنشاء أو تحديث المنتج"""
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            form = ProductForm(instance=product)
            form_title = _('تحديث المنتج')
            images = product.images.all().order_by('sort_order')

            # تحميل المواصفات والميزات إلى النموذج
            form.initial['specifications_json'] = json.dumps(product.specifications, indent=4, ensure_ascii=False)

            # تحميل الميزات
            if product.features:
                if isinstance(product.features, list):
                    form.initial['features_json'] = json.dumps(product.features, indent=4, ensure_ascii=False)
                else:
                    # تحويل من أشكال أخرى إلى قائمة
                    try:
                        form.initial['features_json'] = json.dumps(list(product.features), indent=4, ensure_ascii=False)
                    except:
                        form.initial['features_json'] = '[]'

            # تحميل المنتجات ذات الصلة
            form.initial['related_products'] = product.related_products.all()

            # تحميل منتجات البيع المتقاطع والتصاعدي
            cross_sell_products = product.cross_sell_products.all()
            upsell_products = product.upsell_products.all()

            # تحميل صفات المنتج
            product_attributes = []
            for attr_value in product.attribute_values.select_related('attribute').all():
                form.initial[f'attribute_{attr_value.attribute_id}'] = attr_value.value
                product_attributes.append(attr_value.attribute)

            # تحميل متغيرات المنتج
            product_variants = product.variants.all().order_by('sort_order')
            # تحويل المتغيرات إلى JSON لاستخدامها في JavaScript
            variants_json = self.prepare_variants_json(product_variants)

        else:
            product = None
            form = ProductForm()
            form_title = _('إنشاء منتج جديد')
            images = []
            cross_sell_products = []
            upsell_products = []
            product_variants = []
            variants_json = '[]'
            product_attributes = []

        # تحميل البيانات اللازمة للقالب
        context = {
            'form': form,
            'product': product,
            'form_title': form_title,
            'images': images,
            'cross_sell_products': cross_sell_products,
            'upsell_products': upsell_products,
            'product_variants': product_variants,
            'variants_json': variants_json,
            'product_attributes': product_attributes,  # إضافة صفات المنتج إلى السياق
            'status_choices': Product.STATUS_CHOICES,
            'stock_status_choices': Product.STOCK_STATUS_CHOICES,
            'condition_choices': Product.CONDITION_CHOICES,
        }

        return render(request, 'dashboard/products/product_form.html', context)

    def post(self, request, product_id=None):
        """معالجة نموذج إنشاء أو تحديث المنتج"""
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            form = ProductForm(request.POST, request.FILES, instance=product)
        else:
            product = None
            form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # حفظ المنتج
                product = form.save(commit=True, user=request.user)

                # معالجة صور المنتج
                images = request.FILES.getlist('product_images')
                if images:
                    for i, image_file in enumerate(images):
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

                # معالجة صفات المنتج
                self.process_product_attributes(request, product)

                # معالجة متغيرات المنتج
                self.process_product_variants(request, product)


                # حفظ منتجات البيع المتقاطع إذا تم إرسالها
                cross_sell_ids = request.POST.getlist('cross_sell_products')
                if cross_sell_ids:
                    product.cross_sell_products.set(Product.objects.filter(id__in=cross_sell_ids))

                # حفظ منتجات البيع التصاعدي إذا تم إرسالها
                upsell_ids = request.POST.getlist('upsell_products')
                if upsell_ids:
                    product.upsell_products.set(Product.objects.filter(id__in=upsell_ids))

                messages.success(request, _('تم حفظ المنتج بنجاح'))

                # تحديد ما إذا كان يجب الاستمرار في التحرير أم العودة إلى صفحة التفاصيل
                if 'save_and_continue' in request.POST:
                    return redirect('dashboard:dashboard_product_edit', product_id=str(product.id))
                else:
                    return redirect('dashboard:dashboard_product_detail', product_id=str(product.id))

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حفظ المنتج: {str(e)}')
        else:
            # في حالة وجود أخطاء في النموذج
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")

        # تحميل البيانات اللازمة للقالب في حالة وجود خطأ
        images = []
        cross_sell_products = []
        upsell_products = []
        product_variants = []
        variants_json = '[]'
        product_attributes = []

        if product:
            images = product.images.all().order_by('sort_order')
            cross_sell_products = product.cross_sell_products.all()
            upsell_products = product.upsell_products.all()
            product_variants = product.variants.all().order_by('sort_order')
            variants_json = self.prepare_variants_json(product_variants)

            # تحميل صفات المنتج
            for attr_value in product.attribute_values.select_related('attribute').all():
                product_attributes.append(attr_value.attribute)

        context = {
            'form': form,
            'product': product,
            'form_title': _('تحديث المنتج') if product_id else _('إنشاء منتج جديد'),
            'images': images,
            'cross_sell_products': cross_sell_products,
            'upsell_products': upsell_products,
            'product_variants': product_variants,
            'variants_json': variants_json,
            'product_attributes': product_attributes,
            'status_choices': Product.STATUS_CHOICES,
            'stock_status_choices': Product.STOCK_STATUS_CHOICES,
            'condition_choices': Product.CONDITION_CHOICES,
        }

        return render(request, 'dashboard/products/product_form.html', context)

    def prepare_variants_json(self, variants):
        """تحويل متغيرات المنتج إلى تنسيق JSON للاستخدام في JavaScript"""
        variants_data = []
        for variant in variants:
            variant_data = {
                'id': variant.id,
                'name': variant.name,
                'sku': variant.sku,
                'attributes': variant.attributes,
                'base_price': float(variant.base_price) if variant.base_price else None,
                'stock_quantity': variant.stock_quantity,
                'is_active': variant.is_active,
                'is_default': variant.is_default,
                'sort_order': variant.sort_order
            }
            variants_data.append(variant_data)
        return json.dumps(variants_data, ensure_ascii=False)

    def process_product_attributes(self, request, product):
        """معالجة صفات المنتج من النموذج"""
        # البحث عن جميع حقول صفات المنتج في النموذج
        attribute_fields = [field for field in request.POST if field.startswith('attribute_')]

        # جمع معرفات الخصائص المحذوفة
        deleted_attributes = []
        if request.POST.get('deleted_attributes'):
            try:
                deleted_attributes = json.loads(request.POST.get('deleted_attributes'))
            except json.JSONDecodeError:
                pass

        # حذف قيم الخصائص المحذوفة
        if deleted_attributes:
            ProductAttributeValue.objects.filter(
                product=product,
                attribute_id__in=deleted_attributes
            ).delete()

        # معالجة الخصائص الجديدة
        new_attribute_fields = [field for field in attribute_fields if field.startswith('attribute_new_')]
        for field in new_attribute_fields:
            try:
                # استخراج معرف الخاصية المؤقت من اسم الحقل (attribute_new_123456789 -> new_123456789)
                temp_id = field.split('_', 1)[1]

                # الحصول على اسم ونوع الخاصية الجديدة
                name = request.POST.get(f'new_attribute_name_{temp_id}', '').strip()
                attr_type = request.POST.get(f'new_attribute_type_{temp_id}', 'text').strip()
                options = request.POST.get(f'new_attribute_options_{temp_id}', '').strip()
                value = request.POST.get(field, '').strip()

                if name and value:
                    # إنشاء خاصية جديدة
                    options_list = []
                    if options and (attr_type == 'select' or attr_type == 'multiselect'):
                        options_list = [opt.strip() for opt in options.split(',') if opt.strip()]

                    # إنشاء سلج فريد للخاصية
                    slug = slugify(name, allow_unicode=True)
                    if ProductAttribute.objects.filter(slug=slug).exists():
                        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                    # إنشاء الخاصية
                    attribute = ProductAttribute.objects.create(
                        name=name,
                        slug=slug,
                        attribute_type=attr_type,
                        options=options_list if options_list else []
                    )

                    # إنشاء قيمة الخاصية للمنتج
                    ProductAttributeValue.objects.create(
                        product=product,
                        attribute=attribute,
                        value=value
                    )
            except Exception as e:
                # تسجيل الخطأ ومتابعة المعالجة
                print(f"خطأ في معالجة الخاصية الجديدة: {str(e)}")

        # معالجة الخصائص الموجودة
        for field in attribute_fields:
            if field.startswith('attribute_new_'):
                continue  # تمت معالجة الخصائص الجديدة بالفعل

            try:
                # استخراج معرف الصفة من اسم الحقل (attribute_123 -> 123)
                attribute_id = field.split('_')[1]
                if attribute_id in deleted_attributes:
                    continue  # تخطي الخصائص المحذوفة

                value = request.POST.get(field, '').strip()

                if value:  # تخطي القيم الفارغة
                    # التحقق من وجود الصفة
                    try:
                        attribute = ProductAttribute.objects.get(id=attribute_id)

                        # إنشاء أو تحديث قيمة الصفة
                        ProductAttributeValue.objects.update_or_create(
                            product=product,
                            attribute=attribute,
                            defaults={'value': value}
                        )
                    except ProductAttribute.DoesNotExist:
                        pass  # تجاهل الصفات غير الموجودة
            except (ValueError, IndexError):
                pass  # تجاهل الأخطاء في تنسيق اسم الحقل

    def process_product_variants(self, request, product):
        """معالجة متغيرات المنتج من النموذج مع منع تكرار الأسماء"""
        import json

        # الحصول على المتغيرات من النموذج
        variants_json = request.POST.get('product_variants_json', '[]')
        deleted_variants_json = request.POST.get('deleted_variants_json', '[]')

        try:
            # تحويل البيانات من JSON
            variants_data = json.loads(variants_json) if variants_json.strip() else []
            deleted_variants = json.loads(deleted_variants_json) if deleted_variants_json.strip() else []

            # حذف المتغيرات المحددة للحذف
            if deleted_variants:
                ProductVariant.objects.filter(id__in=deleted_variants, product=product).delete()

            # الحصول على المتغيرات الموجودة للمنتج لمنع تكرار الأسماء
            existing_variants = {}
            for variant in ProductVariant.objects.filter(product=product):
                existing_variants[variant.name] = variant.id

            # تحديث/إنشاء المتغيرات
            for variant_data in variants_data:
                variant_id = variant_data.get('id')
                variant_name = variant_data.get('name', '').strip()

                # تخطي المتغيرات بدون اسم
                if not variant_name:
                    continue

                # تخطي المتغيرات ذات المعرفات السالبة (المتغيرات المؤقتة)
                if variant_id and int(variant_id) < 0:
                    variant_id = None

                # منع تكرار الأسماء للمتغيرات الجديدة
                if not variant_id and variant_name in existing_variants:
                    # إضافة رقم للاسم لمنع التكرار
                    base_name = variant_name
                    counter = 1
                    while variant_name in existing_variants:
                        variant_name = f"{base_name} ({counter})"
                        counter += 1

                # الإعدادات الافتراضية للمتغير
                defaults = {
                    'name': variant_name,
                    'sku': variant_data.get('sku', ''),
                    'attributes': variant_data.get('attributes', {}),
                    'is_active': variant_data.get('is_active', True),
                    'is_default': variant_data.get('is_default', False),
                    'sort_order': variant_data.get('sort_order', 0),
                }

                # إضافة السعر إذا تم توفيره
                if 'base_price' in variant_data and variant_data.get('base_price') not in [None, '']:
                    try:
                        defaults['base_price'] = float(variant_data.get('base_price'))
                    except (ValueError, TypeError):
                        pass

                # إضافة كمية المخزون
                if 'stock_quantity' in variant_data and variant_data.get('stock_quantity') not in [None, '']:
                    try:
                        defaults['stock_quantity'] = int(variant_data.get('stock_quantity'))
                    except (ValueError, TypeError):
                        defaults['stock_quantity'] = 0

                # تحديث أو إنشاء المتغير
                if variant_id and int(variant_id) > 0:
                    # تحديث متغير موجود
                    try:
                        variant = ProductVariant.objects.get(id=variant_id, product=product)

                        # منع تكرار الأسماء عند التحديث
                        if variant.name != variant_name and variant_name in existing_variants and existing_variants[
                            variant_name] != variant_id:
                            base_name = variant_name
                            counter = 1
                            while variant_name in existing_variants and existing_variants[variant_name] != variant_id:
                                variant_name = f"{base_name} ({counter})"
                                counter += 1
                            defaults['name'] = variant_name

                        # تحديث المتغير
                        for key, value in defaults.items():
                            setattr(variant, key, value)
                        variant.save()

                        # تحديث القاموس
                        existing_variants[variant_name] = variant.id

                    except ProductVariant.DoesNotExist:
                        # إنشاء متغير جديد
                        defaults['product'] = product
                        new_variant = ProductVariant.objects.create(**defaults)
                        existing_variants[variant_name] = new_variant.id
                else:
                    # إنشاء متغير جديد
                    # إنشاء SKU إذا لم يتم توفيره
                    if not defaults.get('sku'):
                        base_sku = product.sku
                        variant_count = product.variants.count() + 1
                        defaults['sku'] = f"{base_sku}-{variant_count}"

                    # إنشاء المتغير
                    defaults['product'] = product
                    new_variant = ProductVariant.objects.create(**defaults)
                    existing_variants[variant_name] = new_variant.id

            # التأكد من وجود متغير افتراضي واحد فقط
            default_variants = product.variants.filter(is_default=True)
            if default_variants.count() > 1:
                first_default = default_variants.first()
                product.variants.filter(is_default=True).exclude(id=first_default.id).update(is_default=False)

            return True

        except Exception as e:
            # تسجيل الخطأ
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"خطأ في معالجة متغيرات المنتج: {str(e)}")
            print(f"خطأ في معالجة متغيرات المنتج: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"خطأ في معالجة متغيرات المنتج: {str(e)}")


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

    def post(self, request, product_id=None):
        # استرجاع المنتج إذا كنا في وضع التحرير
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            form_title = 'تحديث المنتج'
            images = product.images.all().order_by('sort_order')
            variants = product.variants.all()
        else:
            product = None
            form_title = 'إنشاء منتج جديد'
            images = []
            variants = []

        # جمع كل البيانات من النموذج
        form_data = request.POST.copy()
        form_files = request.FILES.copy()

        # قائمة للأخطاء
        errors = []

        # التحقق من الحقول المطلوبة

        # 1. اسم المنتج (مطلوب، على الأقل حرفين)
        name = form_data.get('name', '').strip()
        if not name:
            errors.append("اسم المنتج مطلوب")
        elif len(name) < 2:
            errors.append("اسم المنتج يجب أن يكون على الأقل حرفين")

        # 2. الفئة (مطلوبة)
        category_id = form_data.get('category')
        if not category_id:
            errors.append("يجب اختيار فئة للمنتج")

        # 3. السعر الأساسي (مطلوب، أكبر من 0.01)
        try:
            base_price_str = form_data.get('base_price', '0').replace(',', '.')
            base_price = Decimal(base_price_str)
            if base_price < Decimal('0.01'):
                errors.append("السعر الأساسي يجب أن يكون أكبر من صفر")
        except (ValueError, InvalidOperation):
            errors.append("صيغة السعر الأساسي غير صحيحة")

        # 4. الوصف الكامل (مطلوب، على الأقل 20 حرفًا)
        description = form_data.get('description', '').strip()
        if not description:
            errors.append("وصف المنتج مطلوب")
        elif len(description) < 20:
            errors.append("وصف المنتج يجب أن يكون على الأقل 20 حرفًا")

        # 5. الوصف المختصر (اختياري، لكن إذا أُدخل يجب أن يكون على الأقل 10 أحرف)
        short_description = form_data.get('short_description', '').strip()
        if short_description and len(short_description) < 10:
            errors.append("الوصف المختصر يجب أن يكون على الأقل 10 أحرف أو تركه فارغًا")

        # التحقق من تنسيق JSON
        try:
            specs_data = form_data.get('specifications_json', '{}')
            if specs_data.strip():
                json.loads(specs_data)
        except json.JSONDecodeError:
            errors.append("تنسيق JSON غير صحيح في حقل المواصفات")

        try:
            features_data = form_data.get('features', '[]')
            if features_data.strip():
                if features_data.startswith('{') or features_data.startswith('['):
                    json.loads(features_data)
        except json.JSONDecodeError:
            errors.append("تنسيق JSON غير صحيح في حقل الميزات")

        # إذا كانت هناك أخطاء، نعيد عرض النموذج مع رسائل الخطأ
        if errors:
            for error in errors:
                messages.error(request, error)

            # جلب البيانات اللازمة للنموذج
            categories = Category.objects.all()
            brands = Brand.objects.all().order_by('name')
            tags = Tag.objects.all().order_by('name')
            product_attributes = ProductAttribute.objects.all()

            # تحضير البيانات المدخلة مسبقًا
            selected_tags = request.POST.getlist('tags')

            # إعداد سياق العرض مع البيانات المدخلة سابقًا
            context = {
                'product': product,
                'form_title': form_title,
                'categories': categories,
                'brands': brands,
                'tags': tags,
                'images': images,
                'variants': variants,
                'product_attributes': product_attributes,
                'status_choices': Product.STATUS_CHOICES,
                'stock_status_choices': Product.STOCK_STATUS_CHOICES,
                'condition_choices': Product.CONDITION_CHOICES,

                # البيانات المدخلة سابقًا
                'form_data': form_data,
                'selected_category': category_id,
                'selected_brand': form_data.get('brand'),
                'selected_tags': selected_tags,
                'specifications_json': specs_data,
                'features_json': features_data,

                # إعادة تحميل العناصر المرفوعة
                'form_files': form_files
            }

            return render(request, 'dashboard/products/product_form.html', context)

        # إذا لم تكن هناك أخطاء، نستمر في حفظ المنتج
        try:
            # البيانات الإضافية
            name_en = form_data.get('name_en', '')
            brand_id = form_data.get('brand') or None
            sku = form_data.get('sku', '')
            barcode = form_data.get('barcode', '')

            # البيانات البوليانية
            is_active = 'is_active' in form_data
            is_featured = 'is_featured' in form_data
            is_new = 'is_new' in form_data
            is_best_seller = 'is_best_seller' in form_data
            is_digital = 'is_digital' in form_data
            requires_shipping = 'requires_shipping' in form_data

            # الأرقام الإضافية
            compare_price_str = form_data.get('compare_price', '')
            compare_price = Decimal(compare_price_str.replace(',', '.')) if compare_price_str.strip() else None

            cost_str = form_data.get('cost', '')
            cost = Decimal(cost_str.replace(',', '.')) if cost_str.strip() else None

            tax_rate_str = form_data.get('tax_rate', '16')
            tax_rate = Decimal(tax_rate_str.replace(',', '.')) if tax_rate_str.strip() else Decimal('16')

            stock_quantity_str = form_data.get('stock_quantity', '0')
            stock_quantity = int(stock_quantity_str) if stock_quantity_str.strip() else 0

            # حالات المنتج
            status = form_data.get('status', 'draft')
            stock_status = form_data.get('stock_status', 'in_stock')
            condition = form_data.get('condition', 'new')

            # الأبعاد والوزن
            weight_str = form_data.get('weight', '')
            weight = float(weight_str.replace(',', '.')) if weight_str.strip() else None

            length_str = form_data.get('length', '')
            length = float(length_str.replace(',', '.')) if length_str.strip() else None

            width_str = form_data.get('width', '')
            width = float(width_str.replace(',', '.')) if width_str.strip() else None

            height_str = form_data.get('height', '')
            height = float(height_str.replace(',', '.')) if height_str.strip() else None

            # إنشاء أو تحديث المنتج
            if product_id:
                # تحديث منتج موجود
                was_published = product.status == 'published'

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
                # إنشاء سلج من الاسم
                slug = slugify(name, allow_unicode=True)
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

            # معالجة المواصفات
            specs_data = request.POST.get('specifications_json', '{}')
            try:
                if specs_data.strip():
                    product.specifications = json.loads(specs_data)
                    product.save(update_fields=['specifications'])
            except json.JSONDecodeError:
                messages.warning(request, 'حدث خطأ في معالجة بيانات المواصفات')

            # معالجة الميزات
            features_data = request.POST.get('features', '[]')
            try:
                if features_data.strip():
                    if features_data.startswith('{') or features_data.startswith('['):
                        product.features = json.loads(features_data)
                    else:
                        product.features = [line.strip() for line in features_data.split('\n') if line.strip()]
                    product.save(update_fields=['features'])
            except json.JSONDecodeError:
                messages.warning(request, 'حدث خطأ في معالجة بيانات الميزات')

            # معالجة صور المنتج
            images = request.FILES.getlist('product_images')
            if images:
                for i, image_file in enumerate(images):
                    is_primary = i == 0 and not product.images.filter(is_primary=True).exists()
                    ProductImage.objects.create(
                        product=product,
                        image=image_file,
                        alt_text=product.name,
                        is_primary=is_primary,
                        sort_order=i
                    )

            # تحديد ما إذا كان يجب الاستمرار في التحرير أم العودة إلى صفحة التفاصيل
            if 'save_and_continue' in form_data:
                return redirect('dashboard:dashboard_product_edit', product_id=str(product.id))
            else:
                return redirect('dashboard:dashboard_product_detail', product_id=str(product.id))

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ المنتج: {str(e)}')

            # في حالة حدوث استثناء، نعيد عرض النموذج مع البيانات المدخلة
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
                'product_attributes': product_attributes,
                'status_choices': Product.STATUS_CHOICES,
                'stock_status_choices': Product.STOCK_STATUS_CHOICES,
                'condition_choices': Product.CONDITION_CHOICES,

                # البيانات المدخلة سابقًا
                'form_data': form_data,
                'selected_category': category_id,
                'selected_brand': form_data.get('brand'),
                'selected_tags': request.POST.getlist('tags'),
                'specifications_json': specs_data,
                'features_json': features_data
            }

            return render(request, 'dashboard/products/product_form.html', context)


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


#======================
class ProductVariantFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث متغيرات المنتج"""

    def get(self, request, product_id, variant_id=None):
        """عرض نموذج إنشاء أو تحديث متغير المنتج"""
        product = get_object_or_404(Product, id=product_id)

        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
            form = ProductVariantForm(instance=variant, product=product)
            form_title = _('تعديل متغير المنتج')
        else:
            variant = None
            form = ProductVariantForm(product=product)
            form_title = _('إضافة متغير جديد للمنتج')

        context = {
            'form': form,
            'product': product,
            'variant': variant,
            'form_title': form_title,
        }

        return render(request, 'dashboard/products/product_variant_form.html', context)

    def post(self, request, product_id, variant_id=None):
        """معالجة نموذج إنشاء أو تحديث متغير المنتج"""
        product = get_object_or_404(Product, id=product_id)

        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
            form = ProductVariantForm(request.POST, instance=variant, product=product)
        else:
            variant = None
            form = ProductVariantForm(request.POST, product=product)

        if form.is_valid():
            try:
                variant = form.save(commit=False)
                variant.product = product

                # تحديث SKU إذا لم يتم توفيره
                if not variant.sku:
                    # توليد SKU للمتغير اعتمادًا على SKU المنتج الأساسي
                    base_sku = product.sku
                    variant_count = product.variants.count() + 1
                    variant.sku = f"{base_sku}-{variant_count}"

                variant.save()

                messages.success(request, _('تم حفظ متغير المنتج بنجاح'))
                return redirect('dashboard:dashboard_product_detail', product_id=product.id)

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حفظ متغير المنتج: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")

        context = {
            'form': form,
            'product': product,
            'variant': variant,
            'form_title': _('تعديل متغير المنتج') if variant_id else _('إضافة متغير جديد للمنتج'),
        }

        return render(request, 'dashboard/products/product_variant_form.html', context)


class ProductVariantDeleteView(DashboardAccessMixin, View):
    """حذف متغير المنتج"""

    def post(self, request, product_id, variant_id):
        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

        try:
            variant_name = variant.name
            variant.delete()
            messages.success(request, f'تم حذف متغير المنتج "{variant_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف متغير المنتج: {str(e)}')

        return redirect('dashboard:dashboard_product_detail', product_id=product.id)


class ProductVariantBulkActionsView(DashboardAccessMixin, View):
    """عمليات جماعية على متغيرات المنتج"""

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        action = request.POST.get('action')
        variant_ids = request.POST.getlist('selected_variants')

        if not variant_ids:
            messages.error(request, 'لم يتم تحديد أي متغيرات للمنتج')
            return redirect('dashboard:dashboard_product_detail', product_id=product.id)

        variants = ProductVariant.objects.filter(id__in=variant_ids, product=product)
        count = variants.count()

        if action == 'activate':
            variants.update(is_active=True)
            messages.success(request, f'تم تفعيل {count} متغير بنجاح')

        elif action == 'deactivate':
            variants.update(is_active=False)
            messages.success(request, f'تم إلغاء تفعيل {count} متغير بنجاح')

        elif action == 'delete':
            try:
                variants.delete()
                messages.success(request, f'تم حذف {count} متغير بنجاح')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حذف المتغيرات: {str(e)}')

        elif action == 'update_stock':
            # تحويل لصفحة تحديث المخزون للمتغيرات المحددة
            variant_ids_str = ','.join(variant_ids)
            return redirect(f'dashboard_update_variant_stock?variants={variant_ids_str}')

        return redirect('dashboard:dashboard_product_detail', product_id=product.id)