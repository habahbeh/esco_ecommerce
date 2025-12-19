# test_indexer.py
import os
import sys
import django

# إعداد Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esco_project.settings')
django.setup()

from products.rag.indexer import ProductIndexer
from products.rag.logger import log_step


def test_indexer():
    log_step("🧪 بدء اختبار الفهرسة")

    # إنشاء مفهرس
    indexer = ProductIndexer()

    # معلومات المجموعة
    info = indexer.get_collection_info()
    log_step(f"معلومات المجموعة: {info}")

    # فهرسة منتج واحد للاختبار
    from products.models import Product
    test_product = Product.objects.filter(
        is_active=True,
        status='published'
    ).first()

    if test_product:
        log_step(f"اختبار فهرسة: {test_product.name}")
        success = indexer.index_single_product(test_product)

        if success:
            log_step("✅ نجح اختبار الفهرسة")
            # معلومات محدثة
            info = indexer.get_collection_info()
            log_step(f"المجموعة بعد الإضافة: {info}")
        else:
            log_step("❌ فشل اختبار الفهرسة")
    else:
        log_step("⚠️ لا توجد منتجات للاختبار")


if __name__ == "__main__":
    test_indexer()