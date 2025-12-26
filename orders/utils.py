"""
Order utilities for email notifications
أدوات الطلبات للإشعارات بالبريد الإلكتروني
"""
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_site_url():
    """
    Get the site URL - always use production URL
    الحصول على رابط الموقع - استخدام رابط الإنتاج دائماً
    """
    # Always use production URL for email links
    return 'https://esco.jo'


def send_order_confirmation_email(order):
    """
    Send order confirmation email to customer
    إرسال بريد إلكتروني لتأكيد الطلب للعميل

    Args:
        order: Order instance

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Prepare context for email template
        context = {
            'order': order,
            'site_url': get_site_url(),
            'year': timezone.now().year,
        }

        # Render email template
        html_content = render_to_string('emails/order_confirmation.html', context)
        text_content = strip_tags(html_content)

        # Email subject (bilingual)
        subject = f'تأكيد الطلب #{order.order_number} | Order Confirmation - ESCO'

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )

        # Attach HTML version
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send(fail_silently=False)

        logger.info(f'Order confirmation email sent successfully for order #{order.order_number} to {order.email}')
        return True

    except Exception as e:
        logger.error(f'Failed to send order confirmation email for order #{order.order_number}: {str(e)}')
        return False


def send_order_status_update_email(order, old_status=None):
    """
    Send order status update email to customer
    إرسال بريد إلكتروني لتحديث حالة الطلب للعميل

    Args:
        order: Order instance
        old_status: Previous order status (optional)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # التحقق من وجود بريد إلكتروني للعميل
    if not order.email:
        logger.warning(f'Cannot send order status email for order #{order.order_number}: No customer email')
        return False

    try:
        # Define status messages in both languages
        # Colors match ESCO branding - primary blue #0077c8
        status_messages = {
            'pending': {
                'ar': 'تم إرسال طلبك',
                'en': 'Your order has been sent',
                'icon': '📤',
                'color': '#0077c8'  # ESCO Blue - Order received
            },
            'processing': {
                'ar': 'طلبك قيد المعالجة',
                'en': 'Your order is being processed',
                'icon': '⚙️',
                'color': '#ff6b00'  # Orange - Processing
            },
            'confirmed': {
                'ar': 'تم تأكيد طلبك',
                'en': 'Your order has been confirmed',
                'icon': '✅',
                'color': '#28a745'  # Green - Confirmed
            },
            'closed': {
                'ar': 'تم إغلاق طلبك',
                'en': 'Your order has been closed',
                'icon': '🎉',
                'color': '#198754'  # Dark Green - Completed
            },
            'cancelled': {
                'ar': 'تم إلغاء طلبك',
                'en': 'Your order has been cancelled',
                'icon': '❌',
                'color': '#dc3545'
            }
        }

        status_info = status_messages.get(order.status, {
            'ar': 'تم تحديث حالة طلبك',
            'en': 'Your order status has been updated',
            'icon': '📋',
            'color': '#6c757d'
        })

        # Define payment status messages
        payment_messages = {
            'pending': {
                'ar': 'قيد الانتظار',
                'en': 'Pending',
                'color': '#ffc107'  # Yellow - Pending
            },
            'paid': {
                'ar': 'مدفوع',
                'en': 'Paid',
                'color': '#28a745'  # Green - Paid
            },
            'failed': {
                'ar': 'فشل',
                'en': 'Failed',
                'color': '#dc3545'  # Red - Failed
            },
            'refunded': {
                'ar': 'مسترجع',
                'en': 'Refunded',
                'color': '#17a2b8'  # Cyan - Refunded
            }
        }

        payment_info = payment_messages.get(order.payment_status, {
            'ar': 'غير محدد',
            'en': 'Unknown',
            'color': '#6c757d'
        })

        # Prepare context for email template
        context = {
            'order': order,
            'site_url': get_site_url(),
            'year': timezone.now().year,
            'status_info': status_info,
            'payment_info': payment_info,
            'old_status': old_status,
        }

        # Render email template
        html_content = render_to_string('emails/order_status_update.html', context)
        text_content = strip_tags(html_content)

        # Email subject (bilingual)
        subject = f'{status_info["icon"]} {status_info["ar"]} #{order.order_number} | {status_info["en"]} - ESCO'

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )

        # Attach HTML version
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send(fail_silently=False)

        logger.info(f'Order status update email sent successfully for order #{order.order_number} to {order.email}')
        return True

    except Exception as e:
        logger.error(f'Failed to send order status update email for order #{order.order_number}: {str(e)}')
        return False
