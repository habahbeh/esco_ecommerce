import os
import sys
import django

# إعداد Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esco_project.settings')
django.setup()

from products.rag.indexer import ProductIndexer
from products.rag.logger import log_step
from products.models import Product


def index_real_products():
    """فهرسة جميع المنتجات النشطة"""

    log_step("🚀 بدء فهرسة المنتجات الحقيقية")

    # 1. عرض عدد المنتجات المتاحة
    total_products = Product.objects.filter(
        is_active=True,
        status='published'
    ).count()

    log_step(f"📊 عدد المنتجات الجاهزة للفهرسة: {total_products}")

    if total_products == 0:
        log_step("❌ لا توجد منتجات منشورة ونشطة!")
        return

    # 2. إنشاء المفهرس
    indexer = ProductIndexer()

    # 3. حذف المنتج التجريبي "test" إن وجد
    try:
        indexer.collection.delete(ids=["product_1"])
        log_step("🗑️ تم حذف المنتج التجريبي")
    except:
        pass

    # 4. فهرسة المنتجات الحقيقية
    success_count, error_count = indexer.index_all_products(batch_size=10)

    # 5. عرض النتائج
    log_step(f"""
    ✅ اكتملت الفهرسة:
    ===========================
    ✓ نجح: {success_count} منتج
    ✗ فشل: {error_count} منتج
    📦 الإجمالي في الفهرس: {indexer.get_collection_info()['count']}
    ===========================
    """)


if __name__ == "__main__":
    index_real_products()