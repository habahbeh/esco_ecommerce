import os
import sys
import django

# إعداد Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esco_project.settings')
django.setup()

from products.rag.chat_engine import ProductChatEngine
from products.rag.logger import log_step


def test_chat_engine():
    log_step("🧪 اختبار Chat Engine")

    # إنشاء محرك الدردشة
    chat_engine = ProductChatEngine()

    # اختبارات مختلفة
    test_messages = [
        "أريد لابتوب للألعاب",
        "هاتف رخيص",
        "أفضل جهاز للدراسة",
        "منتج بسعر أقل من 500 دينار"
    ]

    for message in test_messages:
        log_step(f"\n{'=' * 60}")
        log_step(f"👤 العميل: {message}")

        # الحصول على الرد
        response = chat_engine.chat(message)

        log_step(f"🤖 المساعد:\n{response}")
        log_step(f"{'=' * 60}\n")


if __name__ == "__main__":
    test_chat_engine()