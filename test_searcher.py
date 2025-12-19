# test_searcher.py
import os
import sys
import django

# إعداد Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esco_project.settings')
django.setup()

from products.rag.searcher import ProductSearcher
from products.rag.logger import log_step


def test_searcher():
    log_step("🧪 بدء اختبار البحث")

    # إنشاء باحث
    searcher = ProductSearcher()

    # اختبارات البحث
    test_queries = [
        "لابتوب",
        "هاتف آيفون",
        "جهاز رخيص",
        "test"  # المنتج الذي فهرسناه
    ]

    for query in test_queries:
        log_step(f"\n{'=' * 50}")
        log_step(f"📍 اختبار البحث عن: '{query}'")

        # بحث عادي
        results = searcher.search_products(query, top_k=3)

        print("\n🔍 البيانات الخام:")
        for r in results:
            print(f"--- {r['name']} ---")
            print(r['description'])
            print("-" * 50)

        if results:
            log_step(f"✅ تم العثور على {len(results)} نتيجة:")
            for i, product in enumerate(results, 1):
                log_step(f"""
                {i}. {product['name']}
                   - السعر: {product['price']} د.أ
                   - الفئة: {product['category']}
                   - التشابه: {product['similarity_score']:.2%}
                   - متوفر: {'نعم' if product['in_stock'] else 'لا'}
                """)
        else:
            log_step("❌ لم يتم العثور على نتائج")

    # اختبار البحث مع الفلاتر
    log_step(f"\n{'=' * 50}")
    log_step("📍 اختبار البحث مع الفلاتر")

    filtered_results = searcher.search_with_filters(
        query="منتج",
        max_price=500,
        in_stock_only=True,
        top_k=3
    )

    if filtered_results:
        log_step(f"✅ نتائج مع الفلاتر: {len(filtered_results)} منتج")
    else:
        log_step("❌ لا توجد نتائج مطابقة للفلاتر")


if __name__ == "__main__":
    test_searcher()