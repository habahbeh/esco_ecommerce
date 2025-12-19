# products/rag/searcher.py
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from .config import *
from .logger import log_step, logger
from typing import List, Dict, Any


class ProductSearcher:
    """البحث في المنتجات المفهرسة"""

    def __init__(self):
        log_step("بدء تهيئة ProductSearcher")

        # إعداد ChromaDB
        # self.client = chromadb.Client(
        #     Settings(
        #         anonymized_telemetry=False,
        #         is_persistent=False
        #     )
        # )

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR)
        )

        # الحصول على المجموعة
        try:
            self.collection = self.client.get_collection(COLLECTION_NAME)
            count = self.collection.count()
            log_step(f"✅ تم تحميل المجموعة: {COLLECTION_NAME} ({count} منتج)")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل المجموعة: {str(e)}")
            raise

        # إعداد OpenAI Embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )

    def search_products(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        البحث عن المنتجات الأكثر صلة بالاستعلام
        """
        log_step(f"🔍 البحث عن: '{query}'")

        try:
            # تحويل الاستعلام إلى embedding
            log_step("إنشاء embedding للاستعلام...")
            query_embedding = self.embeddings.embed_query(query)

            # البحث في ChromaDB
            log_step(f"البحث عن أقرب {top_k} منتجات...")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )

            # معالجة النتائج
            products = []

            if results['ids'][0]:  # إذا وجدت نتائج
                log_step(f"✅ تم العثور على {len(results['ids'][0])} منتج")

                for i, product_id in enumerate(results['ids'][0]):
                    # بناء معلومات المنتج
                    product_info = {
                        'id': results['metadatas'][0][i]['product_id'],
                        'name': results['metadatas'][0][i]['name'],
                        'price': results['metadatas'][0][i]['price'],
                        'category': results['metadatas'][0][i]['category'],
                        'brand': results['metadatas'][0][i].get('brand', ''),
                        'in_stock': results['metadatas'][0][i]['in_stock'],
                        'rating': results['metadatas'][0][i].get('rating', 0),
                        'description': results['documents'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],  # تحويل المسافة إلى تشابه
                        'distance': results['distances'][0][i]
                    }

                    products.append(product_info)

                    logger.debug(f"  - {product_info['name']} (تشابه: {product_info['similarity_score']:.2f})")
            else:
                log_step("⚠️ لم يتم العثور على منتجات مطابقة")

            return products

        except Exception as e:
            logger.error(f"❌ خطأ في البحث: {str(e)}")
            return []

    def search_with_filters(self,
                            query: str,
                            category: str = None,
                            min_price: float = None,
                            max_price: float = None,
                            in_stock_only: bool = False,
                            top_k: int = 5) -> List[Dict[str, Any]]:
        """
        البحث مع فلاتر إضافية
        """
        log_step(f"🔍 البحث المتقدم: '{query}'")

        # بناء الفلاتر
        where_filters = {}

        if category:
            where_filters['category'] = category
            log_step(f"  - فلتر الفئة: {category}")

        if min_price is not None and max_price is not None:
            where_filters['price'] = {"$gte": min_price, "$lte": max_price}
            log_step(f"  - فلتر السعر: {min_price} - {max_price}")
        elif min_price is not None:
            where_filters['price'] = {"$gte": min_price}
            log_step(f"  - فلتر السعر الأدنى: {min_price}")
        elif max_price is not None:
            where_filters['price'] = {"$lte": max_price}
            log_step(f"  - فلتر السعر الأقصى: {max_price}")

        if in_stock_only:
            where_filters['in_stock'] = True
            log_step("  - فلتر: المتوفر فقط")

        try:
            # تحويل الاستعلام إلى embedding
            query_embedding = self.embeddings.embed_query(query)

            # البحث مع الفلاتر
            if where_filters:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filters,
                    include=['documents', 'metadatas', 'distances']
                )
            else:
                # بحث بدون فلاتر
                return self.search_products(query, top_k)

            # معالجة النتائج (نفس الكود السابق)
            products = []
            if results['ids'][0]:
                for i, product_id in enumerate(results['ids'][0]):
                    product_info = {
                        'id': results['metadatas'][0][i]['product_id'],
                        'name': results['metadatas'][0][i]['name'],
                        'price': results['metadatas'][0][i]['price'],
                        'category': results['metadatas'][0][i]['category'],
                        'brand': results['metadatas'][0][i].get('brand', ''),
                        'in_stock': results['metadatas'][0][i]['in_stock'],
                        'rating': results['metadatas'][0][i].get('rating', 0),
                        'description': results['documents'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],
                        'distance': results['distances'][0][i]
                    }
                    products.append(product_info)

                log_step(f"✅ تم العثور على {len(products)} منتج مع الفلاتر")
            else:
                log_step("⚠️ لم يتم العثور على منتجات مطابقة للفلاتر")

            return products

        except Exception as e:
            logger.error(f"❌ خطأ في البحث المتقدم: {str(e)}")
            return []

    def get_similar_products(self, product_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        الحصول على منتجات مشابهة لمنتج معين
        """
        log_step(f"🔍 البحث عن منتجات مشابهة للمنتج: {product_id}")

        try:
            # الحصول على embedding المنتج الأصلي
            result = self.collection.get(
                ids=[f"product_{product_id}"],
                include=['embeddings', 'metadatas', 'documents']
            )

            if not result['ids']:
                log_step(f"⚠️ المنتج {product_id} غير موجود في الفهرس")
                return []

            # البحث عن منتجات مشابهة
            product_embedding = result['embeddings'][0]

            # البحث مع استبعاد المنتج نفسه (نحصل على k+1 ثم نحذف الأول)
            results = self.collection.query(
                query_embeddings=[product_embedding],
                n_results=top_k + 1,
                include=['documents', 'metadatas', 'distances']
            )

            # معالجة النتائج مع استبعاد المنتج الأصلي
            products = []
            for i, pid in enumerate(results['ids'][0]):
                if pid != f"product_{product_id}":  # استبعاد المنتج نفسه
                    product_info = {
                        'id': results['metadatas'][0][i]['product_id'],
                        'name': results['metadatas'][0][i]['name'],
                        'price': results['metadatas'][0][i]['price'],
                        'category': results['metadatas'][0][i]['category'],
                        'brand': results['metadatas'][0][i].get('brand', ''),
                        'in_stock': results['metadatas'][0][i]['in_stock'],
                        'rating': results['metadatas'][0][i].get('rating', 0),
                        'description': results['documents'][0][i],
                        'similarity_score': 1 - results['distances'][0][i]
                    }
                    products.append(product_info)

            log_step(f"✅ تم العثور على {len(products)} منتج مشابه")
            return products[:top_k]  # التأكد من إرجاع العدد المطلوب فقط

        except Exception as e:
            logger.error(f"❌ خطأ في البحث عن منتجات مشابهة: {str(e)}")
            return []