from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.conf import settings
from django.utils.translation import get_language
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
        ).order_by('-published_at')[:8]

        # الحصول على أحدث المنتجات - Get latest products
        context['latest_products'] = Product.objects.filter(
            status='published',
            is_active=True
        ).order_by('-published_at')[:12]

        # الحصول على الفئات الرئيسية - Get main categories
        context['main_categories'] = Category.objects.filter(
            level=1,
            is_active=True
        ).order_by('name')

        # الحصول على المنتجات التي عليها خصم - Get discounted products
        discounted_products = []
        products = Product.objects.filter(
            status='published',
            is_active=True
        )

        for product in products:
            if product.has_discount:
                discounted_products.append(product)
                if len(discounted_products) >= 8:
                    break

        context['discounted_products'] = discounted_products

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

    activate(lang_code)
    response = HttpResponseRedirect(translate_url(request.META.get('HTTP_REFERER', '/'), lang_code))
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)

    return response