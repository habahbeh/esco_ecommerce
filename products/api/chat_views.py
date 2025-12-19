# products/api/chat_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from products.rag.logger import log_step, logger


# لا تستورد ProductChatEngine هنا!
from products.rag.logger import log_step, logger

chat_engine_instance = None

def get_global_chat_engine():
    """الحصول على instance واحد عالمي"""
    global chat_engine_instance
    if not chat_engine_instance:
        try:
            from products.rag.chat_engine import ProductChatEngine
            chat_engine_instance = ProductChatEngine()
            log_step("✅ تم إنشاء Chat Engine عالمي")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل Chat Engine: {e}")
            return None
    return chat_engine_instance


@method_decorator(csrf_exempt, name='dispatch')
class ProductChatView(APIView):
    """API endpoint للدردشة مع المنتجات"""

    def post(self, request):
        """معالجة رسائل الدردشة"""
        try:
            # استخراج الرسالة
            data = request.data
            message = data.get('message', '').strip()

            # التحقق من وجود رسالة
            if not message:
                return Response({
                    'error': 'الرسالة مطلوبة',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)

            log_step(f"📨 API استقبل: {message}")

            # احصل على session_id من Django session
            log_step("🔑 إنشاء/الحصول على session...")
            if not request.session.session_key:
                request.session.save()
            session_id = f"web_{request.session.session_key}"
            log_step(f"📱 Session ID: {session_id[:20]}...")

            # تحميل Chat Engine
            log_step("🔧 جاري تحميل Chat Engine...")
            chat_engine = get_global_chat_engine()

            # تحقق من وجود chat_engine
            if not chat_engine:
                log_step("❌ فشل تحميل Chat Engine")
                return Response({
                    'status': 'error',
                    'message': 'النظام تحت الصيانة. يرجى المحاولة بعد قليل.',
                    'query': message
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            log_step("✅ Chat Engine جاهز")
            log_step("🤖 بدء معالجة الرسالة...")

            # معالجة الرسالة مع session_id
            response_text = chat_engine.chat(message, session_id=session_id)

            log_step("✅ تمت المعالجة بنجاح")
            log_step(f"📤 الرد: {response_text[:50]}...")

            # إرجاع الرد
            return Response({
                'status': 'success',
                'message': response_text,
                'query': message
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ خطأ في API: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")

            return Response({
                'error': 'حدث خطأ في معالجة طلبك',
                'details': str(e),
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """معلومات عن API"""
        return Response({
            'status': 'active',
            'endpoint': '/api/products/chat/',
            'method': 'POST',
            'required_fields': {
                'message': 'نص السؤال'
            },
            'example': {
                'message': 'أريد لابتوب للألعاب'
            }
        })


# Webhook لـ n8n (بدون CSRF)
@method_decorator(csrf_exempt, name='dispatch')
class ProductWebhookView(APIView):
    """Webhook endpoint لـ n8n"""

    def post(self, request):
        """معالجة webhook من n8n"""
        try:
            # دعم أنواع مختلفة من البيانات
            if request.content_type == 'application/json':
                data = request.data
            else:
                data = json.loads(request.body)

            # استخراج الرسالة (دعم تنسيقات مختلفة)
            message = (
                    data.get('message') or
                    data.get('text') or
                    data.get('query') or
                    data.get('Body') or  # Twilio/WhatsApp
                    ''
            ).strip()

            # ⭐ استخراج رقم الهاتف
            phone_number = data.get('phone_number', '')

            if not message:
                return Response({
                    'reply': 'مرحباً! كيف يمكنني مساعدتك في إيجاد المنتج المناسب؟'
                })

            # ⭐ استخدم الدالة العالمية
            chat_engine = get_global_chat_engine()

            # تحقق من وجود chat_engine
            if not chat_engine:
                return Response({
                    'reply': 'النظام تحت الصيانة. يرجى المحاولة بعد قليل.',
                    'status': 'maintenance'
                })

            # ⭐ أضف session_id
            response_text = chat_engine.chat(message, session_id=phone_number)

            # تنسيق مناسب لـ n8n
            return Response({
                'reply': response_text,
                'status': 'success'
            })

        except Exception as e:
            logger.error(f"❌ خطأ في Webhook: {str(e)}")
            return Response({
                'reply': 'عذراً، حدث خطأ. يرجى المحاولة لاحقاً.',
                'status': 'error'
            })