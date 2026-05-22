# products/signals.py
import logging
from decimal import Decimal, InvalidOperation
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import Product
from .rag.indexer import ProductIndexer
from .rag.logger import log_step

logger = logging.getLogger(__name__)

PRICE_ONLY_FIELDS = {
    'base_price', 'compare_price', 'cost',
    'discount_percentage', 'discount_amount',
    'discount_start', 'discount_end',
    'updated_at',
}

TRACKED_FIELDS = {
    'base_price': ('price_changed', 'السعر'),
    'compare_price': ('price_changed', 'سعر المقارنة'),
    'cost': ('price_changed', 'التكلفة'),
    'stock_quantity': ('stock_changed', 'الكمية'),
    'stock_status': ('stock_changed', 'حالة المخزون'),
    'status': ('status_changed', 'الحالة'),
    'is_active': ('status_changed', 'نشط'),
    'discount_percentage': ('price_changed', 'نسبة الخصم'),
    'discount_amount': ('price_changed', 'مبلغ الخصم'),
}

DECIMAL_FIELDS = {'base_price', 'compare_price', 'cost', 'discount_percentage', 'discount_amount'}


def _values_equal(field, old_val, new_val):
    if field in DECIMAL_FIELDS:
        try:
            return Decimal(str(old_val or 0)) == Decimal(str(new_val or 0))
        except (InvalidOperation, TypeError, ValueError):
            pass
    return old_val == new_val


@receiver(pre_save, sender=Product)
def track_product_changes(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Product.objects.only(*TRACKED_FIELDS.keys()).get(pk=instance.pk)
    except Product.DoesNotExist:
        return

    from dashboard.models import ProductActivityLog
    logs = []
    for field, (action, label) in TRACKED_FIELDS.items():
        old_val = getattr(old, field, None)
        new_val = getattr(instance, field, None)
        if _values_equal(field, old_val, new_val):
            continue
        logs.append(ProductActivityLog(
            product=instance,
            action=action,
            field_name=label,
            old_value=str(old_val or '')[:255],
            new_value=str(new_val or '')[:255],
        ))
    if logs:
        ProductActivityLog.objects.bulk_create(logs)


@receiver(post_save, sender=Product)
def log_product_creation(sender, instance, created, **kwargs):
    if created:
        from dashboard.models import ProductActivityLog
        ProductActivityLog.objects.create(
            product=instance,
            action='created',
            field_name='',
            new_value=str(instance.name)[:255],
        )


@receiver(post_save, sender=Product)
def update_product_in_vector_db(sender, instance, created, **kwargs):
    """تحديث المنتج في ChromaDB عند الحفظ"""
    update_fields = kwargs.get('update_fields')
    if update_fields and set(update_fields).issubset(PRICE_ONLY_FIELDS):
        return

    if instance.is_active and instance.status == 'published':
        try:
            indexer = ProductIndexer()
            indexer.index_single_product(instance)
            log_step(f"✅ تم تحديث: {instance.name}")
        except Exception as e:
            log_step(f"❌ فشل تحديث: {instance.name} - {e}")

@receiver(post_delete, sender=Product)
def delete_product_from_vector_db(sender, instance, **kwargs):
    """حذف المنتج من ChromaDB عند الحذف"""
    try:
        indexer = ProductIndexer()
        indexer.delete_product(instance.id)
        log_step(f"🗑️ تم حذف: {instance.name}")
    except Exception as e:
        log_step(f"❌ فشل حذف: {instance.name} - {e}")


@receiver(post_save, sender=Product)
def update_product_in_meilisearch(sender, instance, created, **kwargs):
    try:
        from .search.client import is_available
        if not is_available():
            return
        from .search.indexer import MeilisearchIndexer
        ms_indexer = MeilisearchIndexer()
        if instance.is_active and instance.status == 'published':
            ms_indexer.index_product(instance)
        else:
            ms_indexer.delete_product(instance.id)
    except Exception as e:
        logger.warning(f"Meilisearch sync failed for product {instance.id}: {e}")


@receiver(post_delete, sender=Product)
def delete_product_from_meilisearch(sender, instance, **kwargs):
    try:
        from .search.client import is_available
        if not is_available():
            return
        from .search.indexer import MeilisearchIndexer
        ms_indexer = MeilisearchIndexer()
        ms_indexer.delete_product(instance.id)
    except Exception as e:
        logger.warning(f"Meilisearch delete failed for product {instance.id}: {e}")