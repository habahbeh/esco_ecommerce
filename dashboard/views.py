# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q, F, Avg
import csv, json
from datetime import datetime, timedelta

# تأكد من استيراد جميع النماذج المطلوبة - Import all required models
from products.models import Product, Category, ProductVariant, ProductImage, ProductDiscount

from orders.models import Order, OrderItem
from accounts.models import User
from .models import DashboardNotification, ProductReviewAssignment


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    مزيج للتحقق من أن المستخدم موظف - Mixin to check that the user is staff
    """
    def test_func(self):
        return self.request.user.is_staff

class DashboardView(StaffRequiredMixin, TemplateView):
    """
    عرض لوحة التحكم الرئيسية - يعرض نظرة عامة على المتجر والإحصائيات
    Dashboard view - displays store overview and statistics
    """
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الإحصائيات - Statistics
        context['total_products'] = Product.objects.count()
        context['active_products'] = Product.objects.filter(status='published', is_active=True).count()
        context['pending_products'] = Product.objects.filter(status='pending_review').count()
        context['total_orders'] = Order.objects.count()

        # إحصائيات المبيعات - Sales statistics
        today = timezone.now().date()
        start_of_month = today.replace(day=1)

        # طلبات اليوم - Today's orders
        context['today_orders'] = Order.objects.filter(created_at__date=today).count()
        context['today_sales'] = Order.objects.filter(created_at__date=today).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # طلبات الشهر - Month's orders
        context['month_orders'] = Order.objects.filter(created_at__date__gte=start_of_month).count()
        context['month_sales'] = Order.objects.filter(created_at__date__gte=start_of_month).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # أحدث الطلبات - Latest orders
        context['latest_orders'] = Order.objects.order_by('-created_at')[:5]

        # المنتجات التي تحتاج إلى مراجعة - Products needing review
        if hasattr(self.request.user, 'is_product_reviewer') and self.request.user.is_product_reviewer or self.request.user.is_superuser:
            context['pending_reviews'] = ProductReviewAssignment.objects.filter(
                reviewer=self.request.user,
                is_completed=False
            ).order_by('assigned_at')

        # الإشعارات - Notifications
        context['notifications'] = DashboardNotification.objects.filter(
            user=self.request.user,
            is_read=False
        ).order_by('-created_at')[:5]

        return context

# ===== إدارة المنتجات ===== #
# ===== Product Management ===== #

class ProductListView(StaffRequiredMixin, ListView):
    """
    عرض قائمة المنتجات - يعرض قائمة المنتجات في لوحة التحكم
    Product list view - displays a list of products in the dashboard
    """
    model = Product
    template_name = 'dashboard/products/list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-created_at')

        # فلترة حسب الحالة - Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # فلترة حسب الفئة - Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # فلترة حسب النشاط - Filter by activity
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            is_active = is_active == 'true'
            queryset = queryset.filter(is_active=is_active)

        # البحث - Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الفئات للفلترة - Categories for filtering
        context['categories'] = Category.objects.filter(level=0)  # Root categories

        # الفلاتر الحالية - Current filters
        context['current_status'] = self.request.GET.get('status', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_is_active'] = self.request.GET.get('is_active', '')
        context['current_search'] = self.request.GET.get('search', '')

        return context

class ProductDetailView(StaffRequiredMixin, DetailView):
    """
    عرض تفاصيل المنتج - يعرض تفاصيل منتج معين في لوحة التحكم
    Product detail view - displays details of a specific product in the dashboard
    """
    model = Product
    template_name = 'dashboard/products/detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # المتغيرات - Variants
        context['variants'] = self.object.variants.all()

        # الصور - Images
        context['images'] = self.object.images.all().order_by('sort_order')

        # تعيينات المراجعة - Review assignments
        context['review_assignments'] = self.object.review_assignments.all().select_related('reviewer')

        return context

class ProductCreateView(StaffRequiredMixin, CreateView):
    """
    عرض إنشاء منتج - يتيح للموظفين إنشاء منتج جديد
    Product create view - allows staff to create a new product
    """
    model = Product
    template_name = 'dashboard/products/form.html'
    fields = [
        'name', 'sku', 'description', 'short_description', 'category',
        'brand', 'base_price', 'stock_quantity', 'stock_status', 'status',
        'is_featured', 'is_active', 'meta_title', 'meta_description', 'meta_keywords'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة منتج جديد')
        context['categories'] = Category.objects.all()
        return context

    def form_valid(self, form):
        # تعيين معلومات المستخدم - Set user information
        form.instance.created_by = self.request.user

        # حفظ المنتج - Save the product
        response = super().form_valid(form)

        # إذا كانت الحالة "قيد المراجعة"، قم بتعيين مراجع - If status is "pending", assign a reviewer
        if form.instance.status == 'pending_review':
            # البحث عن مراجعين متاحين - Find available reviewers
            reviewers = User.objects.filter(is_staff=True, is_active=True)

            if reviewers.exists():
                # اختيار المراجع الذي لديه أقل عدد من المهام النشطة
                # Choose the reviewer with the least active assignments
                reviewer = reviewers.annotate(
                    active_assignments=Count(
                        'product_review_assignments',
                        filter=Q(product_review_assignments__is_completed=False)
                    )
                ).order_by('active_assignments').first()

                # إنشاء تعيين المراجعة - Create review assignment
                ProductReviewAssignment.objects.create(
                    product=form.instance,
                    reviewer=reviewer,
                    assigned_by=self.request.user
                )

                # إنشاء إشعار للمراجع - Create notification for reviewer
                DashboardNotification.objects.create(
                    user=reviewer,
                    title=_('تعيين مراجعة منتج جديد'),
                    message=_('تم تعيينك لمراجعة منتج جديد: {}').format(form.instance.name),
                    notification_type='info',
                    related_object_type='product',
                    related_object_id=str(form.instance.id)
                )

        # إنشاء رسالة نجاح - Create success message
        messages.success(self.request, _('تم إنشاء المنتج بنجاح.'))

        return response

    def get_success_url(self):
        return reverse_lazy('dashboard:product_detail', kwargs={'pk': self.object.id})

class ProductUpdateView(StaffRequiredMixin, UpdateView):
    """
    عرض تحديث المنتج - يتيح للموظفين تحديث منتج موجود
    Product update view - allows staff to update an existing product
    """
    model = Product
    template_name = 'dashboard/products/form.html'
    fields = [
        'name', 'sku', 'description', 'short_description', 'category',
        'brand', 'base_price', 'stock_quantity', 'stock_status', 'status',
        'is_featured', 'is_active', 'meta_title', 'meta_description', 'meta_keywords'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تحديث المنتج')
        context['categories'] = Category.objects.all()
        context['is_update'] = True
        return context

    def form_valid(self, form):
        # حفظ المنتج - Save the product
        response = super().form_valid(form)

        # إنشاء رسالة نجاح - Create success message
        messages.success(self.request, _('تم تحديث المنتج بنجاح.'))

        return response

    def get_success_url(self):
        return reverse_lazy('dashboard:product_detail', kwargs={'pk': self.object.id})

class ProductDeleteView(StaffRequiredMixin, DeleteView):
    """
    عرض حذف المنتج - يتيح للموظفين حذف منتج
    Product delete view - allows staff to delete a product
    """
    model = Product
    template_name = 'dashboard/products/delete.html'
    context_object_name = 'product'
    success_url = reverse_lazy('dashboard:product_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف المنتج بنجاح.'))
        return super().delete(request, *args, **kwargs)

class ProductReviewView(StaffRequiredMixin, UpdateView):
    """
    عرض مراجعة المنتج - يتيح للمراجعين مراجعة منتج والموافقة عليه أو رفضه
    Product review view - allows reviewers to review a product and approve or reject it
    """
    model = Product
    template_name = 'dashboard/products/review.html'
    fields = ['status']

    def get_queryset(self):
        # فقط المنتجات المعينة للمراجع - Only products assigned to the reviewer
        if self.request.user.is_superuser:
            return Product.objects.all()
        else:
            return Product.objects.filter(
                review_assignments__reviewer=self.request.user,
                review_assignments__is_completed=False
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('مراجعة المنتج')

        # الحصول على تعيين المراجعة - Get review assignment
        try:
            context['assignment'] = ProductReviewAssignment.objects.get(
                product=self.object,
                reviewer=self.request.user,
                is_completed=False
            )
        except ProductReviewAssignment.DoesNotExist:
            context['assignment'] = None

        return context

    def form_valid(self, form):
        # إذا كانت الحالة "منشور"، قم بتعيين معلومات الموافقة
        # If status is "published", set approval information
        if form.instance.status == 'published':
            form.instance.published_at = timezone.now()

        # حفظ المنتج - Save the product
        response = super().form_valid(form)

        # تحديث تعيين المراجعة - Update review assignment
        try:
            assignment = ProductReviewAssignment.objects.get(
                product=self.object,
                reviewer=self.request.user,
                is_completed=False
            )

            assignment.mark_as_completed(
                notes=self.request.POST.get('review_notes', '')
            )

            # إنشاء إشعار لمنشئ المنتج - Create notification for product creator
            if self.object.created_by:
                status_text = _('تمت الموافقة على') if self.object.status == 'published' else _('تم رفض')

                DashboardNotification.objects.create(
                    user=self.object.created_by,
                    title=_('تحديث حالة المنتج'),
                    message=_('{}المنتج "{}" بواسطة {}').format(
                        status_text, self.object.name, self.request.user.get_full_name() or self.request.user.username
                    ),
                    notification_type='success' if self.object.status == 'published' else 'warning',
                    related_object_type='product',
                    related_object_id=str(self.object.id)
                )
        except ProductReviewAssignment.DoesNotExist:
            pass

        # إنشاء رسالة نجاح - Create success message
        messages.success(self.request, _('تمت مراجعة المنتج بنجاح.'))

        return response

    def get_success_url(self):
        return reverse_lazy('dashboard:product_detail', kwargs={'pk': self.object.id})

class ProductVariantCreateView(StaffRequiredMixin, CreateView):
    """
    عرض إنشاء متغير المنتج - يتيح للموظفين إضافة متغير جديد للمنتج
    Product variant create view - allows staff to add a new variant to a product
    """
    model = ProductVariant
    template_name = 'dashboard/products/variant_form.html'
    fields = ['name', 'sku', 'base_price', 'stock_quantity', 'is_active']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة متغير جديد')
        context['product'] = get_object_or_404(Product, pk=self.kwargs['product_id'])
        return context

    def form_valid(self, form):
        # تعيين المنتج - Set the product
        form.instance.product = get_object_or_404(Product, pk=self.kwargs['product_id'])

        # حفظ المتغير - Save the variant
        response = super().form_valid(form)

        # إنشاء رسالة نجاح - Create success message
        messages.success(self.request, _('تم إضافة متغير المنتج بنجاح.'))

        return response

    def get_success_url(self):
        return reverse_lazy('dashboard:product_detail', kwargs={'pk': self.kwargs['product_id']})

class ProductVariantUpdateView(StaffRequiredMixin, UpdateView):
    """
    عرض تحديث متغير المنتج - يتيح للموظفين تحديث متغير منتج موجود
    Product variant update view - allows staff to update an existing product variant
    """
    model = ProductVariant
    template_name = 'dashboard/products/variant_form.html'
    fields = ['name', 'sku', 'base_price', 'stock_quantity', 'is_active']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تحديث متغير المنتج')
        context['product'] = self.object.product
        context['is_update'] = True
        return context

    def form_valid(self, form):
        # حفظ المتغير - Save the variant
        response = super().form_valid(form)

        # إنشاء رسالة نجاح - Create success message
        messages.success(self.request, _('تم تحديث متغير المنتج بنجاح.'))

        return response

    def get_success_url(self):
        return reverse_lazy('dashboard:product_detail', kwargs={'pk': self.object.product.id})

class ProductVariantDeleteView(StaffRequiredMixin, DeleteView):
    """
    عرض حذف متغير المنتج - يتيح للموظفين حذف متغير منتج
    Product variant delete view - allows staff to delete a product variant
    """
    model = ProductVariant
    template_name = 'dashboard/products/variant_delete.html'
    context_object_name = 'variant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        return context

    def delete(self, request, *args, **kwargs):
        product_id = self.get_object().product.id
        messages.success(request, _('تم حذف متغير المنتج بنجاح.'))
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('dashboard:product_detail', kwargs={'pk': self.object.product.id})

class ProductImageUploadView(StaffRequiredMixin, CreateView):
    """
    عرض رفع صورة المنتج - يتيح للموظفين رفع صور للمنتج
    Product image upload view - allows staff to upload images for a product
    """
    model = ProductImage
    template_name = 'dashboard/products/image_form.html'
    fields = ['image', 'alt_text', 'is_primary', 'variant', 'sort_order']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('رفع صورة جديدة')
        context['product'] = get_object_or_404(Product, pk=self.kwargs['product_id'])
        context['variants'] = context['product'].variants.all()
        return context

    def form_valid(self, form):
        # تعيين المنتج - Set the product
        form.instance.product = get_object_or_404(Product, pk=self.kwargs['product_id'])

        # حفظ الصورة - Save the image
        response = super().form_valid(form)

        # إنشاء رسالة نجاح - Create success message
        messages.success(self.request, _('تم رفع صورة المنتج بنجاح.'))

        return response

    def get_success_url(self):
        return reverse_lazy('dashboard:product_detail', kwargs={'pk': self.kwargs['product_id']})

class ProductImageDeleteView(StaffRequiredMixin, DeleteView):
    """
    عرض حذف صورة المنتج - يتيح للموظفين حذف صورة منتج
    Product image delete view - allows staff to delete a product image
    """
    model = ProductImage
    template_name = 'dashboard/products/image_delete.html'
    context_object_name = 'image'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        return context

    def delete(self, request, *args, **kwargs):
        product_id = self.get_object().product.id
        messages.success(request, _('تم حذف صورة المنتج بنجاح.'))
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('dashboard:product_detail', kwargs={'pk': self.object.product.id})

# ===== إدارة الفئات ===== #
# ===== Category Management ===== #

class CategoryListView(StaffRequiredMixin, ListView):
    """
    عرض قائمة الفئات - يعرض قائمة الفئات في لوحة التحكم
    Category list view - displays a list of categories in the dashboard
    """
    model = Category
    template_name = 'dashboard/categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(level=0).order_by('name')  # Root categories only

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عدد المنتجات في كل فئة - Number of products in each category
        categories = context['categories']
        for category in categories:
            category.product_count = Product.objects.filter(category=category).count()
            category.subcategories_count = Category.objects.filter(parent=category).count()

        return context

class CategoryDetailView(StaffRequiredMixin, DetailView):
    """
    عرض تفاصيل الفئة - يعرض تفاصيل فئة معينة في لوحة التحكم
    Category detail view - displays details of a specific category in the dashboard
    """
    model = Category
    template_name = 'dashboard/categories/detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الفئات الفرعية - Subcategories
        context['subcategories'] = Category.objects.filter(parent=self.object).order_by('name')

        # المنتجات في هذه الفئة - Products in this category
        context['products'] = Product.objects.filter(category=self.object).order_by('-created_at')[:10]

        # عدد المنتجات - Product count
        context['product_count'] = Product.objects.filter(category=self.object).count()

        return context

class CategoryCreateView(StaffRequiredMixin, CreateView):
    """
    عرض إنشاء فئة - يتيح للموظفين إنشاء فئة جديدة
    Category create view - allows staff to create a new category
    """
    model = Category
    template_name = 'dashboard/categories/form.html'
    fields = ['name', 'description', 'image', 'is_active', 'parent']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة فئة جديدة')

        # الفئات الرئيسية للاختيار كأب - Main categories to choose as parent
        parent_id = self.request.GET.get('parent')
        if parent_id:
            context['parent_category'] = get_object_or_404(Category, id=parent_id)

        # جميع الفئات المحتملة - All potential categories
        context['all_categories'] = Category.objects.all()

        return context

    def form_valid(self, form):
        # تعيين معلومات المستخدم - Set user information
        form.instance.created_by = self.request.user

        # تعيين الأب من المعلمات إذا لم يتم تحديده في النموذج
        # Set parent from parameters if not specified in the form
        parent_id = self.request.GET.get('parent')
        if parent_id and not form.instance.parent:
            form.instance.parent = get_object_or_404(Category, id=parent_id)

        # حفظ الفئة - Save the category
        response = super().form_valid(form)

        # إنشاء رسالة نجاح - Create success message
        messages.success(self.request, _('تم إنشاء الفئة بنجاح.'))

        return response

    def get_success_url(self):
        if self.object.parent:
            return reverse_lazy('dashboard:category_detail', kwargs={'pk': self.object.parent.id})
        return reverse_lazy('dashboard:category_list')

class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    """
    عرض تحديث الفئة - يتيح للموظفين تحديث فئة موجودة
    Category update view - allows staff to update an existing category
    """
    model = Category
    template_name = 'dashboard/categories/form.html'
    fields = ['name', 'description', 'image', 'is_active', 'parent']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تحديث الفئة')
        context['is_update'] = True

        # جميع الفئات المحتملة (باستثناء هذه الفئة وفئاتها الفرعية)
        # All potential categories (excluding this category and its subcategories)
        exclude_ids = [self.object.id]
        subcategories = Category.objects.filter(parent=self.object)
        for subcategory in subcategories:
            exclude_ids.append(subcategory.id)

        context['all_categories'] = Category.objects.exclude(id__in=exclude_ids)

        return context

    def form_valid(self, form):
        # حفظ الفئة - Save the category
        response = super().form_valid(form)

        # إنشاء رسالة نجاح - Create success message
        messages.success(self.request, _('تم تحديث الفئة بنجاح.'))

        return response

    def get_success_url(self):
        if self.object.parent:
            return reverse_lazy('dashboard:category_detail', kwargs={'pk': self.object.parent.id})
        return reverse_lazy('dashboard:category_list')

class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    """
    عرض حذف الفئة - يتيح للموظفين حذف فئة
    Category delete view - allows staff to delete a category
    """
    model = Category
    template_name = 'dashboard/categories/delete.html'
    context_object_name = 'category'
    success_url = reverse_lazy('dashboard:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # التحقق من وجود منتجات في هذه الفئة - Check if there are products in this category
        context['has_products'] = Product.objects.filter(category=self.object).exists()

        # التحقق من وجود فئات فرعية - Check if there are subcategories
        context['has_subcategories'] = Category.objects.filter(parent=self.object).exists()

        return context

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        parent_id = category.parent.id if category.parent else None

        # التحقق من عدم وجود منتجات أو فئات فرعية
        # Check there are no products or subcategories
        if Product.objects.filter(category=category).exists():
            messages.error(request, _('لا يمكن حذف الفئة لأنها تحتوي على منتجات.'))
            return redirect('dashboard:category_detail', pk=category.id)

        if Category.objects.filter(parent=category).exists():
            messages.error(request, _('لا يمكن حذف الفئة لأنها تحتوي على فئات فرعية.'))
            return redirect('dashboard:category_detail', pk=category.id)

        messages.success(request, _('تم حذف الفئة بنجاح.'))

        # الحذف - Delete
        response = super().delete(request, *args, **kwargs)

        # إعادة التوجيه إلى الفئة الأب إذا كانت موجودة
        # Redirect to parent category if it exists
        if parent_id:
            return redirect('dashboard:category_detail', pk=parent_id)

        return response

# ===== إدارة الخصومات ===== #
# ===== Discount Management ===== #

class DiscountListView(StaffRequiredMixin, ListView):
    """
    عرض قائمة الخصومات - يعرض قائمة الخصومات في لوحة التحكم
    Discount list view - displays a list of discounts in the dashboard
    """
    model = ProductDiscount
    template_name = 'dashboard/discounts/list.html'
    context_object_name = 'discounts'
    paginate_by = 20

    def get_queryset(self):
        queryset = ProductDiscount.objects.select_related('category', 'created_by').prefetch_related('products').order_by('-start_date')

        # فلترة حسب النشاط - Filter by activity
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            is_active = is_active == 'true'
            queryset = queryset.filter(is_active=is_active)

        # فلترة حسب الفئة - Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # فلترة حسب نوع الخصم - Filter by discount type
        discount_type = self.request.GET.get('discount_type')
        if discount_type:
            queryset = queryset.filter(discount_type=discount_type)

        # البحث - Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(code__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الفئات للفلترة - Categories for filtering
        context['categories'] = Category.objects.all()

        # أنواع الخصم للفلترة - Discount types for filtering
        context['discount_types'] = ProductDiscount.DISCOUNT_TYPE_CHOICES

        # الفلاتر الحالية - Current filters
        context['current_is_active'] = self.request.GET.get('is_active', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_discount_type'] = self.request.GET.get('discount_type', '')
        context['current_search'] = self.request.GET.get('search', '')

        return context

class DiscountCreateView(StaffRequiredMixin, CreateView):
    """
    إنشاء خصم جديد
    Create new discount
    """
    model = ProductDiscount
    template_name = 'dashboard/discounts/create.html'
    fields = [
        'name', 'description', 'code', 'discount_type', 'value', 'max_discount_amount',
        'application_type', 'category', 'products', 'start_date', 'end_date',
        'min_purchase_amount', 'min_quantity', 'max_uses', 'max_uses_per_user',
        'buy_quantity', 'get_quantity', 'get_discount_percentage',
        'is_active', 'is_stackable', 'requires_coupon_code', 'priority'
    ]
    success_url = reverse_lazy('dashboard:discount_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('تم إنشاء الخصم بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['products'] = Product.objects.filter(is_active=True, status='published')
        return context

class DiscountUpdateView(StaffRequiredMixin, UpdateView):
    """
    تحديث خصم موجود
    Update existing discount
    """
    model = ProductDiscount
    template_name = 'dashboard/discounts/update.html'
    fields = [
        'name', 'description', 'code', 'discount_type', 'value', 'max_discount_amount',
        'application_type', 'category', 'products', 'start_date', 'end_date',
        'min_purchase_amount', 'min_quantity', 'max_uses', 'max_uses_per_user',
        'buy_quantity', 'get_quantity', 'get_discount_percentage',
        'is_active', 'is_stackable', 'requires_coupon_code', 'priority'
    ]
    success_url = reverse_lazy('dashboard:discount_list')

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث الخصم بنجاح'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['products'] = Product.objects.filter(is_active=True, status='published')
        return context

class DiscountDeleteView(StaffRequiredMixin, DeleteView):
    """
    حذف خصم
    Delete discount
    """
    model = ProductDiscount
    template_name = 'dashboard/discounts/delete.html'
    success_url = reverse_lazy('dashboard:discount_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف الخصم بنجاح'))
        return super().delete(request, *args, **kwargs)

# ===== إدارة الطلبات ===== #
# ===== Order Management ===== #

class OrderListView(StaffRequiredMixin, ListView):
    """
    عرض قائمة الطلبات - يعرض قائمة الطلبات في لوحة التحكم
    Order list view - displays a list of orders in the dashboard
    """
    model = Order
    template_name = 'dashboard/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = Order.objects.all().order_by('-created_at')

        # فلترة حسب الحالة - Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # البحث - Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # خيارات الفلترة - Filter options
        context['status_choices'] = Order.STATUS_CHOICES if hasattr(Order, 'STATUS_CHOICES') else []

        # الفلاتر الحالية - Current filters
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')

        return context

class OrderDetailView(StaffRequiredMixin, DetailView):
    """
    عرض تفاصيل الطلب - يعرض تفاصيل طلب معين في لوحة التحكم
    Order detail view - displays details of a specific order in the dashboard
    """
    model = Order
    template_name = 'dashboard/orders/detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عناصر الطلب - Order items
        context['order_items'] = self.object.items.all()

        # خيارات تحديث الحالة - Status update options
        context['status_choices'] = Order.STATUS_CHOICES if hasattr(Order, 'STATUS_CHOICES') else []

        return context

class OrderUpdateStatusView(StaffRequiredMixin, View):
    """
    عرض تحديث حالة الطلب - يتيح للموظفين تحديث حالة الطلب
    Order update status view - allows staff to update order status
    """
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        # تحديث حالة الطلب - Update order status
        status = request.POST.get('status')
        if status:
            order.status = status
            order.save()

        # إنشاء رسالة نجاح - Create success message
        messages.success(request, _('تم تحديث حالة الطلب بنجاح.'))

        return redirect('dashboard:order_detail', pk=pk)

# ===== التصدير والاستيراد ===== #
# ===== Export and Import ===== #

class ExportProductsView(StaffRequiredMixin, View):
    """
    عرض تصدير المنتجات - يتيح للموظفين تصدير المنتجات إلى ملف CSV
    Export products view - allows staff to export products to a CSV file
    """
    def get(self, request):
        # إنشاء استجابة CSV - Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'

        # إنشاء كاتب CSV - Create CSV writer
        writer = csv.writer(response)

        # كتابة رأس الملف - Write header
        writer.writerow([
            'ID', 'SKU', 'Name', 'Description', 'Short Description',
            'Category', 'Base Price', 'Stock Quantity', 'Stock Status',
            'Status', 'Is Featured', 'Is Active', 'Created At'
        ])

        # كتابة بيانات المنتجات - Write product data
        products = Product.objects.all().select_related('category')
        for product in products:
            writer.writerow([
                str(product.id), product.sku, product.name,
                product.description, product.short_description,
                product.category.name if product.category else '',
                product.base_price, product.stock_quantity, product.stock_status,
                product.status, product.is_featured, product.is_active, product.created_at
            ])

        return response

class ImportProductsView(StaffRequiredMixin, TemplateView):
    """
    عرض استيراد المنتجات - يتيح للموظفين استيراد المنتجات من ملف CSV
    Import products view - allows staff to import products from a CSV file
    """
    template_name = 'dashboard/products/import.html'

    def post(self, request):
        # الحصول على الملف المرفوع - Get uploaded file
        csv_file = request.FILES.get('csv_file')

        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, _('يرجى تحميل ملف CSV صالح.'))
            return self.get(request)

        # قراءة ملف CSV - Read CSV file
        try:
            # قراءة ملف CSV - Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.reader(decoded_file.splitlines(), delimiter=',')

            # تخطي الصف الأول (الرأس) - Skip first row (header)
            header = next(csv_data)

            # استيراد المنتجات - Import products
            products_created = 0
            products_updated = 0
            errors = 0

            for row in csv_data:
                try:
                    # الحصول على القيم من الصف - Get values from row
                    sku = row[1]
                    name = row[2]
                    description = row[3]
                    short_description = row[4]
                    category_name = row[5]
                    base_price = float(row[6]) if row[6] else 0
                    stock_quantity = int(row[7]) if row[7] else 0
                    stock_status = row[8] if row[8] else 'in_stock'
                    status = row[9] if row[9] else 'draft'
                    is_featured = row[10].lower() in ('true', 'yes', '1') if row[10] else False
                    is_active = row[11].lower() in ('true', 'yes', '1') if row[11] else True

                    # البحث عن الفئة أو إنشاؤها - Find or create category
                    category = None
                    if category_name:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={
                                'created_by': request.user
                            }
                        )

                    # البحث عن المنتج بناءً على SKU - Find product based on SKU
                    product, created = Product.objects.get_or_create(
                        sku=sku,
                        defaults={
                            'name': name,
                            'description': description,
                            'short_description': short_description,
                            'category': category,
                            'base_price': base_price,
                            'stock_quantity': stock_quantity,
                            'stock_status': stock_status,
                            'status': status,
                            'is_featured': is_featured,
                            'is_active': is_active,
                            'created_by': request.user
                        }
                    )

                    if created:
                        products_created += 1
                    else:
                        # تحديث المنتج الموجود - Update existing product
                        product.name = name
                        product.description = description
                        product.short_description = short_description
                        product.category = category
                        product.base_price = base_price
                        product.stock_quantity = stock_quantity
                        product.stock_status = stock_status
                        product.status = status
                        product.is_featured = is_featured
                        product.is_active = is_active
                        product.save()
                        products_updated += 1

                except Exception as e:
                    errors += 1
                    continue

            # إنشاء رسالة نجاح - Create success message
            if errors > 0:
                messages.warning(
                    request,
                    _('تم استيراد المنتجات بنجاح: {} منتج جديد، {} منتج تم تحديثه، {} خطأ.').format(
                        products_created, products_updated, errors
                    )
                )
            else:
                messages.success(
                    request,
                    _('تم استيراد المنتجات بنجاح: {} منتج جديد، {} منتج تم تحديثه.').format(
                        products_created, products_updated
                    )
                )

        except Exception as e:
            messages.error(request, _('حدث خطأ أثناء استيراد المنتجات: {}').format(str(e)))

        return redirect('dashboard:product_list')