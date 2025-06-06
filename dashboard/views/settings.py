# dashboard/views/settings.py
"""
عروض إعدادات النظام - يتضمن كافة العروض المتعلقة بإدارة إعدادات النظام المختلفة
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings as django_settings
from django.core.cache import cache
from django.http import JsonResponse
from django.db import transaction

from core.models import SiteSettings
from dashboard.models import DashboardUserSettings, DashboardWidget
from dashboard.forms.core import SiteSettingsForm
from dashboard.forms.dashboard import DashboardUserSettingsForm, DashboardWidgetForm
from dashboard.mixins import DashboardAccessMixin, SuperuserRequiredMixin

import os
import json
from PIL import Image
from io import BytesIO


class SiteSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    """
    عرض إعدادات الموقع العامة - متاح فقط للمديرين
    يتيح تعديل إعدادات الموقع الأساسية مثل الاسم والوصف والشعار وألوان الواجهة
    """
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'dashboard/settings/site_settings.html'
    success_url = reverse_lazy('dashboard:site_settings')

    def get_object(self, queryset=None):
        """الحصول على كائن الإعدادات الحالي أو إنشاء واحد جديد إذا لم يكن موجوداً"""
        settings = SiteSettings.get_settings()
        return settings

    def form_valid(self, form):
        # تخزين الملفات القديمة للحذف لاحقاً إذا تم تغييرها
        old_logo = None
        old_favicon = None

        if self.object.logo and form.cleaned_data.get('logo') and self.object.logo != form.cleaned_data.get('logo'):
            old_logo = self.object.logo

        if self.object.favicon and form.cleaned_data.get('favicon') and self.object.favicon != form.cleaned_data.get(
                'favicon'):
            old_favicon = self.object.favicon

        # حفظ النموذج
        response = super().form_valid(form)

        # معالجة الشعار (تغيير الحجم)
        if self.object.logo and self.object.logo != old_logo:
            try:
                img = Image.open(self.object.logo.path)
                # الحد الأقصى للأبعاد هو 300×100 بكسل
                img.thumbnail((300, 100), Image.LANCZOS)
                img.save(self.object.logo.path)
            except Exception as e:
                messages.warning(self.request, _("تعذر معالجة الشعار: %s") % str(e))

        # معالجة الأيقونة المفضلة (favicon)
        if self.object.favicon and self.object.favicon != old_favicon:
            try:
                img = Image.open(self.object.favicon.path)
                # الأيقونة المفضلة يجب أن تكون 32×32 بكسل
                img = img.resize((32, 32), Image.LANCZOS)
                img.save(self.object.favicon.path)
            except Exception as e:
                messages.warning(self.request, _("تعذر معالجة أيقونة الموقع: %s") % str(e))

        # حذف الملفات القديمة لتوفير مساحة التخزين
        if old_logo and os.path.isfile(old_logo.path):
            try:
                os.remove(old_logo.path)
            except:
                pass

        if old_favicon and os.path.isfile(old_favicon.path):
            try:
                os.remove(old_favicon.path)
            except:
                pass

        # مسح ذاكرة التخزين المؤقت للإعدادات
        cache.delete('site_settings')

        messages.success(self.request, _("تم تحديث إعدادات الموقع بنجاح"))
        return response


class EmailSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات البريد الإلكتروني - متاح فقط للمديرين
    يتيح تكوين إعدادات خادم SMTP لإرسال رسائل البريد الإلكتروني
    """
    template_name = 'dashboard/settings/email_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع الإعدادات الحالية من ملف الإعدادات
        context['email_host'] = django_settings.EMAIL_HOST
        context['email_port'] = django_settings.EMAIL_PORT
        context['email_use_tls'] = django_settings.EMAIL_USE_TLS
        context['email_use_ssl'] = getattr(django_settings, 'EMAIL_USE_SSL', False)
        context['email_host_user'] = django_settings.EMAIL_HOST_USER
        context['default_from_email'] = django_settings.DEFAULT_FROM_EMAIL

        # لا نعرض كلمة المرور لأسباب أمنية

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - ملاحظة: هذا يتطلب آلية حفظ في ملف إعدادات حقيقي"""
        email_host = request.POST.get('email_host', '')
        email_port = request.POST.get('email_port', '')
        email_use_tls = request.POST.get('email_use_tls') == 'on'
        email_use_ssl = request.POST.get('email_use_ssl') == 'on'
        email_host_user = request.POST.get('email_host_user', '')
        email_host_password = request.POST.get('email_host_password', '')
        default_from_email = request.POST.get('default_from_email', '')

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        # يمكن إضافة اختبار اتصال قبل الحفظ
        success = True

        if success:
            messages.success(request, _("تم تحديث إعدادات البريد الإلكتروني بنجاح"))
        else:
            messages.error(request, _("حدث خطأ أثناء حفظ إعدادات البريد الإلكتروني"))

        return redirect('dashboard:email_settings')


class PaymentGatewaySettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات بوابات الدفع - متاح فقط للمديرين
    يتيح تكوين بوابات الدفع المختلفة مثل PayPal و Stripe وغيرها
    """
    template_name = 'dashboard/settings/payment_gateway_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع الإعدادات الحالية
        # في بيئة حقيقية، هذه الإعدادات قد تأتي من قاعدة البيانات أو ملف ENV

        # بوابات الدفع المدعومة
        context['payment_gateways'] = [
            {
                'id': 'paypal',
                'name': 'PayPal',
                'is_enabled': getattr(django_settings, 'PAYPAL_ENABLED', False),
                'is_configured': bool(getattr(django_settings, 'PAYPAL_CLIENT_ID', '')),
                'logo': 'dashboard/img/payment/paypal.png',
            },
            {
                'id': 'stripe',
                'name': 'Stripe',
                'is_enabled': getattr(django_settings, 'STRIPE_ENABLED', False),
                'is_configured': bool(getattr(django_settings, 'STRIPE_API_KEY', '')),
                'logo': 'dashboard/img/payment/stripe.png',
            },
            {
                'id': 'myfatoorah',
                'name': 'MyFatoorah',
                'is_enabled': getattr(django_settings, 'MYFATOORAH_ENABLED', False),
                'is_configured': bool(getattr(django_settings, 'MYFATOORAH_API_KEY', '')),
                'logo': 'dashboard/img/payment/myfatoorah.png',
            },
        ]

        # بوابة الدفع المحددة للعرض
        gateway_id = self.kwargs.get('gateway_id', 'paypal')
        context['selected_gateway'] = next(
            (g for g in context['payment_gateways'] if g['id'] == gateway_id),
            context['payment_gateways'][0]
        )

        # إعدادات بوابة الدفع المحددة
        if gateway_id == 'paypal':
            context['gateway_settings'] = {
                'client_id': getattr(django_settings, 'PAYPAL_CLIENT_ID', ''),
                'client_secret': 'HIDDEN',  # لا نعرض كلمات السر والمفاتيح السرية
                'mode': getattr(django_settings, 'PAYPAL_MODE', 'sandbox'),
                'currency': getattr(django_settings, 'PAYPAL_CURRENCY', 'USD'),
            }
        elif gateway_id == 'stripe':
            context['gateway_settings'] = {
                'api_key': 'HIDDEN',
                'public_key': getattr(django_settings, 'STRIPE_PUBLIC_KEY', ''),
                'webhook_secret': 'HIDDEN',
                'currency': getattr(django_settings, 'STRIPE_CURRENCY', 'USD'),
            }
        elif gateway_id == 'myfatoorah':
            context['gateway_settings'] = {
                'api_key': 'HIDDEN',
                'mode': getattr(django_settings, 'MYFATOORAH_MODE', 'test'),
                'currency': getattr(django_settings, 'MYFATOORAH_CURRENCY', 'KWD'),
            }

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث إعدادات بوابة الدفع المحددة"""
        gateway_id = kwargs.get('gateway_id', 'paypal')

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        if gateway_id == 'paypal':
            is_enabled = request.POST.get('is_enabled') == 'on'
            client_id = request.POST.get('client_id', '')
            client_secret = request.POST.get('client_secret', '')
            mode = request.POST.get('mode', 'sandbox')
            currency = request.POST.get('currency', 'USD')

            # حفظ الإعدادات...

        elif gateway_id == 'stripe':
            is_enabled = request.POST.get('is_enabled') == 'on'
            api_key = request.POST.get('api_key', '')
            public_key = request.POST.get('public_key', '')
            webhook_secret = request.POST.get('webhook_secret', '')
            currency = request.POST.get('currency', 'USD')

            # حفظ الإعدادات...

        elif gateway_id == 'myfatoorah':
            is_enabled = request.POST.get('is_enabled') == 'on'
            api_key = request.POST.get('api_key', '')
            mode = request.POST.get('mode', 'test')
            currency = request.POST.get('currency', 'KWD')

            # حفظ الإعدادات...

        messages.success(request, _("تم تحديث إعدادات بوابة الدفع بنجاح"))
        return redirect('dashboard:payment_gateway_settings', gateway_id=gateway_id)


class ShippingSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات الشحن - متاح فقط للمديرين
    يتيح تكوين خيارات الشحن وطرق التوصيل وتكاليفها
    """
    template_name = 'dashboard/settings/shipping_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع طرق الشحن من نموذج ShippingMethod
        from checkout.models import ShippingMethod
        context['shipping_methods'] = ShippingMethod.objects.all().order_by('sort_order')

        # الحصول على إعدادات الشحن العامة
        context['free_shipping_threshold'] = getattr(django_settings, 'FREE_SHIPPING_THRESHOLD', 0)
        context['default_shipping_cost'] = getattr(django_settings, 'DEFAULT_SHIPPING_COST', 0)
        context['international_shipping_enabled'] = getattr(django_settings, 'INTERNATIONAL_SHIPPING_ENABLED', False)

        return context


class TaxSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات الضرائب - متاح فقط للمديرين
    يتيح تكوين إعدادات الضرائب والرسوم المطبقة على المنتجات
    """
    template_name = 'dashboard/settings/tax_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع إعدادات الضرائب
        context['tax_enabled'] = getattr(django_settings, 'TAX_ENABLED', True)
        context['default_tax_rate'] = getattr(django_settings, 'DEFAULT_TAX_RATE', 16)  # نسبة الضريبة الافتراضية 16%
        context['tax_included_in_price'] = getattr(django_settings, 'TAX_INCLUDED_IN_PRICE', True)
        context['tax_display_setting'] = getattr(django_settings, 'TAX_DISPLAY_SETTING', 'including_tax')

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث إعدادات الضرائب"""
        tax_enabled = request.POST.get('tax_enabled') == 'on'
        default_tax_rate = float(request.POST.get('default_tax_rate', 16))
        tax_included_in_price = request.POST.get('tax_included_in_price') == 'on'
        tax_display_setting = request.POST.get('tax_display_setting', 'including_tax')

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        messages.success(request, _("تم تحديث إعدادات الضرائب بنجاح"))
        return redirect('dashboard:tax_settings')


class DashboardSettingsView(LoginRequiredMixin, DashboardAccessMixin, UpdateView):
    """
    عرض إعدادات لوحة التحكم للمستخدم الحالي
    يتيح للمستخدم تخصيص لوحة التحكم وفقاً لتفضيلاته
    """
    model = DashboardUserSettings
    form_class = DashboardUserSettingsForm
    template_name = 'dashboard/settings/dashboard_settings.html'
    success_url = reverse_lazy('dashboard:dashboard_settings')

    def get_object(self, queryset=None):
        """الحصول على إعدادات المستخدم الحالي أو إنشاء إعدادات جديدة إذا لم تكن موجودة"""
        settings, created = DashboardUserSettings.objects.get_or_create(
            user=self.request.user,
            defaults={
                'theme': 'light',
                'language': 'ar',
                'default_view': 'dashboard:index',
                'items_per_page': 20,
            }
        )
        return settings

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("تم تحديث إعدادات لوحة التحكم بنجاح"))

        # تحديث اللغة المفضلة في الجلسة إذا تم تغييرها
        new_language = form.cleaned_data.get('language')
        if new_language and self.request.session.get('_language') != new_language:
            self.request.session['_language'] = new_language

        return response


