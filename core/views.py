from django.shortcuts import render
from django.views.generic import TemplateView
from django.conf import settings
from django.utils.translation import get_language
from django.db.models import Q
from django.utils import timezone
from products.models import Product, Category
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect

from .models import SiteSettings, Newsletter, SliderItem, StaticContent
from .forms import SiteSettingsForm
from events.models import Event
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _


class HomeView(TemplateView):
    """
    عرض الصفحة الرئيسية - يعرض الصفحة الرئيسية للموقع
    Home view - displays the home page of the site
    """
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة عناصر السلايدر النشطة للسياق
        context['slider_items'] = SliderItem.objects.filter(is_active=True).order_by('order')

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

        now = timezone.now()

        # الفعاليات للعرض في معرض الشرائح
        context['slider_events'] = Event.objects.filter(
            is_active=True,
            display_in__in=['slider', 'both'],
            end_date__gte=now
        ).order_by('order', 'start_date')

        return context


class AboutView(TemplateView):
    """
    عرض نبذة عنا - يعرض صفحة نبذة عن الشركة
    About view - displays the about page
    """
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة المحتوى الثابت إلى السياق
        try:
            about_content = StaticContent.objects.get(key="about")
            context['about_content'] = about_content
        except StaticContent.DoesNotExist:
            context['about_content'] = None

        return context


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


@staff_member_required
def site_settings_view(request):
    """
    عرض وتحديث إعدادات الموقع
    View and update site settings
    """
    settings = SiteSettings.get_settings()

    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            # مسح الكاش لتطبيق التغييرات فوراً
            cache.clear()
            messages.success(request, 'تم حفظ الإعدادات بنجاح')
            return redirect('site_settings')
    else:
        form = SiteSettingsForm(instance=settings)

    context = {
        'form': form,
        'settings': settings,
    }
    return render(request, 'core/site_settings.html', context)


def preview_color(request):
    """
    معاينة اللون قبل الحفظ (AJAX)
    Preview color before saving (AJAX)
    """
    if request.method == 'POST' and request.is_ajax():
        color = request.POST.get('color', '#1e88e5')

        # تحويل اللون إلى RGB
        hex_color = color.lstrip('#')
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            rgb = f"{r}, {g}, {b}"
        except:
            rgb = "30, 136, 229"

        return JsonResponse({
            'color': color,
            'rgb': rgb,
            'success': True
        })

    return JsonResponse({'success': False})

def newsletter_subscribe(request):
    """معالجة الاشتراك في النشرة البريدية مع التحقق من البريد"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        name = request.POST.get('name', '').strip()

        if not email:
            messages.error(request, _('يرجى إدخال البريد الإلكتروني'))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # التحقق من صحة البريد الإلكتروني
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messages.error(request, _('يرجى إدخال بريد إلكتروني صحيح'))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # التحقق من النطاقات المؤقتة/الوهمية
        blocked_domains = [
            'tempmail.com', 'throwaway.com', 'guerrillamail.com', 'mailinator.com',
            '10minutemail.com', 'fakeinbox.com', 'trashmail.com', 'getnada.com',
            'temp-mail.org', 'disposablemail.com', 'yopmail.com', 'sharklasers.com',
            'tempail.com', 'fakemailgenerator.com', 'emailondeck.com', 'mohmal.com'
        ]
        email_domain = email.split('@')[-1].lower()
        if email_domain in blocked_domains:
            messages.error(request, _('يرجى استخدام بريد إلكتروني حقيقي وليس مؤقت'))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        try:
            newsletter, created = Newsletter.objects.get_or_create(
                email=email,
                defaults={'name': name}
            )

            if created:
                # إنشاء رمز التحقق
                newsletter.generate_verification_token()
                newsletter.generate_unsubscribe_token()
                newsletter.verification_sent_at = timezone.now()
                newsletter.save()

                # إرسال رسالة التحقق
                send_verification_email(request, newsletter)
                messages.success(request, _('تم إرسال رسالة تأكيد إلى بريدك الإلكتروني. يرجى التحقق من صندوق الوارد.'))
            elif not newsletter.is_verified:
                # إعادة إرسال رسالة التحقق إذا لم يتم التحقق بعد
                newsletter.generate_verification_token()
                newsletter.verification_sent_at = timezone.now()
                newsletter.save()
                send_verification_email(request, newsletter)
                messages.info(request, _('تم إعادة إرسال رسالة التأكيد إلى بريدك الإلكتروني.'))
            else:
                messages.info(request, _('أنت مشترك بالفعل في النشرة البريدية.'))

        except Exception as e:
            print(f"Newsletter subscription error: {e}")
            messages.error(request, _('حدث خطأ أثناء الاشتراك. يرجى المحاولة مرة أخرى.'))

        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect('/')


def send_verification_email(request, newsletter):
    """إرسال رسالة التحقق من البريد الإلكتروني"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    # Use production URLs
    site_url = 'https://esco.jo'
    verification_url = f'https://esco.jo/newsletter/verify/{newsletter.verification_token}/'
    logo_url = 'https://esco.jo/static/images/logo.png'

    context = {
        'name': newsletter.name,
        'email': newsletter.email,
        'verification_url': verification_url,
        'site_url': site_url,
        'logo_url': logo_url,
        'year': timezone.now().year,
    }

    html_message = render_to_string('emails/newsletter_verification.html', context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject='تأكيد الاشتراك في النشرة البريدية - ESCO | Confirm Newsletter Subscription',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[newsletter.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def newsletter_verify(request, token):
    """التحقق من صحة البريد الإلكتروني"""
    try:
        newsletter = Newsletter.objects.get(verification_token=token)

        if newsletter.is_verified:
            messages.info(request, _('تم التحقق من بريدك الإلكتروني مسبقاً.'))
        else:
            newsletter.is_verified = True
            newsletter.verified_at = timezone.now()
            newsletter.verification_token = None  # إلغاء الرمز بعد الاستخدام
            newsletter.save()
            messages.success(request, _('تم تأكيد اشتراكك بنجاح! شكراً لك.'))

    except Newsletter.DoesNotExist:
        messages.error(request, _('رابط التحقق غير صالح أو منتهي الصلاحية.'))

    return redirect('/')


def newsletter_unsubscribe(request, token):
    """إلغاء الاشتراك من النشرة البريدية"""
    try:
        newsletter = Newsletter.objects.get(unsubscribe_token=token)
        newsletter.is_active = False
        newsletter.save()
        messages.success(request, _('تم إلغاء اشتراكك من النشرة البريدية بنجاح.'))
    except Newsletter.DoesNotExist:
        messages.error(request, _('رابط إلغاء الاشتراك غير صالح.'))

    return redirect('/')