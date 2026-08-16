# products/signals.py
import logging
import threading
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


def _sync_vector_db(product_id, product_name, is_active, status):
    """Run ChromaDB/OpenAI embedding sync in background."""
    try:
        indexer = ProductIndexer()
        product = Product.objects.get(pk=product_id)
        indexer.index_single_product(product)
        log_step(f"✅ تم تحديث: {product_name}")
    except Exception as e:
        log_step(f"❌ فشل تحديث: {product_name} - {e}")
    finally:
        from django import db
        db.connection.close()


@receiver(post_save, sender=Product)
def update_product_in_vector_db(sender, instance, created, **kwargs):
    """تحديث المنتج في ChromaDB عند الحفظ (background thread)"""
    update_fields = kwargs.get('update_fields')
    if update_fields and set(update_fields).issubset(PRICE_ONLY_FIELDS):
        return

    if instance.is_active and instance.status == 'published':
        t = threading.Thread(
            target=_sync_vector_db,
            args=(instance.pk, instance.name, instance.is_active, instance.status),
            daemon=True,
        )
        t.start()


@receiver(post_delete, sender=Product)
def delete_product_from_vector_db(sender, instance, **kwargs):
    """حذف المنتج من ChromaDB عند الحذف"""
    def _delete(product_id, product_name):
        try:
            indexer = ProductIndexer()
            indexer.delete_product(product_id)
            log_step(f"🗑️ تم حذف: {product_name}")
        except Exception as e:
            log_step(f"❌ فشل حذف: {product_name} - {e}")

    t = threading.Thread(target=_delete, args=(instance.id, instance.name), daemon=True)
    t.start()


def _sync_meilisearch(product_id, is_active, status):
    """Run Meilisearch sync in background."""
    try:
        from .search.client import is_available
        if not is_available():
            return
        from .search.indexer import MeilisearchIndexer
        ms_indexer = MeilisearchIndexer()
        product = Product.objects.get(pk=product_id)
        if is_active and status == 'published':
            ms_indexer.index_product(product)
        else:
            ms_indexer.delete_product(product_id)
    except Exception as e:
        logger.warning(f"Meilisearch sync failed for product {product_id}: {e}")
    finally:
        from django import db
        db.connection.close()


@receiver(post_save, sender=Product)
def update_product_in_meilisearch(sender, instance, created, **kwargs):
    t = threading.Thread(
        target=_sync_meilisearch,
        args=(instance.pk, instance.is_active, instance.status),
        daemon=True,
    )
    t.start()


@receiver(post_delete, sender=Product)
def delete_product_from_meilisearch(sender, instance, **kwargs):
    def _delete(product_id):
        try:
            from .search.client import is_available
            if not is_available():
                return
            from .search.indexer import MeilisearchIndexer
            ms_indexer = MeilisearchIndexer()
            ms_indexer.delete_product(product_id)
        except Exception as e:
            logger.warning(f"Meilisearch delete failed for product {product_id}: {e}")

    t = threading.Thread(target=_delete, args=(instance.id,), daemon=True)
    t.start()