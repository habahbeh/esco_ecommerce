# products/rag/config.py
import os
from pathlib import Path

# إعدادات OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # ضع مفتاحك في متغير البيئة

# إعدادات ChromaDB
CHROMA_PERSIST_DIR = Path(__file__).parent / "chroma_db"

# للسيرفر
# CHROMA_PERSIST_DIR = Path("/var/www/esco_ecommerce/products/rag/chroma_db")

COLLECTION_NAME = "products"

# إعدادات RAG
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_SEARCH_RESULTS = 5

# رسائل تتبع الأخطاء
DEBUG_MODE = True  # لتتبع العملية