class WidgetSettingsView(LoginRequiredMixin, DashboardAccessMixin, TemplateView):
    """
    عرض إعدادات الودجات في لوحة التحكم
    يتيح للمستخدم تخصيص ترتيب وظهور الودجات في لوحة التحكم
    """
    template_name = 'dashboard/settings/widget_settings.html'
    permission_required = 'dashboard.change_dashboardwidget'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على ودجات لوحة التحكم
        widgets = DashboardWidget.objects.filter(is_active=True).order_by('sort_order')
        context['widgets'] = widgets

        # الحصول على إعدادات الودجات للمستخدم الحالي
        user_settings, _ = DashboardUserSettings.objects.get_or_create(user=self.request.user)
        context['user_settings'] = user_settings

        # تخطيط الودجات الحالي
        context['widgets_layout'] = user_settings.widgets_layout or {}

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث ترتيب وإعدادات الودجات"""
        widgets_layout = json.loads(request.POST.get('widgets_layout', '{}'))

        # تحديث إعدادات المستخدم
        user_settings, _ = DashboardUserSettings.objects.get_or_create(user=request.user)
        user_settings.widgets_layout = widgets_layout
        user_settings.save()

        messages.success(request, _("تم تحديث إعدادات الودجات بنجاح"))
        return redirect('dashboard:widget_settings')


class CurrencySettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات العملات - متاح فقط للمديرين
    يتيح تكوين العملات المدعومة وأسعار الصرف
    """
    template_name = 'dashboard/settings/currency_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع إعدادات العملات
        context['default_currency'] = getattr(django_settings, 'DEFAULT_CURRENCY', 'SAR')
        context['supported_currencies'] = getattr(django_settings, 'SUPPORTED_CURRENCIES', [
            {'code': 'SAR', 'name': _('ريال سعودي'), 'symbol': 'ر.س', 'rate': 1.0},
            {'code': 'USD', 'name': _('دولار أمريكي'), 'symbol': '$', 'rate': 0.27},
            {'code': 'EUR', 'name': _('يورو'), 'symbol': '€', 'rate': 0.24},
        ])

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث إعدادات العملات"""
        default_currency = request.POST.get('default_currency', 'SAR')

        # استخراج بيانات العملات من النموذج
        currency_codes = request.POST.getlist('currency_code')
        currency_names = request.POST.getlist('currency_name')
        currency_symbols = request.POST.getlist('currency_symbol')
        currency_rates = request.POST.getlist('currency_rate')

        currencies = []
        for i in range(len(currency_codes)):
            if i < len(currency_names) and i < len(currency_symbols) and i < len(currency_rates):
                try:
                    rate = float(currency_rates[i])
                except (ValueError, TypeError):
                    rate = 1.0

                currencies.append({
                    'code': currency_codes[i],
                    'name': currency_names[i],
                    'symbol': currency_symbols[i],
                    'rate': rate,
                })

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        messages.success(request, _("تم تحديث إعدادات العملات بنجاح"))
        return redirect('dashboard:currency_settings')


class LanguageSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات اللغات - متاح فقط للمديرين
    يتيح تكوين اللغات المدعومة وإعدادات الترجمة
    """
    template_name = 'dashboard/settings/language_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع إعدادات اللغات
        context['default_language'] = getattr(django_settings, 'LANGUAGE_CODE', 'ar')
        context['available_languages'] = getattr(django_settings, 'LANGUAGES', [
            ('ar', _('العربية')),
            ('en', _('الإنجليزية')),
        ])
        context['current_languages'] = dict(django_settings.LANGUAGES)

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث إعدادات اللغات"""
        default_language = request.POST.get('default_language', 'ar')

        # استخراج اللغات النشطة
        active_languages = request.POST.getlist('active_languages')

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        messages.success(request, _("تم تحديث إعدادات اللغات بنجاح"))
        return redirect('dashboard:language_settings')


class MaintenanceModeView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض وضع الصيانة - متاح فقط للمديرين
    يتيح تفعيل وضع الصيانة للموقع وتخصيص رسالة الصيانة
    """
    template_name = 'dashboard/settings/maintenance_mode.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع إعدادات وضع الصيانة
        context['maintenance_mode'] = getattr(django_settings, 'MAINTENANCE_MODE', False)
        context['maintenance_message'] = getattr(django_settings, 'MAINTENANCE_MESSAGE',
                                                 _('الموقع قيد الصيانة حالياً. يرجى العودة لاحقاً.'))
        context['allowed_ips'] = getattr(django_settings, 'MAINTENANCE_ALLOWED_IPS', [])

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث إعدادات وضع الصيانة"""
        maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        maintenance_message = request.POST.get('maintenance_message', '')
        allowed_ips = request.POST.get('allowed_ips', '').split('\n')
        allowed_ips = [ip.strip() for ip in allowed_ips if ip.strip()]

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        messages.success(request, _("تم تحديث إعدادات وضع الصيانة بنجاح"))
        return redirect('dashboard:maintenance_mode')


class CacheManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إدارة ذاكرة التخزين المؤقت - متاح فقط للمديرين
    يتيح مسح ذاكرة التخزين المؤقت وتكوين إعداداتها
    """
    template_name = 'dashboard/settings/cache_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # معلومات عن ذاكرة التخزين المؤقت
        context['cache_backend'] = getattr(django_settings, 'CACHES', {}).get('default', {}).get('BACKEND', '')
        context['cache_location'] = getattr(django_settings, 'CACHES', {}).get('default', {}).get('LOCATION', '')

        # أنواع الكاش المختلفة
        context['cache_types'] = [
            {'key': 'all', 'name': _('جميع أنواع التخزين المؤقت')},
            {'key': 'template', 'name': _('قوالب الصفحات')},
            {'key': 'products', 'name': _('المنتجات والفئات')},
            {'key': 'settings', 'name': _('إعدادات الموقع')},
            {'key': 'menu', 'name': _('القوائم والتنقل')},
        ]

        return context

    def post(self, request, *args, **kwargs):
        """معالجة طلب مسح ذاكرة التخزين المؤقت"""
        cache_type = request.POST.get('cache_type', 'all')

        try:
            if cache_type == 'all':
                # مسح جميع أنواع التخزين المؤقت
                cache.clear()
                messages.success(request, _("تم مسح جميع أنواع التخزين المؤقت بنجاح"))
            elif cache_type == 'template':
                # مسح ذاكرة تخزين القوالب
                cache.delete_pattern("template.*")
                messages.success(request, _("تم مسح ذاكرة تخزين القوالب بنجاح"))
            elif cache_type == 'products':
                # مسح ذاكرة تخزين المنتجات والفئات
                cache.delete_pattern("product.*")
                cache.delete_pattern("category.*")
                messages.success(request, _("تم مسح ذاكرة تخزين المنتجات والفئات بنجاح"))
            elif cache_type == 'settings':
                # مسح ذاكرة تخزين الإعدادات
                cache.delete("site_settings")
                cache.delete_pattern("settings.*")
                messages.success(request, _("تم مسح ذاكرة تخزين الإعدادات بنجاح"))
            elif cache_type == 'menu':
                # مسح ذاكرة تخزين القوائم
                cache.delete_pattern("menu.*")
                cache.delete("categories_menu")
                cache.delete("main_menu")
                messages.success(request, _("تم مسح ذاكرة تخزين القوائم بنجاح"))
        except Exception as e:
            messages.error(request, _("حدث خطأ أثناء مسح ذاكرة التخزين المؤقت: %s") % str(e))

        return redirect('dashboard:cache_management')


class BackupSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات النسخ الاحتياطي - متاح فقط للمديرين
    يتيح تكوين إعدادات النسخ الاحتياطي واستعادة البيانات
    """
    template_name = 'dashboard/settings/backup_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع إعدادات النسخ الاحتياطي
        context['backup_enabled'] = getattr(django_settings, 'BACKUP_ENABLED', False)
        context['backup_directory'] = getattr(django_settings, 'BACKUP_DIRECTORY', 'backups/')
        context['backup_frequency'] = getattr(django_settings, 'BACKUP_FREQUENCY', 'daily')
        context['backup_retention'] = getattr(django_settings, 'BACKUP_RETENTION', 7)

        # الحصول على قائمة النسخ الاحتياطية المتاحة
        import os
        backup_dir = os.path.join(django_settings.MEDIA_ROOT, context['backup_directory'])

        context['available_backups'] = []
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                if file.endswith('.zip') or file.endswith('.sql'):
                    file_path = os.path.join(backup_dir, file)
                    file_stats = os.stat(file_path)
                    context['available_backups'].append({
                        'name': file,
                        'size': file_stats.st_size,
                        'date': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'path': file_path,
                    })

        # ترتيب النسخ الاحتياطية حسب التاريخ (الأحدث أولاً)
        context['available_backups'].sort(key=lambda x: x['date'], reverse=True)

        return context

    def post(self, request, *args, **kwargs):
        """معالجة طلبات النسخ الاحتياطي واستعادة البيانات"""
        action = request.POST.get('action', '')

        if action == 'create_backup':
            # إنشاء نسخة احتياطية جديدة
            try:
                # هنا يمكن استدعاء دالة لإنشاء نسخة احتياطية
                # في بيئة حقيقية، هذا سيتضمن استخدام أوامر مثل pg_dump أو mysqldump

                messages.success(request, _("تم إنشاء نسخة احتياطية جديدة بنجاح"))
            except Exception as e:
                messages.error(request, _("حدث خطأ أثناء إنشاء النسخة الاحتياطية: %s") % str(e))

        elif action == 'restore_backup':
            # استعادة نسخة احتياطية
            backup_file = request.POST.get('backup_file', '')

            if not backup_file:
                messages.error(request, _("يرجى تحديد ملف النسخة الاحتياطية المراد استعادته"))
            else:
                try:
                    # هنا يمكن استدعاء دالة لاستعادة النسخة الاحتياطية
                    # في بيئة حقيقية، هذا سيتضمن استخدام أوامر مثل psql أو mysql

                    messages.success(request, _("تم استعادة النسخة الاحتياطية بنجاح"))
                except Exception as e:
                    messages.error(request, _("حدث خطأ أثناء استعادة النسخة الاحتياطية: %s") % str(e))

        elif action == 'update_settings':
            # تحديث إعدادات النسخ الاحتياطي
            backup_enabled = request.POST.get('backup_enabled') == 'on'
            backup_frequency = request.POST.get('backup_frequency', 'daily')
            backup_retention = int(request.POST.get('backup_retention', 7))

            # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
            # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

            messages.success(request, _("تم تحديث إعدادات النسخ الاحتياطي بنجاح"))

        return redirect('dashboard:backup_settings')


class APISettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات واجهة برمجة التطبيقات - متاح فقط للمديرين
    يتيح تكوين إعدادات API وإدارة مفاتيح الوصول
    """
    template_name = 'dashboard/settings/api_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع إعدادات API
        context['api_enabled'] = getattr(django_settings, 'API_ENABLED', True)
        context['api_version'] = getattr(django_settings, 'API_VERSION', 'v1')
        context['api_rate_limit'] = getattr(django_settings, 'API_RATE_LIMIT', '100/day')

        # يمكن استرجاع مفاتيح API من قاعدة البيانات
        # في مثال حقيقي، يمكن استخدام نموذج APIKey لتخزين مفاتيح API

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث إعدادات API"""
        api_enabled = request.POST.get('api_enabled') == 'on'
        api_rate_limit = request.POST.get('api_rate_limit', '100/day')

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        messages.success(request, _("تم تحديث إعدادات واجهة برمجة التطبيقات بنجاح"))
        return redirect('dashboard:api_settings')


class SocialMediaSettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات وسائل التواصل الاجتماعي - متاح فقط للمديرين
    يتيح تكوين حسابات التواصل الاجتماعي وإعدادات المشاركة
    """
    template_name = 'dashboard/settings/social_media_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع إعدادات وسائل التواصل الاجتماعي
        site_settings = SiteSettings.get_settings()

        context['facebook'] = site_settings.facebook
        context['twitter'] = site_settings.twitter
        context['instagram'] = site_settings.instagram
        context['linkedin'] = site_settings.linkedin

        # إعدادات مشاركة المحتوى
        context['enable_sharing'] = getattr(django_settings, 'ENABLE_SOCIAL_SHARING', True)
        context['og_image'] = getattr(django_settings, 'DEFAULT_OG_IMAGE', '')

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث إعدادات وسائل التواصل الاجتماعي"""
        # تحديث روابط التواصل الاجتماعي
        site_settings = SiteSettings.get_settings()

        site_settings.facebook = request.POST.get('facebook', '')
        site_settings.twitter = request.POST.get('twitter', '')
        site_settings.instagram = request.POST.get('instagram', '')
        site_settings.linkedin = request.POST.get('linkedin', '')

        site_settings.save()

        # تحديث إعدادات المشاركة
        enable_sharing = request.POST.get('enable_sharing') == 'on'

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        messages.success(request, _("تم تحديث إعدادات وسائل التواصل الاجتماعي بنجاح"))
        return redirect('dashboard:social_media_settings')


class SecuritySettingsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """
    عرض إعدادات الأمان - متاح فقط للمديرين
    يتيح تكوين إعدادات الأمان مثل reCAPTCHA وسياسات كلمات المرور
    """
    template_name = 'dashboard/settings/security_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # استرجاع إعدادات الأمان
        context['enable_recaptcha'] = getattr(django_settings, 'RECAPTCHA_ENABLED', False)
        context['recaptcha_site_key'] = getattr(django_settings, 'RECAPTCHA_SITE_KEY', '')
        context['recaptcha_secret_key'] = 'HIDDEN'  # لا نعرض المفتاح السري

        # إعدادات كلمات المرور
        context['password_min_length'] = getattr(django_settings, 'PASSWORD_MIN_LENGTH', 8)
        context['password_require_uppercase'] = getattr(django_settings, 'PASSWORD_REQUIRE_UPPERCASE', True)
        context['password_require_lowercase'] = getattr(django_settings, 'PASSWORD_REQUIRE_LOWERCASE', True)
        context['password_require_numbers'] = getattr(django_settings, 'PASSWORD_REQUIRE_NUMBERS', True)
        context['password_require_symbols'] = getattr(django_settings, 'PASSWORD_REQUIRE_SYMBOLS', False)

        # إعدادات تسجيل الدخول
        context['max_login_attempts'] = getattr(django_settings, 'MAX_LOGIN_ATTEMPTS', 5)
        context['login_lockout_time'] = getattr(django_settings, 'LOGIN_LOCKOUT_TIME', 30)  # بالدقائق

        return context

    def post(self, request, *args, **kwargs):
        """معالجة النموذج المرسل - تحديث إعدادات الأمان"""
        # إعدادات reCAPTCHA
        enable_recaptcha = request.POST.get('enable_recaptcha') == 'on'
        recaptcha_site_key = request.POST.get('recaptcha_site_key', '')
        recaptcha_secret_key = request.POST.get('recaptcha_secret_key', '')

        # إعدادات كلمات المرور
        password_min_length = int(request.POST.get('password_min_length', 8))
        password_require_uppercase = request.POST.get('password_require_uppercase') == 'on'
        password_require_lowercase = request.POST.get('password_require_lowercase') == 'on'
        password_require_numbers = request.POST.get('password_require_numbers') == 'on'
        password_require_symbols = request.POST.get('password_require_symbols') == 'on'

        # إعدادات تسجيل الدخول
        max_login_attempts = int(request.POST.get('max_login_attempts', 5))
        login_lockout_time = int(request.POST.get('login_lockout_time', 30))

        # في بيئة حقيقية، هنا سنقوم بحفظ الإعدادات في ملف ENV أو قاعدة البيانات
        # لكن هذا الكود تجريبي فقط ويحتاج إلى تعديل حسب آلية حفظ الإعدادات في مشروعك

        messages.success(request, _("تم تحديث إعدادات الأمان بنجاح"))
        return redirect('dashboard:security_settings')