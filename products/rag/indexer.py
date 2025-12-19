# products/rag/indexer.py
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from products.models import Product
from .config import *
from .logger import log_step, logger
import json


class ProductIndexer:
    """فهرسة المنتجات في ChromaDB"""

    def __init__(self):
        log_step("بدء تهيئة ProductIndexer")

        # إعداد ChromaDB
        self.client = chromadb.Client(
            Settings(
                anonymized_telemetry=False,
                is_persistent=False
            )
        )

        # server centos
        # self.client = chromadb.PersistentClient(
        #     path="/var/www/esco_ecommerce/products/rag/chroma_db"
        # )

        # إنشاء أو الحصول على المجموعة
        try:
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                embedding_function=None  # سنستخدم OpenAI
            )
            log_step(f"✅ تم إنشاء مجموعة جديدة: {COLLECTION_NAME}")
        except:
            self.collection = self.client.get_collection(COLLECTION_NAME)
            log_step(f"📌 استخدام مجموعة موجودة: {COLLECTION_NAME}")

        # إعداد OpenAI Embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )

    def product_to_text(self, product):
        """تحويل المنتج إلى نص وصفي شامل"""
        log_step(f"تحويل المنتج: {product.name}")

        # بناء نص شامل عن المنتج
        text_parts = [
            f"اسم المنتج: {product.name}",
            f"الفئة: {product.category.name}",
            f"السعر: {product.base_price} دينار",
        ]

        # إضافة العلامة التجارية
        if product.brand:
            text_parts.append(f"العلامة التجارية: {product.brand.name}")

        # إضافة الوصف
        if product.description:
            text_parts.append(f"الوصف: {product.description}")

        # إضافة المواصفات
        if product.specifications:
            specs_text = "المواصفات: "
            for key, value in product.specifications.items():
                specs_text += f"{key}: {value}, "
            text_parts.append(specs_text)

        # إضافة الحالة
        if product.stock_quantity > 0:
            text_parts.append("الحالة: متوفر في المخزون")
        else:
            text_parts.append("الحالة: غير متوفر حالياً")

        # إضافة معلومات إضافية
        if product.is_featured:
            text_parts.append("منتج مميز")
        if product.is_new:
            text_parts.append("منتج جديد")
        if product.has_discount:
            text_parts.append(f"يوجد خصم {product.discount_percentage}%")

        final_text = "\n".join(text_parts)
        logger.debug(f"النص النهائي: {final_text[:200]}...")

        return final_text

    def product_to_metadata(self, product):
        """إنشاء metadata للمنتج"""
        return {
            "product_id": str(product.id),
            "name": product.name,
            "price": float(product.base_price),
            "category": product.category.name,
            "brand": product.brand.name if product.brand else "",
            "in_stock": product.stock_quantity > 0,
            "is_featured": product.is_featured,
            "rating": float(product.rating) if product.rating else 0.0
        }

    def index_single_product(self, product):
        """فهرسة منتج واحد"""
        try:
            log_step(f"بدء فهرسة: {product.name}")

            # احذف النسخة القديمة أولاً
            product_id = f"product_{product.id}"
            try:
                self.collection.delete(ids=[product_id])
                log_step(f"🗑️ حذف النسخة القديمة")
            except:
                pass  # لا مشكلة إذا لم توجد

            # أضف النسخة الجديدة
            text = self.product_to_text(product)
            metadata = self.product_to_metadata(product)
            embedding = self.embeddings.embed_query(text)

            self.collection.add(
                ids=[product_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )

            log_step(f"✅ تمت فهرسة: {product.name}")
            return True

        except Exception as e:
            logger.error(f"❌ خطأ في فهرسة {product.name}: {str(e)}")
            return False

    def index_all_products(self, batch_size=10):
        """فهرسة جميع المنتجات النشطة"""
        log_step("بدء فهرسة جميع المنتجات")

        # الحصول على المنتجات النشطة
        products = Product.objects.filter(
            is_active=True,
            status='published'
        ).select_related('category', 'brand')

        total = products.count()
        log_step(f"عدد المنتجات للفهرسة: {total}")

        success_count = 0
        error_count = 0

        # فهرسة على دفعات
        for i in range(0, total, batch_size):
            batch = products[i:i + batch_size]
            log_step(f"معالجة الدفعة {i // batch_size + 1}")

            for product in batch:
                if self.index_single_product(product):
                    success_count += 1
                else:
                    error_count += 1

        log_step(f"""
        ✅ انتهت الفهرسة:
        - نجح: {success_count}
        - فشل: {error_count}
        - الإجمالي: {total}
        """)

        return success_count, error_count

    def delete_product(self, product_id):
        """حذف منتج من الفهرس"""
        try:
            self.collection.delete(ids=[f"product_{product_id}"])
            log_step(f"✅ تم حذف المنتج: {product_id}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حذف المنتج {product_id}: {str(e)}")
            return False

    def get_collection_info(self):
        """معلومات عن المجموعة المفهرسة"""
        count = self.collection.count()
        log_step(f"📊 عدد المنتجات المفهرسة: {count}")
        return {
            "count": count,
            "collection_name": COLLECTION_NAME
        }