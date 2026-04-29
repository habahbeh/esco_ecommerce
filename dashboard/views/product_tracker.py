from urllib.parse import quote

from django.views.generic import ListView, View
from django.http import JsonResponse
from django.db.models import Q, F, Count, Case, When, Value, IntegerField
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from products.models import Product
from dashboard.models import ProductNote, ProductActivityLog
from dashboard.mixins import DashboardAccessMixin


class ProductTrackerView(DashboardAccessMixin, ListView):
    template_name = 'dashboard/products/product_tracker.html'
    context_object_name = 'products'
    paginate_by = 25

    VALID_SORTS = {
        '-updated_at', 'updated_at',
        'name', '-name',
        'base_price', '-base_price',
        'stock_quantity', '-stock_quantity',
    }

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True)

        product_status = self.request.GET.get('product_status')
        if product_status == 'published':
            qs = qs.filter(status='published')
        elif product_status == 'draft':
            qs = qs.filter(status='draft')
        elif product_status == 'out_of_stock':
            qs = qs.filter(stock_status='out_of_stock')
        elif product_status == 'low_stock':
            qs = qs.filter(
                stock_quantity__gt=0,
                stock_quantity__lte=F('min_stock_level')
            )

        search = self.request.GET.get('q', '').strip()
        if len(search) >= 2:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(name_en__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search)
            )

        sort = self.request.GET.get('sort', '-updated_at')
        if sort not in self.VALID_SORTS:
            sort = '-updated_at'

        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('متتبع المنتجات')

        agg = Product.objects.filter(is_active=True).aggregate(
            total=Count('id'),
            published=Count(Case(When(status='published', then=1))),
            draft=Count(Case(When(status='draft', then=1))),
            out_of_stock=Count(Case(When(stock_status='out_of_stock', then=1))),
            low_stock=Count(Case(When(
                stock_quantity__gt=0,
                stock_quantity__lte=F('min_stock_level'),
                then=1,
            ))),
        )
        context['stats'] = agg

        context['recent_changes'] = (
            ProductActivityLog.objects.select_related('product', 'user')
            .order_by('-timestamp')[:10]
        )

        context['recent_notes'] = (
            ProductNote.objects.select_related('product', 'user')
            .filter(is_resolved=False)
            .order_by('-created_at')[:10]
        )

        today = timezone.now().date()
        today_agg = ProductActivityLog.objects.filter(
            action__in=('price_changed', 'stock_changed'),
            timestamp__date=today,
        ).aggregate(
            price=Count(Case(When(action='price_changed', then=1))),
            stock=Count(Case(When(action='stock_changed', then=1))),
        )
        context['price_changes_today'] = today_agg['price']
        context['stock_changes_today'] = today_agg['stock']

        context['current_product_status'] = self.request.GET.get('product_status', '')
        context['current_search'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '-updated_at')

        search_encoded = quote(context['current_search'], safe='')

        filter_parts = []
        if context['current_product_status']:
            filter_parts.append(f"product_status={context['current_product_status']}")
        if context['current_search']:
            filter_parts.append(f"q={search_encoded}")
        if context['current_sort'] != '-updated_at':
            filter_parts.append(f"sort={context['current_sort']}")
        context['filter_params'] = '&'.join(filter_parts)

        card_parts = []
        if context['current_search']:
            card_parts.append(f"q={search_encoded}")
        if context['current_sort'] != '-updated_at':
            card_parts.append(f"sort={context['current_sort']}")
        card_qs = '&'.join(card_parts)
        context['card_filter_base'] = ('&' + card_qs) if card_qs else ''
        context['card_filter_only'] = card_qs

        return context


class ProductSearchAPIView(DashboardAccessMixin, View):
    raise_exception = True

    def handle_no_permission(self):
        return JsonResponse({'results': [], 'error': 'unauthorized'}, status=403)

    def get(self, request):
        q = request.GET.get('q', '').strip()
        if len(q) < 2:
            return JsonResponse({'results': []})

        products = Product.objects.filter(
            Q(name__icontains=q) |
            Q(name_en__icontains=q) |
            Q(sku__icontains=q) |
            Q(barcode__icontains=q)
        ).values('id', 'name', 'sku')[:10]

        return JsonResponse({
            'results': [
                {'id': str(p['id']), 'name': p['name'], 'sku': p['sku'] or ''}
                for p in products
            ]
        })


class ProductNoteCreateView(DashboardAccessMixin, View):
    VALID_NOTE_TYPES = {'general', 'price', 'stock', 'quality', 'supplier', 'todo'}

    def post(self, request):
        product_id = request.POST.get('product_id')
        content = request.POST.get('content', '').strip()
        note_type = request.POST.get('note_type', 'general')
        if note_type not in self.VALID_NOTE_TYPES:
            note_type = 'general'

        if not product_id or not content:
            return JsonResponse({'status': 'error', 'message': str(_('بيانات ناقصة'))}, status=400)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': str(_('المنتج غير موجود'))}, status=404)

        note = ProductNote.objects.create(
            product=product,
            user=request.user,
            content=content,
            note_type=note_type,
        )

        return JsonResponse({
            'status': 'success',
            'note': {
                'id': note.id,
                'content': note.content,
                'note_type': note.get_note_type_display(),
                'user': request.user.get_full_name() or request.user.username,
                'created_at': note.created_at.strftime('%Y/%m/%d %H:%M'),
            }
        })


class ProductNoteResolveView(DashboardAccessMixin, View):
    def post(self, request, pk):
        try:
            note = ProductNote.objects.get(pk=pk)
            note.is_resolved = True
            note.save(update_fields=['is_resolved'])
            return JsonResponse({'status': 'success'})
        except ProductNote.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)


class ProductNoteDeleteView(DashboardAccessMixin, View):
    def post(self, request, pk):
        try:
            note = ProductNote.objects.get(pk=pk)
            note.delete()
            return JsonResponse({'status': 'success'})
        except ProductNote.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)


class ProductNotesListView(DashboardAccessMixin, View):
    def get(self, request, product_id):
        notes = ProductNote.objects.filter(
            product_id=product_id
        ).select_related('user').order_by('-created_at')

        data = [{
            'id': n.id,
            'content': n.content,
            'note_type': n.get_note_type_display(),
            'note_type_key': n.note_type,
            'user': n.user.get_full_name() or n.user.username if n.user else '',
            'created_at': n.created_at.strftime('%Y/%m/%d %H:%M'),
            'is_resolved': n.is_resolved,
        } for n in notes]

        return JsonResponse({'notes': data})
