import json
import logging
from collections import Counter
from datetime import timedelta
from functools import reduce
from operator import or_
from urllib.parse import urlparse

from django.db import models
from django.db.models import Q, Count, Max, Min, Sum, F
from django.db.models.functions import TruncDate, TruncHour
from django.views.generic import UpdateView, ListView, CreateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse
from django.views import View

from core.models import SiteSettings, SEOKeyword, PageView
from dashboard.forms.seo import SEOSettingsForm, SEOKeywordForm
from dashboard.mixins import SuperuserRequiredMixin
from accounts.models import UserActivity

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
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='seo_keyword_create',
            description=f'Created SEO keyword: {self.object.keyword}',
            object_id=str(self.object.pk),
            content_type='core.seokeyword',
            ip_address=self.request.META.get('REMOTE_ADDR'),
        )
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
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='seo_keyword_update',
            description=f'Updated SEO keyword: {self.object.keyword}',
            object_id=str(self.object.pk),
            content_type='core.seokeyword',
            ip_address=self.request.META.get('REMOTE_ADDR'),
        )
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


class SiteAnalyticsView(SuperuserRequiredMixin, TemplateView):
    template_name = 'dashboard/seo/analytics.html'

    def _calc_change(self, current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round((current - previous) / previous * 100, 1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('تحليلات الموقع')

        now = timezone.now()
        period = self.request.GET.get('period', '30')
        try:
            days = int(period)
        except (ValueError, TypeError):
            days = 30
        days = max(1, min(days, 365))
        start_date = now - timedelta(days=days)

        human_qs = PageView.objects.filter(is_bot=False, timestamp__gte=start_date).order_by()
        all_qs = PageView.objects.filter(timestamp__gte=start_date).order_by()

        # ── 1. Core KPIs ──
        total_views = human_qs.count()
        unique_visitors = human_qs.values('ip_address').distinct().count()
        bot_hits = all_qs.filter(is_bot=True).count()

        session_qs = human_qs.exclude(session_key='')
        unique_sessions = session_qs.values('session_key').distinct().count()
        session_views = session_qs.count()
        avg_pages = round(session_views / unique_sessions, 1) if unique_sessions else 0

        # Bounce rate: count sessions with exactly 1 page view in DB
        if unique_sessions > 0:
            bounced = (
                session_qs.values('session_key')
                .annotate(pages=Count('id'))
                .filter(pages=1)
                .count()
            )
            bounce_rate = round(bounced / unique_sessions * 100, 1)
        else:
            bounce_rate = 0

        # Previous period comparison
        prev_start = start_date - timedelta(days=days)
        prev_qs = PageView.objects.filter(is_bot=False, timestamp__gte=prev_start, timestamp__lt=start_date).order_by()
        prev_views = prev_qs.count()
        prev_unique = prev_qs.values('ip_address').distinct().count()
        views_change = self._calc_change(total_views, prev_views)
        visitors_change = self._calc_change(unique_visitors, prev_unique)

        # Today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_views = human_qs.filter(timestamp__gte=today_start).count()
        today_unique = human_qs.filter(timestamp__gte=today_start).values('ip_address').distinct().count()

        # Live — active visitors in the last 15 minutes (by IP)
        live_window = now - timedelta(minutes=15)
        live_visitors = (
            PageView.objects.filter(is_bot=False, timestamp__gte=live_window)
            .exclude(ip_address__isnull=True)
            .values('ip_address').distinct().count()
        )

        # Week / Month (always absolute, not period-dependent)
        weekly_views = PageView.objects.filter(is_bot=False, timestamp__gte=now - timedelta(days=7)).count()
        monthly_views = PageView.objects.filter(is_bot=False, timestamp__gte=now - timedelta(days=30)).count()

        # ── 2. Traffic chart ──
        if days <= 2:
            chart_data = list(
                human_qs.annotate(date=TruncHour('timestamp'))
                .values('date').annotate(views=Count('id'), visitors=Count('ip_address', distinct=True))
                .order_by('date')
            )
        else:
            chart_data = list(
                human_qs.annotate(date=TruncDate('timestamp'))
                .values('date').annotate(views=Count('id'), visitors=Count('ip_address', distinct=True))
                .order_by('date')
            )

        chart_labels, chart_views_data, chart_visitors_data = [], [], []
        for entry in chart_data:
            d = entry['date']
            chart_labels.append(d.strftime('%H:%M') if days <= 2 else d.strftime('%m/%d'))
            chart_views_data.append(entry['views'])
            chart_visitors_data.append(entry['visitors'])

        # ── 3. Top pages ──
        top_pages = list(
            human_qs.values('path')
            .annotate(views=Count('id'), visitors=Count('ip_address', distinct=True))
            .order_by('-views')[:10]
        )

        # ── 4. Exit pages — two-step: max timestamp per session, then lookup ──
        last_per_session = list(
            session_qs.values('session_key')
            .annotate(last_ts=Max('timestamp'))
            .values_list('session_key', 'last_ts')
        )
        if last_per_session:
            exit_filter = reduce(or_, [Q(session_key=sk, timestamp=ts) for sk, ts in last_per_session])
            exit_pages = list(
                session_qs.filter(exit_filter)
                .values('path').annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
        else:
            exit_pages = []

        # ── 5. Devices / Browsers / OS ──
        device_stats = list(human_qs.values('device_type').annotate(count=Count('id')).order_by('-count'))
        browser_stats = list(human_qs.exclude(browser='').values('browser').annotate(count=Count('id')).order_by('-count')[:6])
        os_stats = list(human_qs.exclude(os='').values('os').annotate(count=Count('id')).order_by('-count')[:6])

        device_total = sum(d['count'] for d in device_stats) or 1
        device_percents = [
            {'type': d['device_type'], 'count': d['count'], 'percent': round(d['count'] / device_total * 100, 1)}
            for d in device_stats
        ]
        browser_total = sum(b['count'] for b in browser_stats) or 1
        os_total = sum(o['count'] for o in os_stats) or 1

        # ── 6. Geography ──
        country_stats = list(
            human_qs.exclude(country='').values('country')
            .annotate(count=Count('id'), visitors=Count('ip_address', distinct=True))
            .order_by('-count')[:15]
        )
        city_stats = list(
            human_qs.exclude(city='').values('city', 'country')
            .annotate(count=Count('id')).order_by('-count')[:10]
        )

        # ── 7. Referrers — aggregate in DB, parse in Python only top results ──
        referrer_rows = list(
            human_qs.exclude(referrer='')
            .values('referrer')
            .annotate(count=Count('id'))
            .order_by('-count')[:200]
        )
        referrer_domains = Counter()
        for row in referrer_rows:
            try:
                domain = urlparse(row['referrer']).netloc
                if domain:
                    referrer_domains[domain] += row['count']
            except Exception:
                pass
        top_referrers = referrer_domains.most_common(10)

        # ── 8. Hourly distribution ──
        hourly_data = list(
            human_qs.annotate(hour=TruncHour('timestamp'))
            .values('hour').annotate(count=Count('id')).order_by('hour')
        )
        hourly_distribution = [0] * 24
        for entry in hourly_data:
            hourly_distribution[entry['hour'].hour] += entry['count']

        # ── 9. New vs returning (by unique session count per IP) ──
        ip_sessions = (
            session_qs.values('ip_address')
            .annotate(session_count=Count('session_key', distinct=True))
        )
        new_count = ip_sessions.filter(session_count=1).count()
        returning_count = ip_sessions.filter(session_count__gt=1).count()

        # ── 10. Search terms ──
        from products.models import SearchQuery
        top_searches = list(
            SearchQuery.objects.order_by('-count')
            .values('query', 'count', 'results_count', 'last_searched')[:15]
        )
        zero_result_searches = list(
            SearchQuery.objects.filter(results_count=0).order_by('-count')
            .values('query', 'count')[:10]
        )

        # ── 11. Bot crawlers — group by browser only ──
        bot_browsers = list(
            all_qs.filter(is_bot=True)
            .values('browser')
            .annotate(count=Count('id'))
            .order_by('-count')[:8]
        )

        # ── 12. Audience profile: logged-in vs guest ──
        logged_in_visitors = human_qs.exclude(user__isnull=True).values('ip_address').distinct().count()
        guest_visitors = max(0, unique_visitors - logged_in_visitors)
        logged_in_pct = round(logged_in_visitors / unique_visitors * 100, 1) if unique_visitors else 0

        # ── 13. Visitor interest: top product & category pages ──
        # URLs: /products/<slug>/ for a product page
        #       /products/category/<slug>/ for a category
        #       /products/brand/<slug>/ for a brand
        #       /products/, /products/categories/, /products/brands/ are LISTING pages
        # Product pages = under /products/ but NOT under the listing/category/brand sub-routes
        product_views = (
            human_qs.filter(path__regex=r'^/(en/)?products/[^/]+/?$')
            .exclude(path__regex=r'^/(en/)?products/(categories?|brands?|search|category|brand|new|featured|best-?sellers|special-?offers|offers|tag|tags|wishlist|compare|chat)/?$')
            .values('path').annotate(views=Count('id'), visitors=Count('ip_address', distinct=True))
            .order_by('-views')[:8]
        )
        category_views = (
            human_qs.filter(path__regex=r'^/(en/)?(products/category|blog/category)/[^/]+')
            .values('path').annotate(views=Count('id'), visitors=Count('ip_address', distinct=True))
            .order_by('-views')[:8]
        )

        # ── 14. Conversion funnel: visitors → carts → orders ──
        try:
            from cart.models import Cart
            from orders.models import Order
            active_carts = Cart.objects.filter(
                is_active=True, converted_to_order=False,
                updated_at__gte=start_date,
            ).count()
            period_orders = Order.objects.filter(created_at__gte=start_date).count()
            paid_orders = Order.objects.filter(
                created_at__gte=start_date, payment_status='paid'
            ).count()
            revenue = Order.objects.filter(
                created_at__gte=start_date, payment_status='paid'
            ).aggregate(t=Sum('grand_total'))['t'] or 0
        except Exception:
            active_carts = period_orders = paid_orders = 0
            revenue = 0

        conversion_rate = round(period_orders / unique_visitors * 100, 2) if unique_visitors else 0
        cart_abandonment = (
            round((active_carts) / (active_carts + period_orders) * 100, 1)
            if (active_carts + period_orders) > 0 else 0
        )

        # ── 15. Top landing pages (first page per session) ──
        first_per_session = list(
            session_qs.values('session_key')
            .annotate(first_ts=Min('timestamp'))
            .values_list('session_key', 'first_ts')[:5000]
        )
        if first_per_session:
            landing_filter = reduce(or_, [Q(session_key=sk, timestamp=ts) for sk, ts in first_per_session])
            landing_pages = list(
                session_qs.filter(landing_filter)
                .values('path').annotate(count=Count('id'))
                .order_by('-count')[:8]
            )
        else:
            landing_pages = []

        # ── 16. Average session duration (first→last view per session) ──
        try:
            session_spans = (
                session_qs.values('session_key')
                .annotate(start=Min('timestamp'), end=Max('timestamp'))
            )
            durations = [
                (s['end'] - s['start']).total_seconds()
                for s in session_spans if s['end'] and s['start']
            ]
            multi_page = [d for d in durations if d > 0]
            avg_session_seconds = int(sum(multi_page) / len(multi_page)) if multi_page else 0
        except Exception:
            avg_session_seconds = 0
        avg_session_minutes = round(avg_session_seconds / 60, 1)

        # ── 17. Day-of-week distribution ──
        dow_counts = [0] * 7
        for entry in human_qs.values_list('timestamp', flat=True)[:50000]:
            dow_counts[entry.weekday()] += 1

        # ── 18. Insight tags for the headline ──
        peak_hour_idx = hourly_distribution.index(max(hourly_distribution)) if any(hourly_distribution) else None
        peak_hour_label = f"{peak_hour_idx:02d}:00" if peak_hour_idx is not None else "—"
        dow_names = [_('الإثنين'), _('الثلاثاء'), _('الأربعاء'), _('الخميس'), _('الجمعة'), _('السبت'), _('الأحد')]
        peak_dow = dow_names[dow_counts.index(max(dow_counts))] if any(dow_counts) else "—"
        top_country = country_stats[0]['country'] if country_stats else None
        primary_device = max(device_stats, key=lambda d: d['count'])['device_type'] if device_stats else None

        # ── 19. Hour × Day-of-week heatmap (7 rows x 24 cols) ──
        heatmap = [[0] * 24 for _ in range(7)]
        for ts in human_qs.values_list('timestamp', flat=True)[:80000]:
            heatmap[ts.weekday()][ts.hour] += 1
        heatmap_max = max((max(row) for row in heatmap), default=0)

        # ── 20. Revenue trend (daily) + AOV + RPV ──
        revenue_chart_labels, revenue_chart_values, orders_chart_values = [], [], []
        aov = 0
        rpv = 0
        try:
            from orders.models import Order
            paid_qs = Order.objects.filter(created_at__gte=start_date, payment_status='paid')
            if days <= 2:
                daily_rev = list(
                    paid_qs.annotate(date=TruncHour('created_at'))
                    .values('date').annotate(total=Sum('grand_total'), cnt=Count('id'))
                    .order_by('date')
                )
            else:
                daily_rev = list(
                    paid_qs.annotate(date=TruncDate('created_at'))
                    .values('date').annotate(total=Sum('grand_total'), cnt=Count('id'))
                    .order_by('date')
                )
            for d in daily_rev:
                dt = d['date']
                revenue_chart_labels.append(dt.strftime('%H:%M') if days <= 2 else dt.strftime('%m/%d'))
                revenue_chart_values.append(float(d['total'] or 0))
                orders_chart_values.append(d['cnt'])
            if paid_orders > 0 and revenue:
                aov = round(float(revenue) / paid_orders, 2)
            if unique_visitors > 0 and revenue:
                rpv = round(float(revenue) / unique_visitors, 2)
        except Exception:
            pass

        # ── 21. Top customers by lifetime value (all-time) ──
        top_customers = []
        try:
            from accounts.models import User
            top_customers = list(
                User.objects.filter(orders__payment_status='paid')
                .annotate(
                    ltv=Sum('orders__grand_total'),
                    order_count=Count('orders', distinct=True),
                    last_order=Max('orders__created_at'),
                )
                .filter(ltv__gt=0)
                .order_by('-ltv')
                .values('id', 'first_name', 'last_name', 'email', 'ltv', 'order_count', 'last_order')[:10]
            )
        except Exception:
            pass

        # ── 22. First vs Repeat buyers (all-time) ──
        first_time_buyers = 0
        repeat_buyers = 0
        try:
            from orders.models import Order
            buyer_orders = (
                Order.objects.filter(user__isnull=False, payment_status='paid')
                .values('user').annotate(c=Count('id'))
            )
            for b in buyer_orders:
                if b['c'] == 1:
                    first_time_buyers += 1
                else:
                    repeat_buyers += 1
        except Exception:
            pass

        # ── 23. Cart recovery: active unconverted carts with items ──
        cart_recovery = []
        cart_recovery_value = 0
        try:
            from cart.models import Cart
            active_carts_qs = (
                Cart.objects.filter(is_active=True, converted_to_order=False)
                .annotate(item_count=Count('items'))
                .filter(item_count__gt=0)
                .select_related('user')
                .prefetch_related('items__product', 'items__variant')
                .order_by('-updated_at')[:15]
            )
            for c in active_carts_qs:
                items = list(c.items.all())
                if not items:
                    continue
                try:
                    val = sum(i.total_price for i in items)
                except Exception:
                    val = 0
                user_label = ''
                if c.user:
                    user_label = c.user.get_full_name() or c.user.email
                else:
                    user_label = _('ضيف')
                cart_recovery.append({
                    'id': str(c.id),
                    'user_name': user_label,
                    'user_email': c.user.email if c.user else '',
                    'is_guest': c.user is None,
                    'item_count': len(items),
                    'total': float(val or 0),
                    'updated_at': c.updated_at,
                    'sample_product': items[0].product.name if items[0].product else '',
                })
                cart_recovery_value += float(val or 0)
        except Exception:
            pass

        # ── 24. Wishlist top items ──
        wishlist_top = []
        try:
            from products.models import Wishlist
            wl = (
                Wishlist.objects.values('product__id', 'product__name', 'product__slug')
                .annotate(wishes=Count('id'), users=Count('user', distinct=True))
                .order_by('-wishes')[:10]
            )
            for w in wl:
                if not w['product__id']:
                    continue
                wishlist_top.append({
                    'name': w['product__name'],
                    'slug': w['product__slug'],
                    'wishes': w['wishes'],
                    'users': w['users'],
                })
        except Exception:
            pass

        # ── 25. Stock vs Demand: high-viewed products with low/zero stock ──
        stock_alerts = []
        try:
            from products.models import Product
            slugs_seen = []
            # Use the top_pages list which has highest-traffic paths
            for pv in list(product_views) + list(top_pages):
                parts = pv['path'].strip('/').split('/')
                if len(parts) >= 2 and parts[0] in ('products', 'en') and parts[-1]:
                    slug = parts[-1]
                    if slug not in [s[0] for s in slugs_seen]:
                        slugs_seen.append((slug, pv.get('views', 0), pv.get('visitors', 0)))
            slugs_only = [s[0] for s in slugs_seen]
            if slugs_only:
                products_meta = {
                    p.slug: p for p in
                    Product.objects.filter(slug__in=slugs_only)
                    .only('slug', 'name', 'stock_quantity', 'stock_status', 'min_stock_level', 'track_inventory')
                }
                for slug, views, visitors in slugs_seen:
                    p = products_meta.get(slug)
                    if not p or not p.track_inventory:
                        continue
                    if p.stock_quantity == 0 or p.stock_status == 'out_of_stock':
                        severity = 'critical'
                    elif p.min_stock_level and p.stock_quantity <= p.min_stock_level:
                        severity = 'low'
                    else:
                        continue
                    stock_alerts.append({
                        'name': p.name,
                        'slug': p.slug,
                        'views': views,
                        'visitors': visitors,
                        'stock': p.stock_quantity,
                        'severity': severity,
                    })
                stock_alerts = stock_alerts[:8]
        except Exception:
            pass

        # ── 26. Slowest / bounce-prone pages ──
        slowest_pages = []
        try:
            single_page_session_keys = list(
                session_qs.values('session_key')
                .annotate(c=Count('id'))
                .filter(c=1)
                .values_list('session_key', flat=True)[:5000]
            )
            if single_page_session_keys:
                slowest_pages = list(
                    session_qs.filter(session_key__in=single_page_session_keys)
                    .values('path').annotate(bounces=Count('id'))
                    .order_by('-bounces')[:8]
                )
        except Exception:
            pass

        # ── 27. 404 errors ──
        not_found_pages = []
        try:
            not_found_pages = list(
                PageView.objects.filter(status_code=404, timestamp__gte=start_date, is_bot=False)
                .values('path').annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
        except Exception:
            pass

        # ── 28. Search → conversion ──
        search_conversion = None
        try:
            search_session_keys = list(
                session_qs.filter(path__contains='/search')
                .values_list('session_key', flat=True).distinct()[:5000]
            )
            if search_session_keys:
                converted = (
                    session_qs.filter(
                        session_key__in=search_session_keys,
                        path__regex=r'^/(en/)?products/[^/]+/?$',
                    ).values('session_key').distinct().count()
                )
                search_conversion = {
                    'searched': len(search_session_keys),
                    'viewed_product': converted,
                    'rate': round(converted / len(search_session_keys) * 100, 1) if search_session_keys else 0,
                }
        except Exception:
            pass

        # ── 29. All-time order context ──
        try:
            from orders.models import Order
            all_time_orders = Order.objects.count()
            all_time_paid_orders = Order.objects.filter(payment_status='paid').count()
            all_time_revenue = Order.objects.filter(payment_status='paid').aggregate(t=Sum('grand_total'))['t'] or 0
        except Exception:
            all_time_orders = all_time_paid_orders = 0
            all_time_revenue = 0

        context.update({
            'period': days,
            # KPIs
            'live_visitors': live_visitors,
            'today_views': today_views,
            'today_unique': today_unique,
            'weekly_views': weekly_views,
            'monthly_views': monthly_views,
            'total_views': total_views,
            'unique_visitors': unique_visitors,
            'avg_pages': avg_pages,
            'bounce_rate': bounce_rate,
            'views_change': views_change,
            'visitors_change': visitors_change,
            'bot_hits': bot_hits,
            # Charts
            'chart_labels': json.dumps(chart_labels),
            'chart_views': json.dumps(chart_views_data),
            'chart_visitors': json.dumps(chart_visitors_data),
            'hourly_distribution': json.dumps(hourly_distribution),
            # Tables
            'top_pages': top_pages,
            'exit_pages': exit_pages,
            'top_referrers': top_referrers,
            'top_searches': top_searches,
            'zero_result_searches': zero_result_searches,
            # Segments
            'device_stats': device_percents,
            'device_labels': json.dumps([d['device_type'] for d in device_stats]),
            'device_values': json.dumps([d['count'] for d in device_stats]),
            'browser_stats': browser_stats,
            'browser_total': browser_total,
            'browser_labels': json.dumps([b['browser'] for b in browser_stats]),
            'browser_values': json.dumps([b['count'] for b in browser_stats]),
            'os_stats': os_stats,
            'os_total': os_total,
            'os_labels': json.dumps([o['os'] for o in os_stats]),
            'os_values': json.dumps([o['count'] for o in os_stats]),
            # Geo
            'country_stats': country_stats,
            'city_stats': city_stats,
            # Audience
            'new_visitors': new_count,
            'returning_visitors': returning_count,
            'logged_in_visitors': logged_in_visitors,
            'guest_visitors': guest_visitors,
            'logged_in_pct': logged_in_pct,
            # Visitor interest (audience signals)
            'product_views': list(product_views),
            'category_views': list(category_views),
            # Conversion funnel
            'active_carts': active_carts,
            'period_orders': period_orders,
            'paid_orders': paid_orders,
            'revenue': revenue,
            'conversion_rate': conversion_rate,
            'cart_abandonment': cart_abandonment,
            # Engagement
            'landing_pages': landing_pages,
            'avg_session_seconds': avg_session_seconds,
            'avg_session_minutes': avg_session_minutes,
            # Time patterns
            'dow_counts': json.dumps(dow_counts),
            'peak_hour_label': peak_hour_label,
            'peak_dow': peak_dow,
            # Headline insights
            'top_country': top_country,
            'primary_device': primary_device,
            # Bots
            'bot_browsers': bot_browsers,
            # Heatmap
            'heatmap': json.dumps(heatmap),
            'heatmap_max': heatmap_max,
            # Revenue trend
            'revenue_chart_labels': json.dumps(revenue_chart_labels),
            'revenue_chart_values': json.dumps(revenue_chart_values),
            'orders_chart_values': json.dumps(orders_chart_values),
            'aov': aov,
            'rpv': rpv,
            # Top customers
            'top_customers': top_customers,
            'first_time_buyers': first_time_buyers,
            'repeat_buyers': repeat_buyers,
            # Cart recovery
            'cart_recovery': cart_recovery,
            'cart_recovery_value': cart_recovery_value,
            # Wishlist
            'wishlist_top': wishlist_top,
            # Stock alerts
            'stock_alerts': stock_alerts,
            # Slowest pages + 404 + search conversion
            'slowest_pages': slowest_pages,
            'not_found_pages': not_found_pages,
            'search_conversion': search_conversion,
            # All-time context
            'all_time_orders': all_time_orders,
            'all_time_paid_orders': all_time_paid_orders,
            'all_time_revenue': all_time_revenue,
        })
        return context


class AnalyticsAPIView(SuperuserRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        action = request.GET.get('action', '')
        now = timezone.now()

        if action == 'live':
            live_window = now - timedelta(minutes=15)
            active = (
                PageView.objects.filter(is_bot=False, timestamp__gte=live_window)
                .exclude(ip_address__isnull=True)
                .values('ip_address').distinct().count()
            )
            return JsonResponse({'active_visitors': active})

        return JsonResponse({'error': 'Unknown action'}, status=400)
