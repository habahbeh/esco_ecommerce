from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from core.models import Newsletter, SiteSettings
from products.models import Product, Brand
from dashboard.forms.newsletter_forms import NewsletterForm
from accounts.models import UserActivity
import logging
import traceback

logger = logging.getLogger(__name__)


@login_required
@permission_required('core.view_newsletter')
def dashboard_newsletters(request):
    """عرض قائمة اشتراكات النشرة البريدية"""
    newsletters = Newsletter.objects.all().order_by('-created_at')

    # إحصائيات
    total_subscribers = newsletters.count()
    verified_subscribers = newsletters.filter(is_verified=True, is_active=True).count()
    unverified_subscribers = newsletters.filter(is_verified=False).count()
    inactive_subscribers = newsletters.filter(is_active=False).count()

    context = {
        'newsletters': newsletters,
        'total_subscribers': total_subscribers,
        'verified_subscribers': verified_subscribers,
        'unverified_subscribers': unverified_subscribers,
        'inactive_subscribers': inactive_subscribers,
        'page_title': _('اشتراكات النشرة البريدية'),
        'current_page': _('اشتراكات النشرة البريدية')
    }
    return render(request, 'dashboard/newsletters/newsletter_list.html', context)


@login_required
@permission_required('core.add_newsletter')
def dashboard_newsletter_create(request):
    """إضافة اشتراك جديد في النشرة البريدية"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save()
            messages.success(request, _('تم إضافة الاشتراك بنجاح'))
            UserActivity.objects.create(
                user=request.user,
                activity_type='newsletter_create',
                description=f'Created newsletter subscription: {newsletter.email}',
                object_id=str(newsletter.pk),
                content_type='core.newsletter',
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            return redirect('dashboard:dashboard_newsletters')
    else:
        form = NewsletterForm()

    context = {
        'form': form,
        'page_title': _('إضافة اشتراك جديد'),
        'current_page': _('إضافة اشتراك جديد')
    }
    return render(request, 'dashboard/newsletters/newsletter_form.html', context)


@login_required
@permission_required('core.change_newsletter')
def dashboard_newsletter_edit(request, pk):
    """تعديل اشتراك في النشرة البريدية"""
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث الاشتراك بنجاح'))
            return redirect('dashboard:dashboard_newsletters')
    else:
        form = NewsletterForm(instance=newsletter)

    context = {
        'form': form,
        'newsletter': newsletter,
        'page_title': _('تعديل اشتراك'),
        'current_page': _('تعديل اشتراك')
    }
    return render(request, 'dashboard/newsletters/newsletter_form.html', context)


@login_required
@permission_required('core.delete_newsletter')
def dashboard_newsletter_delete(request, pk):
    """حذف اشتراك من النشرة البريدية"""
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == 'POST':
        newsletter.delete()
        messages.success(request, _('تم حذف الاشتراك بنجاح'))
        return redirect('dashboard:dashboard_newsletters')

    context = {
        'newsletter': newsletter,
        'page_title': _('حذف اشتراك'),
        'current_page': _('حذف اشتراك')
    }
    return render(request, 'dashboard/newsletters/newsletter_confirm_delete.html', context)


@login_required
@permission_required('core.change_newsletter')
def dashboard_newsletter_verify(request, pk):
    """تحقق يدوي من اشتراك في النشرة البريدية"""
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == 'POST':
        newsletter.is_verified = True
        newsletter.verified_at = timezone.now()
        newsletter.verification_token = None  # Clear the token
        newsletter.save()
        messages.success(request, _('تم التحقق من الاشتراك %s بنجاح') % newsletter.email)

    return redirect('dashboard:dashboard_newsletters')


@login_required
@permission_required('core.change_newsletter')
def dashboard_newsletter_toggle_verify(request, pk):
    """تبديل حالة التحقق من اشتراك في النشرة البريدية"""
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == 'POST':
        if newsletter.is_verified:
            newsletter.is_verified = False
            newsletter.verified_at = None
            messages.success(request, _('تم إلغاء التحقق من الاشتراك %s') % newsletter.email)
        else:
            newsletter.is_verified = True
            newsletter.verified_at = timezone.now()
            newsletter.verification_token = None
            messages.success(request, _('تم التحقق من الاشتراك %s بنجاح') % newsletter.email)
        newsletter.save()

    return redirect('dashboard:dashboard_newsletters')


@login_required
@permission_required('core.change_newsletter')
def dashboard_newsletter_send(request):
    """إرسال نشرة بريدية للمشتركين"""
    if request.method == 'POST':
        try:
            email_type = request.POST.get('email_type', 'new_products')
            subject = request.POST.get('subject', '')
            coupon_code = request.POST.get('coupon_code', '')

            # الحصول على المشتركين النشطين والموثقين فقط
            subscribers = Newsletter.objects.filter(is_active=True, is_verified=True)

            if not subscribers.exists():
                messages.warning(request, _('لا يوجد مشتركين موثقين لإرسال النشرة إليهم'))
                return redirect('dashboard:dashboard_newsletter_send')

            site_settings = SiteSettings.get_settings()
            # Use production URLs
            site_url = 'https://esco.jo'
            logo_url = 'https://esco.jo/static/images/logo.png'

            # تحديد القالب والبيانات حسب النوع
            if email_type == 'new_products':
                template_name = 'emails/newsletter_new_products.html'
                products = Product.objects.filter(
                    status='published',
                    is_active=True
                ).order_by('-created_at')[:8]

                products_data = []
                for product in products:
                    try:
                        # Use production URL for product image
                        product_image = None
                        try:
                            default_img = product.default_image
                            if default_img and default_img.image:
                                product_image = f'https://esco.jo/media/{default_img.image.name}'
                            elif product.images.exists():
                                product_image = f'https://esco.jo/media/{product.images.first().image.name}'
                        except Exception:
                            product_image = None

                        # Get prices safely
                        try:
                            current_price = str(product.current_price) if product.current_price else str(product.base_price)
                            base_price = str(product.base_price) if product.base_price else '0'
                        except Exception:
                            current_price = '0'
                            base_price = '0'

                        products_data.append({
                            'name': product.name or '',
                            'price': current_price,
                            'old_price': base_price if base_price != current_price else None,
                            'image': product_image,
                            'url': f'https://esco.jo{product.get_absolute_url()}',
                            'brand': product.brand.name if product.brand else None,
                            'discount_percentage': float(product.discount_percentage) if product.discount_percentage else None,
                        })
                    except Exception as e:
                        logger.error(f"Error processing product {product.id}: {e}")
                        continue

                base_context = {
                    'products': products_data,
                    'coupon_code': coupon_code,
                }
                default_subject = 'منتجات جديدة من ESCO | New Products from ESCO'

            elif email_type == 'new_brands':
                template_name = 'emails/newsletter_new_brands.html'
                brands = Brand.objects.filter(is_active=True).order_by('-created_at')[:6]

                brands_data = []
                for brand in brands:
                    # Use production URL for brand logo
                    brand_logo = None
                    try:
                        if brand.logo and brand.logo.name:
                            brand_logo = f'https://esco.jo/media/{brand.logo.name}'
                    except Exception:
                        brand_logo = None

                    brands_data.append({
                        'name': brand.name,
                        'description': getattr(brand, 'description', '') or '',
                        'logo': brand_logo,
                        'url': f'https://esco.jo/products/brand/{brand.slug}/',
                        'country': getattr(brand, 'country', None),
                    })

                base_context = {
                    'brands': brands_data,
                }
                default_subject = 'علامات تجارية جديدة في ESCO | New Brands at ESCO'

            elif email_type == 'promotions':
                template_name = 'emails/newsletter_promotions.html'
                products = Product.objects.filter(
                    status='published',
                    is_active=True,
                    discount_percentage__gt=0
                ).order_by('-discount_percentage')[:8]

                products_data = []
                for product in products:
                    try:
                        # Use production URL for product image
                        product_image = None
                        try:
                            default_img = product.default_image
                            if default_img and default_img.image:
                                product_image = f'https://esco.jo/media/{default_img.image.name}'
                            elif product.images.exists():
                                product_image = f'https://esco.jo/media/{product.images.first().image.name}'
                        except Exception:
                            product_image = None

                        # Get prices safely
                        try:
                            current_price = str(product.current_price) if product.current_price else str(product.base_price)
                            base_price = str(product.base_price) if product.base_price else '0'
                        except Exception:
                            current_price = '0'
                            base_price = '0'

                        products_data.append({
                            'name': product.name or '',
                            'price': current_price,
                            'old_price': base_price,
                            'image': product_image,
                            'url': f'https://esco.jo{product.get_absolute_url()}',
                            'brand': product.brand.name if product.brand else None,
                            'discount_percentage': float(product.discount_percentage) if product.discount_percentage else 0,
                        })
                    except Exception as e:
                        logger.error(f"Error processing product {product.id}: {e}")
                        continue

                base_context = {
                    'products': products_data,
                    'coupon_code': coupon_code,
                    'coupon_value': request.POST.get('coupon_value', '10%'),
                    'promotion_title': request.POST.get('promotion_title', 'عروض حصرية'),
                    'promotion_subtitle': request.POST.get('promotion_subtitle', 'خصومات تصل إلى 50%'),
                }
                default_subject = 'عروض حصرية من ESCO | Special Offers from ESCO'

            else:
                messages.error(request, _('نوع النشرة غير صحيح'))
                return redirect('dashboard:dashboard_newsletter_send')

            # استخدام الموضوع المخصص أو الافتراضي
            final_subject = subject if subject else default_subject

            # إرسال الرسائل
            success_count = 0
            error_count = 0

            for subscriber in subscribers:
                try:
                    # إنشاء رابط إلغاء الاشتراك
                    if not subscriber.unsubscribe_token:
                        subscriber.generate_unsubscribe_token()
                        subscriber.save()

                    unsubscribe_url = f'https://esco.jo/newsletter/unsubscribe/{subscriber.unsubscribe_token}/'

                    # إعداد السياق لكل مشترك
                    context = {
                        **base_context,
                        'name': subscriber.name or '',
                        'email': subscriber.email,
                        'site_url': site_url,
                        'logo_url': logo_url,
                        'unsubscribe_url': unsubscribe_url,
                        'year': timezone.now().year,
                    }

                    html_message = render_to_string(template_name, context)
                    plain_message = strip_tags(html_message)

                    send_mail(
                        subject=final_subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[subscriber.email],
                        html_message=html_message,
                        fail_silently=False,
                    )

                    # تحديث إحصائيات المشترك
                    subscriber.emails_received += 1
                    subscriber.last_email_sent = timezone.now()
                    subscriber.save()

                    success_count += 1

                except Exception as e:
                    logger.error(f"Error sending to {subscriber.email}: {e}")
                    error_count += 1

            if success_count > 0:
                messages.success(request, _('تم إرسال النشرة البريدية بنجاح إلى %s مشترك') % success_count)
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='newsletter_send',
                    description=f'Sent {email_type} newsletter to {success_count} subscribers',
                    object_id='',
                    content_type='core.newsletter',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
            if error_count > 0:
                messages.warning(request, _('فشل إرسال %s رسالة') % error_count)

            return redirect('dashboard:dashboard_newsletters')

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Newsletter send error: {e}\n{error_traceback}")
            print(f"Newsletter send error: {e}\n{error_traceback}")  # For server logs
            messages.error(request, _('حدث خطأ أثناء إرسال النشرة البريدية: %s') % str(e))
            return redirect('dashboard:dashboard_newsletter_send')

    # GET request - عرض نموذج الإرسال
    subscribers_count = Newsletter.objects.filter(is_active=True, is_verified=True).count()

    context = {
        'subscribers_count': subscribers_count,
        'page_title': _('إرسال نشرة بريدية'),
        'current_page': _('إرسال نشرة بريدية')
    }
    return render(request, 'dashboard/newsletters/newsletter_send.html', context)