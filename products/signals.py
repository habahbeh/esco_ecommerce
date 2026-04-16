# products/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product
from .rag.indexer import ProductIndexer
from .rag.logger import log_step

PRICE_ONLY_FIELDS = {
    'base_price', 'compare_price', 'cost',
    'discount_percentage', 'discount_amount',
    'discount_start', 'discount_end',
    'updated_at',
}


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