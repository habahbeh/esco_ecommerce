from django.shortcuts import render
from django.views.generic import TemplateView
from django.conf import settings
from django.utils.translation import get_language
from django.db.models import Q
from django.utils import timezone
from products.models import Product, Category


class HomeView(TemplateView):
    """
    عرض الصفحة الرئيسية - يعرض الصفحة الرئيسية للموقع
    Home view - displays the home page of the site
    """
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على المنتجات المميزة - Get featured products
        context['featured_products'] = Product.objects.filter(
            is_featured=True,
            status='published',
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images').order_by('-published_at')[:8]

        # الحصول على أحدث المنتجات - Get latest products
        context['latest_products'] = Product.objects.filter(
            status='published',
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images').order_by('-published_at')[:12]

        # الحصول على الفئات الرئيسية - Get main categories
        # تغيير من level=1 إلى parent=None للحصول على الفئات الجذر
        context['main_categories'] = Category.objects.filter(
            parent=None,  # الفئات التي ليس لها أب (الفئات الرئيسية)
            is_active=True
        ).order_by('sort_order', 'name')  # استخدام sort_order أولاً ثم name

        # الحصول على المنتجات التي عليها خصم - Get discounted products (محسن)
        now = timezone.now()
        context['discounted_products'] = Product.objects.filter(
            status='published',
            is_active=True
        ).filter(
            Q(discount_percentage__gt=0) | Q(discount_amount__gt=0)
        ).filter(
            Q(discount_start__isnull=True) | Q(discount_start__lte=now)
        ).filter(
            Q(discount_end__isnull=True) | Q(discount_end__gte=now)
        ).select_related('category', 'brand').prefetch_related('images').order_by('-discount_percentage')[:8]

        return context


class AboutView(TemplateView):
    """
    عرض نبذة عنا - يعرض صفحة نبذة عن الشركة
    About view - displays the about page
    """
    template_name = 'core/about.html'


class ContactView(TemplateView):
    """
    عرض اتصل بنا - يعرض صفحة الاتصال
    Contact view - displays the contact page
    """
    template_name = 'core/contact.html'


class TermsView(TemplateView):
    """
    عرض الشروط والأحكام - يعرض صفحة الشروط والأحكام
    Terms view - displays the terms and conditions page
    """
    template_name = 'core/terms.html'


class PrivacyView(TemplateView):
    """
    عرض سياسة الخصوصية - يعرض صفحة سياسة الخصوصية
    Privacy view - displays the privacy policy page
    """
    template_name = 'core/privacy.html'


def set_language(request, lang_code):
    """
    تغيير لغة الموقع - يتيح للمستخدم تغيير لغة الموقع
    Set language - allows the user to change the site language
    """
    from django.http import HttpResponseRedirect
    from django.urls import translate_url
    from django.utils.translation import activate
    from django.utils.http import url_has_allowed_host_and_scheme

    # التحقق من صحة كود اللغة
    if lang_code not in [lang[0] for lang in settings.LANGUAGES]:
        lang_code = settings.LANGUAGE_CODE

    activate(lang_code)

    # الحصول على الرابط السابق بشكل آمن
    next_url = request.META.get('HTTP_REFERER', '/')

    # التحقق من أن الرابط آمن ومن نفس الموقع
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = '/'

    # ترجمة الرابط إلى اللغة الجديدة
    try:
        next_url = translate_url(next_url, lang_code)
    except:
        # في حالة فشل الترجمة، استخدم الصفحة الرئيسية
        next_url = '/'

    response = HttpResponseRedirect(next_url)
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang_code,
        max_age=settings.LANGUAGE_COOKIE_AGE if hasattr(settings, 'LANGUAGE_COOKIE_AGE') else None,
        path=settings.LANGUAGE_COOKIE_PATH if hasattr(settings, 'LANGUAGE_COOKIE_PATH') else '/',
        domain=settings.LANGUAGE_COOKIE_DOMAIN if hasattr(settings, 'LANGUAGE_COOKIE_DOMAIN') else None,
        secure=settings.LANGUAGE_COOKIE_SECURE if hasattr(settings, 'LANGUAGE_COOKIE_SECURE') else False,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY if hasattr(settings, 'LANGUAGE_COOKIE_HTTPONLY') else False,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE if hasattr(settings, 'LANGUAGE_COOKIE_SAMESITE') else None,
    )

    return response