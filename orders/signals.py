# orders/signals.py
"""
إشارات تطبيق الطلبات
تستخدم لتحديث المخزون وإرسال الإشعارات عند تغيير حالة الطلب
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Order, OrderItem


@receiver(post_save, sender=Order)
def update_inventory_on_order_status_change(sender, instance, **kwargs):
    """
    تحديث المخزون عند تغيير حالة الطلب
    Update inventory when order status changes
    """
    # تحديث المخزون فقط عند اكتمال الطلب أو إلغائه
    if instance.status == 'delivered' and instance.tracker.has_changed('status') and instance.tracker.previous(
            'status') != 'delivered':
        # الطلب اكتمل، قم بتخفيض المخزون
        with transaction.atomic():
            for item in instance.items.all():
                try:
                    from products.models import Product, ProductVariant
                    # تحديث المخزون استناداً إلى المنتج أو المتغير
                    if item.variant_id:
                        variant = ProductVariant.objects.get(id=item.variant_id)
                        if variant.track_inventory:
                            variant.stock_quantity = max(0, variant.stock_quantity - item.quantity)
                            variant.save(update_fields=['stock_quantity'])
                    else:
                        product = Product.objects.get(id=item.product_id)
                        if product.track_inventory:
                            product.stock_quantity = max(0, product.stock_quantity - item.quantity)
                            product.sales_count = product.sales_count + item.quantity
                            product.save(update_fields=['stock_quantity', 'sales_count'])
                except Exception as e:
                    # تسجيل الخطأ في التحديث
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error updating inventory for order {instance.id}: {e}")

    elif instance.status == 'cancelled' and instance.tracker.has_changed('status') and instance.tracker.previous(
            'status') not in ['cancelled', 'refunded']:
        # الطلب ألغي، أعد المخزون
        with transaction.atomic():
            for item in instance.items.all():
                try:
                    from products.models import Product, ProductVariant
                    # إعادة المخزون استناداً إلى المنتج أو المتغير
                    if item.variant_id:
                        variant = ProductVariant.objects.get(id=item.variant_id)
                        if variant.track_inventory:
                            variant.stock_quantity = variant.stock_quantity + item.quantity
                            variant.save(update_fields=['stock_quantity'])
                    else:
                        product = Product.objects.get(id=item.product_id)
                        if product.track_inventory:
                            product.stock_quantity = product.stock_quantity + item.quantity
                            product.sales_count = max(0, product.sales_count - item.quantity)
                            product.save(update_fields=['stock_quantity', 'sales_count'])
                except Exception as e:
                    # تسجيل الخطأ في التحديث
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error restoring inventory for cancelled order {instance.id}: {e}")


@receiver(post_save, sender=Order)
def notify_user_on_order_status_change(sender, instance, **kwargs):
    """
    إرسال إشعار للمستخدم عند تغيير حالة الطلب
    Notify user when order status changes
    """
    if instance.tracker.has_changed('status') and instance.user:
        status_text = dict(Order.STATUS_CHOICES).get(instance.status, instance.status)

        # إنشاء نشاط جديد للمستخدم
        from accounts.models import UserActivity
        UserActivity.objects.create(
            user=instance.user,
            activity_type='order_status_change',
            description=f'تم تغيير حالة الطلب {instance.order_number} إلى {status_text}',
            object_id=instance.id,
            content_type='order'
        )

        # يمكن إضافة إرسال إشعار بالبريد الإلكتروني هنا