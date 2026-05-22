import json
import logging
import time
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from django.utils.translation import get_language
from django.core.cache import cache

from .models import ChatbotSettings, Conversation, Message, LeadRequest
from .providers.registry import get_provider
from .context_builder import build_messages, parse_response
from . import knowledge

logger = logging.getLogger(__name__)


class ChatbotConfigView(View):
    def get(self, request):
        settings = ChatbotSettings.get_settings()
        if not settings.is_enabled:
            return JsonResponse({'enabled': False})

        lang = get_language() or 'ar'
        if lang not in ('ar', 'en'):
            lang = 'ar'

        suggested = knowledge.get_suggested_questions(lang)

        config = {
            'enabled': True,
            'bot_name': settings.bot_name_ar if lang == 'ar' else settings.bot_name_en,
            'welcome_message': settings.welcome_message_ar if lang == 'ar' else settings.welcome_message_en,
            'avatar_url': settings.avatar.url if settings.avatar else '',
            'avatar_icon': settings.avatar_icon or 'fas fa-robot',
            'avatar_icon_color': settings.avatar_icon_color or '#ffffff',
            'primary_color': settings.primary_color,
            'secondary_color': settings.secondary_color,
            'position': settings.position,
            'bubble_size': settings.bubble_size,
            'bubble_icon': settings.bubble_icon or 'fas fa-comments',
            'bubble_icon_color': settings.bubble_icon_color or '#ffffff',
            'bubble_bg_color': settings.bubble_bg_color or settings.primary_color,
            'show_on_mobile': settings.show_on_mobile,
            'language': lang,
            'direction': 'rtl' if lang == 'ar' else 'ltr',
            'enable_comparison': settings.enable_comparison,
            'enable_suggestions': settings.enable_suggestions,
            'suggested_questions': suggested,
            'csrf_token': get_token(request),
            'voice_input_enabled': settings.enable_voice_input,
            'voice_output_enabled': settings.enable_voice_output,
            'voice_provider': settings.voice_provider,
            'voice_language': settings.voice_language,
            'auto_play_voice': settings.auto_play_voice,
        }

        if settings.enable_voice_agent:
            from .voice_agent_providers.registry import get_voice_agent_provider
            agent_provider = get_voice_agent_provider(settings)
            agent_config = {
                'enabled': True,
                'provider': settings.voice_agent_provider,
                'trigger': settings.voice_agent_trigger,
                'button_color': settings.voice_agent_button_color,
                'button_icon': settings.voice_agent_button_icon,
                'button_position': settings.voice_agent_button_position,
                'label': settings.voice_agent_label_ar if lang == 'ar' else settings.voice_agent_label_en,
            }
            if agent_provider:
                agent_config['sdk_url'] = agent_provider.get_sdk_url()
                # Never expose raw API keys — strip them from init_config
                init_cfg = agent_provider.get_init_config()
                init_cfg.pop('apiKey', None)
                agent_config['init_config'] = init_cfg
                agent_config['embed_script'] = agent_provider.get_embed_script()
                agent_config['start_call_url'] = '/api/chatbot/voice-agent/start/'
            config['voice_agent'] = agent_config
        else:
            config['voice_agent'] = {'enabled': False}

        return JsonResponse(config)


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotMessageView(View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        if not settings.is_enabled:
            return JsonResponse({'error': 'Chatbot is disabled'}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        user_message = body.get('message', '').strip()
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)
        if len(user_message) > 2000:
            return JsonResponse({'error': 'Message too long'}, status=400)

        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        if not self._check_rate_limit(session_key, settings):
            lang = get_language() or 'ar'
            msg = 'عذراً، أنت ترسل رسائل بسرعة كبيرة. انتظر قليلاً.' if lang == 'ar' else 'Too many messages. Please wait a moment.'
            return JsonResponse({'error': msg}, status=429)

        conversation = self._get_or_create_conversation(request, session_key, body)
        msg_count = conversation.messages.count()
        if msg_count >= settings.max_messages_per_session:
            lang = get_language() or 'ar'
            msg = 'وصلت للحد الأقصى من الرسائل. ابدأ محادثة جديدة.' if lang == 'ar' else 'Maximum messages reached. Start a new conversation.'
            return JsonResponse({'error': msg}, status=429)

        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
        )

        history = list(conversation.messages.values('role', 'content').order_by('created_at'))

        lang = conversation.language
        qa_match = knowledge.match_custom_qa(user_message, lang)
        if qa_match:
            parsed = {
                'text': qa_match['answer'],
                'rich_content': {},
                'quick_replies': [],
            }
            products = knowledge.search_products(user_message, limit=3, chatbot_settings=settings)
            if products:
                parsed['rich_content'] = {'type': 'product_cards', 'products': products}

            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=parsed['text'],
                rich_content=parsed['rich_content'],
                provider_used='custom_qa',
            )
            return JsonResponse({
                'message': parsed['text'],
                'rich_content': parsed['rich_content'],
                'quick_replies': parsed['quick_replies'],
                'conversation_id': conversation.id,
            })

        ai_messages, msg_language = build_messages(settings, user_message, history[:-1], lang)

        t0 = time.time()
        provider = get_provider(settings)
        if not provider.api_key:
            error_text = 'عذراً، لم يتم تكوين مفتاح API بعد. يرجى التواصل مع إدارة الموقع.' if msg_language == 'ar' else 'Sorry, the AI service is not configured yet. Please contact site administration.'
            Message.objects.create(conversation=conversation, role='assistant', content=error_text)
            return JsonResponse({
                'message': error_text,
                'rich_content': {},
                'quick_replies': [],
                'conversation_id': conversation.id,
            })
        response = provider.chat(ai_messages)
        elapsed_ms = int((time.time() - t0) * 1000)

        parsed = parse_response(response.content, msg_language, chatbot_settings=settings)

        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=parsed['text'],
            rich_content=parsed['rich_content'],
            tokens_used=response.tokens_used,
            response_time_ms=elapsed_ms,
            provider_used=settings.provider,
            model_used=response.model,
        )

        return JsonResponse({
            'message': parsed['text'],
            'rich_content': parsed['rich_content'],
            'quick_replies': parsed['quick_replies'],
            'conversation_id': conversation.id,
        })

    def _get_or_create_conversation(self, request, session_key, body):
        conversation_id = body.get('conversation_id')
        if conversation_id:
            try:
                return Conversation.objects.get(pk=conversation_id, session_key=session_key, is_active=True)
            except Conversation.DoesNotExist:
                pass

        lang = get_language() or 'ar'
        if lang not in ('ar', 'en'):
            lang = 'ar'

        conversation = Conversation.objects.create(
            session_key=session_key,
            user=request.user if request.user.is_authenticated else None,
            language=lang,
            page_url=body.get('page_url', ''),
        )
        return conversation

    def _check_rate_limit(self, session_key, settings):
        cache_key = f'chatbot_rate_{session_key}'
        count = cache.get(cache_key, 0)
        if count >= settings.rate_limit_per_minute:
            return False
        cache.set(cache_key, count + 1, 60)
        return True


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotStreamView(View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        if not settings.is_enabled:
            return JsonResponse({'error': 'Chatbot is disabled'}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        user_message = body.get('message', '').strip()
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)
        if len(user_message) > 2000:
            return JsonResponse({'error': 'Message too long'}, status=400)

        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        cache_key = f'chatbot_rate_{session_key}'
        count = cache.get(cache_key, 0)
        if count >= settings.rate_limit_per_minute:
            lang = get_language() or 'ar'
            msg = 'عذراً، أنت ترسل رسائل بسرعة كبيرة. انتظر قليلاً.' if lang == 'ar' else 'Too many messages. Please wait a moment.'
            return JsonResponse({'error': msg}, status=429)
        cache.set(cache_key, count + 1, 60)

        conversation_id = body.get('conversation_id')
        conversation = None
        if conversation_id:
            try:
                conversation = Conversation.objects.get(pk=conversation_id, session_key=session_key, is_active=True)
            except Conversation.DoesNotExist:
                conversation = None

        if not conversation:
            lang = get_language() or 'ar'
            if lang not in ('ar', 'en'):
                lang = 'ar'
            conversation = Conversation.objects.create(
                session_key=session_key,
                user=request.user if request.user.is_authenticated else None,
                language=lang,
                page_url=body.get('page_url', ''),
            )

        msg_count = conversation.messages.count()
        if msg_count >= settings.max_messages_per_session:
            lang = get_language() or 'ar'
            msg = 'وصلت للحد الأقصى من الرسائل. ابدأ محادثة جديدة.' if lang == 'ar' else 'Maximum messages reached. Start a new conversation.'
            return JsonResponse({'error': msg}, status=429)

        Message.objects.create(conversation=conversation, role='user', content=user_message)

        history = list(conversation.messages.values('role', 'content').order_by('created_at'))
        lang = conversation.language

        qa_match = knowledge.match_custom_qa(user_message, lang)
        if qa_match:
            parsed = {
                'text': qa_match['answer'],
                'rich_content': {},
                'quick_replies': [],
            }
            products = knowledge.search_products(user_message, limit=3, chatbot_settings=settings)
            if products:
                parsed['rich_content'] = {'type': 'product_cards', 'products': products}
            Message.objects.create(
                conversation=conversation, role='assistant',
                content=parsed['text'], rich_content=parsed['rich_content'], provider_used='custom_qa',
            )
            return JsonResponse({
                'message': parsed['text'],
                'rich_content': parsed['rich_content'],
                'quick_replies': parsed['quick_replies'],
                'conversation_id': conversation.id,
            })

        ai_messages, msg_language = build_messages(settings, user_message, history[:-1], lang)

        provider = get_provider(settings)
        if not provider.api_key:
            error_text = 'عذراً، لم يتم تكوين مفتاح API بعد.' if msg_language == 'ar' else 'Sorry, the AI service is not configured yet.'
            Message.objects.create(conversation=conversation, role='assistant', content=error_text)
            return JsonResponse({
                'message': error_text, 'rich_content': {}, 'quick_replies': [],
                'conversation_id': conversation.id,
            })

        t0 = time.time()
        response = provider.chat(ai_messages)
        elapsed_ms = int((time.time() - t0) * 1000)

        parsed = parse_response(response.content, msg_language, chatbot_settings=settings)

        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=parsed['text'],
            rich_content=parsed['rich_content'],
            tokens_used=response.tokens_used,
            response_time_ms=elapsed_ms,
            provider_used=settings.provider,
            model_used=response.model,
        )

        return JsonResponse({
            'message': parsed['text'],
            'rich_content': parsed['rich_content'],
            'quick_replies': parsed.get('quick_replies', []),
            'conversation_id': conversation.id,
        })


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotCompareView(View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        if not settings.is_enabled or not settings.enable_comparison:
            return JsonResponse({'error': 'Comparison not available'}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        product_ids = body.get('product_ids', [])
        if not product_ids or len(product_ids) > 4:
            return JsonResponse({'error': 'Provide 2-4 product IDs'}, status=400)

        products = knowledge.get_products_for_comparison(product_ids, chatbot_settings=settings)
        return JsonResponse({'products': products})


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotNewConversationView(View):
    def post(self, request):
        if not request.session.session_key:
            request.session.create()
        return JsonResponse({'status': 'ok'})


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotLeadRequestView(View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        if not settings.is_enabled:
            return JsonResponse({'error': 'Chatbot is disabled'}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        customer_name = body.get('customer_name', '').strip()
        customer_phone = body.get('customer_phone', '').strip()
        if not customer_name or not customer_phone:
            lang = get_language() or 'ar'
            msg = 'يرجى إدخال الاسم ورقم الهاتف.' if lang == 'ar' else 'Please enter your name and phone number.'
            return JsonResponse({'error': msg}, status=400)

        if not request.session.session_key:
            request.session.create()

        conversation_id = body.get('conversation_id')
        conversation = None
        if conversation_id:
            try:
                conversation = Conversation.objects.get(pk=conversation_id)
            except Conversation.DoesNotExist:
                pass

        lead = LeadRequest.objects.create(
            conversation=conversation,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=body.get('customer_address', '').strip(),
            expected_date=body.get('expected_date', '').strip(),
            product_interest=body.get('product_interest', '').strip(),
            notes=body.get('notes', '').strip(),
            language=get_language() or 'ar',
            session_key=request.session.session_key,
            page_url=body.get('page_url', ''),
        )

        lang = get_language() or 'ar'
        if lang == 'ar':
            msg = f'شكراً {customer_name}! تم تسجيل طلبك بنجاح. سيتواصل معك أحد موظفي المبيعات قريباً على الرقم {customer_phone}.'
        else:
            msg = f'Thank you {customer_name}! Your request has been submitted successfully. A sales representative will contact you soon at {customer_phone}.'

        return JsonResponse({
            'success': True,
            'message': msg,
            'lead_id': lead.id,
        })


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotVoiceTranscribeView(View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        if not settings.is_enabled or not settings.enable_voice_input:
            return JsonResponse({'error': 'Voice input is disabled'}, status=403)

        if settings.voice_provider == 'browser':
            return JsonResponse({'error': 'Transcription handled client-side'}, status=400)

        from .voice_providers.registry import get_voice_provider
        provider = get_voice_provider(settings)
        if not provider:
            return JsonResponse({'error': 'Voice provider not configured'}, status=400)

        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({'error': 'No audio file provided'}, status=400)

        audio_data = audio_file.read()
        content_type = audio_file.content_type or 'audio/webm'

        try:
            text = provider.transcribe(audio_data, content_type)
            return JsonResponse({'text': text})
        except Exception as e:
            logger.error(f'Voice transcription error: {e}')
            return JsonResponse({'error': 'Transcription failed'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotVoiceSynthesizeView(View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        if not settings.is_enabled or not settings.enable_voice_output:
            return JsonResponse({'error': 'Voice output is disabled'}, status=403)

        if settings.voice_provider == 'browser':
            return JsonResponse({'error': 'Synthesis handled client-side'}, status=400)

        from .voice_providers.registry import get_voice_provider
        provider = get_voice_provider(settings)
        if not provider:
            return JsonResponse({'error': 'Voice provider not configured'}, status=400)

        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid request'}, status=400)

        text = body.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        if len(text) > 5000:
            return JsonResponse({'error': 'Text too long'}, status=400)

        try:
            audio_data, content_type = provider.synthesize(text)
            response = HttpResponse(audio_data, content_type=content_type)
            response['Content-Disposition'] = 'inline; filename="speech.mp3"'
            return response
        except Exception as e:
            logger.error(f'Voice synthesis error: {e}')
            return JsonResponse({'error': 'Synthesis failed'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotVoiceAgentStartView(View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        if not settings.is_enabled or not settings.enable_voice_agent:
            return JsonResponse({'error': 'Voice agent is disabled'}, status=403)

        # Rate limit: max 5 voice agent starts per minute per session
        if not request.session.session_key:
            request.session.create()
        cache_key = f'voice_agent_rate_{request.session.session_key}'
        count = cache.get(cache_key, 0)
        if count >= 5:
            return JsonResponse({'error': 'Too many requests'}, status=429)
        cache.set(cache_key, count + 1, 60)

        from .voice_agent_providers.registry import get_voice_agent_provider
        provider = get_voice_agent_provider(settings)
        if not provider:
            return JsonResponse({'error': 'Voice agent provider not configured'}, status=400)

        init_config = provider.get_init_config()

        return JsonResponse({
            'success': True,
            'provider': settings.voice_agent_provider,
            'config': init_config,
        })
