# products/rag/chat_engine.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from .searcher import ProductSearcher
from .config import OPENAI_API_KEY
from .logger import log_step, logger
from typing import List, Dict, Any


class ProductChatEngine:
    """محرك الدردشة الذكي للمنتجات مع دعم الذاكرة"""

    def __init__(self):
        log_step("بدء تهيئة ProductChatEngine")

        # إعداد نموذج GPT-4
        self.llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4o-mini",  # أرخص وأسرع
            temperature=0.7,
            max_tokens=500
        )

        # إعداد الباحث
        self.searcher = ProductSearcher()

        # ⭐ ذاكرة المحادثات
        self.sessions = {}  # {phone_number: [messages]}

        # قالب النظام
        self.system_prompt = """أنت مساعد مبيعات ذكي في متجر إلكتروني.

        القواعد المهمة جداً:
        1. اذكر فقط المنتجات الموجودة في نتائج البحث المعطاة لك
        2. ممنوع منعاً باتاً ذكر أي منتج غير موجود في القائمة
        3. إذا سأل عن "كل المنتجات"، اعرض ما لديك فقط (لا تخترع)
        4. لا تتحدث عن منتجات "نفذت" أو "غير متوفرة" إلا إذا كانت في النتائج
        5. اذكر السعر والفئة كما هي بالضبط
        6. كن مختصراً ومباشراً
        7. استخدم رموز تعبيرية
        8. اكتب بالعربية
        9. تذكر المحادثات السابقة واستخدمها في السياق

        تذكر: لديك قائمة محددة من المنتجات - التزم بها فقط!"""

        # قالب تنسيق المنتجات
        self.product_template = """
🔍 بناءً على طلبك، وجدت لك هذه المنتجات:

{products_list}

💡 نصيحة: {advice}

هل تريد معلومات إضافية عن أي منتج؟"""

    def get_or_create_session(self, session_id: str) -> List[Dict]:
        """الحصول على جلسة أو إنشاء واحدة جديدة"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def _format_history(self, history: List[Dict]) -> str:
        """تنسيق تاريخ المحادثة"""
        if not history:
            return "لا توجد محادثة سابقة"

        formatted = []
        for msg in history:
            role = "العميل" if msg['role'] == 'user' else "المساعد"
            formatted.append(f"{role}: {msg['content']}")

        return "\n".join(formatted)

    def format_product(self, product: Dict[str, Any], rank: int) -> str:
        """تنسيق منتج واحد"""
        in_stock = "✅ متوفر" if product['in_stock'] else "❌ نفذ المخزون"

        # استخرج الوصف من البيانات المفهرسة
        description_text = product.get('description', '')

        # استخرج الوصف الفعلي من النص المفهرس
        lines = description_text.split('\n')
        actual_description = ""

        for line in lines:
            if line.startswith('الوصف:'):
                actual_description = line.replace('الوصف:', '').strip()
                break

        return f"""
    {rank}. 📦 {product['name']}
       💰 السعر: {product['price']:.2f} د.أ
       🏷️ الفئة: {product['category']}
       {in_stock}

       📝 **الوصف**: {actual_description if actual_description else 'لا يوجد وصف'}
       """

    def chat(self, user_message: str, session_id: str = None) -> str:
        """معالجة رسالة المستخدم وإرجاع رد مع دعم الذاكرة"""
        try:
            log_step(f"💬 رسالة المستخدم: {user_message}")
            if session_id:
                log_step(f"📱 Session ID: {session_id}")

            # احصل على تاريخ المحادثة
            session_history = []
            if session_id:
                session_history = self.get_or_create_session(session_id)

            # 1. البحث عن المنتجات
            log_step("🔍 البحث عن منتجات مناسبة...")
            products = self.searcher.search_products(
                query=user_message,
                top_k=5
            )

            if not products:
                log_step("⚠️ لم يتم العثور على منتجات")
                response = self.no_products_response(user_message, session_history)
            else:
                # 2. تنسيق المنتجات
                products_formatted = []
                for i, product in enumerate(products, 1):
                    products_formatted.append(
                        self.format_product(product, i)
                    )

                products_list = "\n".join(products_formatted)

                # 3. إنشاء السياق مع المحادثة السابقة
                context = f"""
                المحادثة السابقة:
                {self._format_history(session_history[-5:])}  # آخر 5 رسائل

                سأل العميل الآن: {user_message}

                المنتجات المتاحة (هذه فقط - لا تضف غيرها):
                {products_list}

                مهمتك: اكتب رداً مع مراعاة السياق السابق. إذا سأل العميل عن "ما سعره" أو "أعطني كل المنتجات" 
                فيجب أن تفهم من السياق ما يقصده."""

                # 4. توليد الرد عبر GPT-4
                log_step("🤖 توليد الرد عبر GPT-4...")
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=context)
                ]

                response = self.llm.invoke(messages)
                response = response.content

            # 5. احفظ في الذاكرة
            if session_id:
                session_history.append({
                    'role': 'user',
                    'content': user_message
                })
                session_history.append({
                    'role': 'assistant',
                    'content': response
                })

                # احتفظ بآخر 10 رسائل فقط
                if len(session_history) > 10:
                    self.sessions[session_id] = session_history[-10:]

                log_step(f"💾 تم حفظ المحادثة - عدد الرسائل: {len(session_history)}")

            log_step("✅ تم توليد الرد بنجاح")
            return response

        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الرسالة: {str(e)}")
            return "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى."

    def no_products_response(self, user_message: str, session_history: List[Dict] = None) -> str:
        """رد عند عدم وجود منتجات مع مراعاة السياق"""
        context = f"""
        المحادثة السابقة:
        {self._format_history(session_history[-5:]) if session_history else 'لا توجد محادثة سابقة'}

        العميل سأل: {user_message}

        للأسف لم أجد منتجات مطابقة تماماً لطلبك.
        اكتب رداً مفيداً مع اقتراحات بديلة."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=context)
        ]

        response = self.llm.invoke(messages)
        return response.content

    def chat_with_filters(self,
                          user_message: str,
                          session_id: str = None,
                          category: str = None,
                          max_price: float = None,
                          in_stock_only: bool = True) -> str:
        """دردشة مع فلاتر إضافية ودعم الذاكرة"""
        try:
            log_step(f"💬 رسالة مع فلاتر: {user_message}")

            # احصل على تاريخ المحادثة
            session_history = []
            if session_id:
                session_history = self.get_or_create_session(session_id)

            # البحث مع الفلاتر
            products = self.searcher.search_with_filters(
                query=user_message,
                category=category,
                max_price=max_price,
                in_stock_only=in_stock_only,
                top_k=5
            )

            if not products:
                return self.no_products_response(user_message, session_history)

            # تنسيق المنتجات
            products_formatted = []
            for i, product in enumerate(products, 1):
                products_formatted.append(
                    self.format_product(product, i)
                )

            products_list = "\n".join(products_formatted)

            # إنشاء السياق
            context = f"""
            المحادثة السابقة:
            {self._format_history(session_history[-5:])}

            سأل العميل: {user_message}

            الفلاتر المطبقة:
            - الفئة: {category or 'الكل'}
            - السعر الأقصى: {max_price or 'غير محدد'}
            - المتوفر فقط: {'نعم' if in_stock_only else 'لا'}

            المنتجات المتاحة:
            {products_list}"""

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=context)
            ]

            response = self.llm.invoke(messages)
            final_response = response.content

            # احفظ في الذاكرة
            if session_id:
                session_history.append({
                    'role': 'user',
                    'content': user_message
                })
                session_history.append({
                    'role': 'assistant',
                    'content': final_response
                })

                if len(session_history) > 10:
                    self.sessions[session_id] = session_history[-10:]

            return final_response

        except Exception as e:
            logger.error(f"❌ خطأ: {str(e)}")
            return "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى."

    def clear_session(self, session_id: str):
        """مسح ذاكرة جلسة معينة"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            log_step(f"🗑️ تم مسح ذاكرة الجلسة: {session_id}")

    def get_session_info(self):
        """الحصول على معلومات الجلسات النشطة"""
        info = {
            'active_sessions': len(self.sessions),
            'sessions': {}
        }

        for session_id, history in self.sessions.items():
            info['sessions'][session_id] = {
                'message_count': len(history),
                'last_message': history[-1]['content'][:50] + '...' if history else None
            }

        return info