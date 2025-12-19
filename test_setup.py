# test_setup.py
from products.rag.config import *
from products.rag.logger import log_step


def test_setup():
    log_step("بدء اختبار الإعداد")

    # تحقق من OpenAI
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-key-here":
        log_step("❌ خطأ: لم تضع مفتاح OpenAI")
        return False

    # تحقق من المجلدات
    CHROMA_PERSIST_DIR.mkdir(exist_ok=True)
    log_step("✅ تم إنشاء مجلد ChromaDB")

    # تحقق من الاستيراد
    try:
        import chromadb
        import langchain
        log_step("✅ المكتبات مثبتة بنجاح")
    except ImportError as e:
        log_step(f"❌ خطأ في المكتبات: {e}")
        return False

    log_step("✅ الإعداد جاهز!")
    return True


if __name__ == "__main__":
    test_setup()