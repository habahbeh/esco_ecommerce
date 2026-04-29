import json
import logging

from django.db.models import Q
from django.views.generic import UpdateView, ListView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views import View

from core.models import SiteSettings, SEOKeyword
from dashboard.forms.seo import SEOSettingsForm, SEOKeywordForm
from dashboard.mixins import SuperuserRequiredMixin

logger = logging.getLogger(__name__)


class SEOSettingsView(SuperuserRequiredMixin, UpdateView):
    model = SiteSettings
    form_class = SEOSettingsForm
    template_name = 'dashboard/seo/seo_settings.html'
    success_url = reverse_lazy('dashboard:seo_settings')

    def get_object(self, queryset=None):
        return SiteSettings.get_settings()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('تم حفظ إعدادات SEO بنجاح'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('إعدادات SEO')
        context['keyword_count'] = SEOKeyword.objects.filter(is_active=True).count()
        context['site_keywords'] = SEOKeyword.objects.filter(level='site', is_active=True).count()
        context['competitor_keywords'] = SEOKeyword.objects.filter(is_competitor=True, is_active=True).count()
        return context


class SEOKeywordListView(SuperuserRequiredMixin, ListView):
    model = SEOKeyword
    template_name = 'dashboard/seo/keyword_list.html'
    context_object_name = 'keywords'
    paginate_by = 25

    def get_queryset(self):
        qs = SEOKeyword.objects.all().select_related('category', 'product')
        level = self.request.GET.get('level')
        if level:
            qs = qs.filter(level=level)
        competition = self.request.GET.get('competition')
        if competition:
            qs = qs.filter(competition=competition)
        is_competitor = self.request.GET.get('is_competitor')
        if is_competitor == '1':
            qs = qs.filter(is_competitor=True)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(keyword__icontains=q) | Q(keyword_en__icontains=q))
        return qs.order_by('-search_volume', 'keyword')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('إدارة الكلمات المفتاحية')
        context['total_keywords'] = SEOKeyword.objects.count()
        context['active_keywords'] = SEOKeyword.objects.filter(is_active=True).count()
        context['competitor_count'] = SEOKeyword.objects.filter(is_competitor=True).count()
        context['current_level'] = self.request.GET.get('level', '')
        context['current_competition'] = self.request.GET.get('competition', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class SEOKeywordCreateView(SuperuserRequiredMixin, CreateView):
    model = SEOKeyword
    form_class = SEOKeywordForm
    template_name = 'dashboard/seo/keyword_form.html'
    success_url = reverse_lazy('dashboard:seo_keywords')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('تم إضافة الكلمة المفتاحية بنجاح'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('إضافة كلمة مفتاحية')
        context['is_edit'] = False
        return context


class SEOKeywordEditView(SuperuserRequiredMixin, UpdateView):
    model = SEOKeyword
    form_class = SEOKeywordForm
    template_name = 'dashboard/seo/keyword_form.html'
    success_url = reverse_lazy('dashboard:seo_keywords')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('تم تحديث الكلمة المفتاحية بنجاح'))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('تعديل كلمة مفتاحية')
        context['is_edit'] = True
        return context


class SEOKeywordDeleteView(SuperuserRequiredMixin, DeleteView):
    model = SEOKeyword
    success_url = reverse_lazy('dashboard:seo_keywords')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('تم حذف الكلمة المفتاحية'))
        return super().delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


def _get_product_queryset(scope, filter_value):
    from products.models import Product
    qs = Product.objects.filter(is_active=True, status='published')
    if scope == 'category' and filter_value:
        qs = qs.filter(category_id=filter_value)
    elif scope == 'brand' and filter_value:
        qs = qs.filter(brand_id=filter_value)
    elif scope == 'untagged':
        qs = qs.filter(Q(meta_keywords='') | Q(meta_keywords__isnull=True))
    return qs


class AutoTagView(SuperuserRequiredMixin, View):
    template_name = 'dashboard/seo/auto_tag.html'

    def get(self, request, *args, **kwargs):
        from products.models import Product, Category, Brand
        from django.shortcuts import render

        total = Product.objects.filter(is_active=True, status='published').count()
        tagged = Product.objects.filter(
            is_active=True, status='published'
        ).exclude(meta_keywords='').exclude(meta_keywords__isnull=True).count()

        categories = list(
            Category.objects.filter(is_active=True)
            .order_by('name')
            .values_list('id', 'name')
        )
        brands = list(
            Brand.objects.filter(is_active=True)
            .order_by('name')
            .values_list('id', 'name')
        )

        return render(request, self.template_name, {
            'total_products': total,
            'tagged_products': tagged,
            'untagged_products': total - tagged,
            'page_title': _('التوسيم التلقائي'),
            'categories_json': json.dumps(
                [{'id': c[0], 'name': c[1]} for c in categories],
                ensure_ascii=False
            ),
            'brands_json': json.dumps(
                [{'id': b[0], 'name': b[1]} for b in brands],
                ensure_ascii=False
            ),
        })

    def post(self, request, *args, **kwargs):
        from products.models import Product
        from products.utils.auto_tagger import auto_tag_product

        product_id = request.POST.get('product_id')
        if product_id:
            try:
                product = Product.objects.get(pk=product_id)
                tags = auto_tag_product(product)
                return JsonResponse({'status': 'success', 'tags': tags})
            except Product.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': _('المنتج غير موجود')}, status=404)

        offset = int(request.POST.get('offset', 0))
        batch_size = int(request.POST.get('batch_size', 50))
        scope = request.POST.get('scope', 'all')
        filter_value = request.POST.get('filter_value', '')

        base_qs = _get_product_queryset(scope, filter_value)
        total = base_qs.count()

        products = list(
            base_qs.order_by('pk')
            .select_related('category', 'brand')[offset:offset + batch_size]
        )

        tagged_count = 0
        log_entries = []
        to_update = []

        for product in products:
            try:
                tags = auto_tag_product(product, save=False)
                if tags:
                    tagged_count += 1
                    to_update.append(product)
                    log_entries.append({
                        'id': product.pk,
                        'name': str(product.name)[:50],
                        'keywords': len(tags),
                        'sample': ', '.join(tags[:5]),
                    })
                else:
                    log_entries.append({
                        'id': product.pk,
                        'name': str(product.name)[:50],
                        'keywords': 0,
                        'sample': 'No keywords extracted',
                    })
            except Exception as e:
                logger.exception("Auto-tag failed for product %s", product.pk)
                log_entries.append({
                    'id': product.pk,
                    'name': str(product.name)[:50],
                    'keywords': 0,
                    'sample': f'Error: {str(e)[:40]}',
                })

        if to_update:
            Product.objects.bulk_update(to_update, ['meta_keywords', 'search_keywords', 'meta_title', 'meta_description'], batch_size=50)

        processed = offset + len(products)
        has_more = processed < total

        return JsonResponse({
            'status': 'success',
            'batch_tagged': tagged_count,
            'batch_processed': len(products),
            'total_processed': processed,
            'total': total,
            'has_more': has_more,
            'next_offset': processed,
            'percent': round(processed / total * 100) if total else 100,
            'log': log_entries,
        })
