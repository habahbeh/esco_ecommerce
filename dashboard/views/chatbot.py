import json
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta

from dashboard.mixins import DashboardAccessMixin, SuperuserRequiredMixin
from chatbot.models import ChatbotSettings, Conversation, Message, CustomQA, SuggestedQuestion
from chatbot.providers.registry import get_provider, get_all_providers_models
from chatbot.voice_providers.registry import get_all_voice_providers_voices
from chatbot.voice_agent_providers.registry import get_all_voice_agent_providers_info


class ChatbotSettingsView(SuperuserRequiredMixin, View):
    template_name = 'dashboard/chatbot/settings.html'

    def get(self, request):
        settings = ChatbotSettings.get_settings()
        all_models = get_all_providers_models()
        all_voices = get_all_voice_providers_voices()
        all_agent_providers = get_all_voice_agent_providers_info()
        api_key = settings.api_key or ''
        voice_api_key = settings.voice_api_key or ''
        voice_agent_api_key = settings.voice_agent_api_key or ''
        extra_config = settings.voice_agent_extra_config
        extra_config_json = json.dumps(extra_config, ensure_ascii=False, indent=2) if extra_config else ''
        context = {
            'settings': settings,
            'all_models': json.dumps(all_models),
            'all_voices': json.dumps(all_voices),
            'all_agent_providers': json.dumps(all_agent_providers),
            'api_key_set': bool(api_key),
            'api_key_masked': (api_key[:8] + '...' + api_key[-4:]) if len(api_key) > 12 else '',
            'voice_api_key_set': bool(voice_api_key),
            'voice_api_key_masked': (voice_api_key[:8] + '...' + voice_api_key[-4:]) if len(voice_api_key) > 12 else '',
            'voice_agent_api_key_set': bool(voice_agent_api_key),
            'voice_agent_api_key_masked': (voice_agent_api_key[:8] + '...' + voice_agent_api_key[-4:]) if len(voice_agent_api_key) > 12 else '',
            'voice_agent_extra_config_json': extra_config_json,
            'page_title': _('إعدادات الشات بوت'),
            'current_page': 'chatbot',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        settings = ChatbotSettings.get_settings()

        settings.is_enabled = request.POST.get('is_enabled') == 'on'
        settings.provider = request.POST.get('provider', 'openrouter')
        new_api_key = request.POST.get('api_key', '').strip()
        if new_api_key:
            settings.api_key = new_api_key
        settings.model_name = request.POST.get('model_name', 'openrouter/free')
        settings.temperature = request.POST.get('temperature', 0.7)
        settings.max_tokens = request.POST.get('max_tokens', 1024)

        settings.primary_color = request.POST.get('primary_color', '#1e88e5')
        settings.secondary_color = request.POST.get('secondary_color', '#ffffff')
        settings.position = request.POST.get('position', 'bottom-right')
        settings.bubble_size = request.POST.get('bubble_size', 'medium')
        settings.show_on_mobile = request.POST.get('show_on_mobile') == 'on'
        settings.welcome_message_ar = request.POST.get('welcome_message_ar', '')
        settings.welcome_message_en = request.POST.get('welcome_message_en', '')
        settings.bot_name_ar = request.POST.get('bot_name_ar', 'مساعد ESCO')
        settings.bot_name_en = request.POST.get('bot_name_en', 'ESCO Assistant')

        avatar_mode = request.POST.get('avatar_mode', 'icon')
        if avatar_mode == 'upload' and 'avatar' in request.FILES:
            settings.avatar = request.FILES['avatar']
            settings.avatar_icon = ''
        elif avatar_mode == 'icon':
            settings.avatar_icon = request.POST.get('avatar_icon', 'fas fa-robot')
            if settings.avatar:
                settings.avatar.delete(save=False)
                settings.avatar = None
        settings.avatar_icon_color = request.POST.get('avatar_icon_color', '#ffffff')

        settings.bubble_icon = request.POST.get('bubble_icon', 'fas fa-comments')
        settings.bubble_icon_color = request.POST.get('bubble_icon_color', '#ffffff')
        settings.bubble_bg_color = request.POST.get('bubble_bg_color', '#1e88e5')

        settings.system_prompt_ar = request.POST.get('system_prompt_ar', '')
        settings.system_prompt_en = request.POST.get('system_prompt_en', '')
        settings.max_history_messages = request.POST.get('max_history_messages', 10)
        settings.enable_product_search = request.POST.get('enable_product_search') == 'on'
        settings.enable_blog_search = request.POST.get('enable_blog_search') == 'on'
        settings.enable_comparison = request.POST.get('enable_comparison') == 'on'
        settings.enable_suggestions = request.POST.get('enable_suggestions') == 'on'
        settings.show_categories_in_response = request.POST.get('show_categories_in_response') == 'on'
        settings.product_status_filter = request.POST.get('product_status_filter', 'published_only')
        settings.hide_products_without_price = request.POST.get('hide_products_without_price') == 'on'
        settings.hide_out_of_stock = request.POST.get('hide_out_of_stock') == 'on'
        settings.show_price_in_response = request.POST.get('show_price_in_response') == 'on'
        settings.product_sort_order = request.POST.get('product_sort_order', 'newest')

        settings.enable_voice_input = request.POST.get('enable_voice_input') == 'on'
        settings.enable_voice_output = request.POST.get('enable_voice_output') == 'on'
        settings.voice_provider = request.POST.get('voice_provider', 'browser')
        new_voice_api_key = request.POST.get('voice_api_key', '').strip()
        if new_voice_api_key:
            settings.voice_api_key = new_voice_api_key
        settings.voice_language = request.POST.get('voice_language', 'ar-SA')
        voice_id = request.POST.get('voice_id', '')
        voice_id_text = request.POST.get('voice_id_text', '')
        settings.voice_id = voice_id_text if settings.voice_provider == 'custom' else voice_id
        settings.auto_play_voice = request.POST.get('auto_play_voice') == 'on'

        settings.custom_voice_tts_url = request.POST.get('custom_voice_tts_url', '')
        settings.custom_voice_stt_url = request.POST.get('custom_voice_stt_url', '')
        settings.custom_voice_auth_header = request.POST.get('custom_voice_auth_header', 'Authorization')
        settings.custom_voice_auth_prefix = request.POST.get('custom_voice_auth_prefix', 'Bearer')
        settings.custom_voice_tts_body = request.POST.get('custom_voice_tts_body', '')
        settings.custom_voice_stt_field = request.POST.get('custom_voice_stt_field', 'file')
        settings.custom_voice_response_path = request.POST.get('custom_voice_response_path', 'text')

        # Voice Agent settings
        settings.enable_voice_agent = request.POST.get('enable_voice_agent') == 'on'
        settings.voice_agent_provider = request.POST.get('voice_agent_provider', 'vapi')
        new_voice_agent_api_key = request.POST.get('voice_agent_api_key', '').strip()
        if new_voice_agent_api_key:
            settings.voice_agent_api_key = new_voice_agent_api_key
        settings.voice_agent_id = request.POST.get('voice_agent_id', '')
        settings.voice_agent_phone_number = request.POST.get('voice_agent_phone_number', '')
        settings.voice_agent_trigger = request.POST.get('voice_agent_trigger', 'floating_button')
        settings.voice_agent_button_color = request.POST.get('voice_agent_button_color', '#4caf50')
        settings.voice_agent_button_icon = request.POST.get('voice_agent_button_icon', 'fas fa-phone-alt')
        settings.voice_agent_button_position = request.POST.get('voice_agent_button_position', 'bottom-left')
        settings.voice_agent_label_ar = request.POST.get('voice_agent_label_ar', 'تحدث معنا')
        settings.voice_agent_label_en = request.POST.get('voice_agent_label_en', 'Talk to us')
        settings.voice_agent_embed_code = request.POST.get('voice_agent_embed_code', '')
        extra_config_str = request.POST.get('voice_agent_extra_config', '').strip()
        if extra_config_str:
            try:
                settings.voice_agent_extra_config = json.loads(extra_config_str)
            except (json.JSONDecodeError, ValueError):
                messages.warning(request, _('تنسيق JSON غير صالح في الإعدادات الإضافية للوكيل الصوتي'))
        else:
            settings.voice_agent_extra_config = {}
        settings.voice_agent_custom_ws_url = request.POST.get('voice_agent_custom_ws_url', '')
        settings.voice_agent_custom_api_url = request.POST.get('voice_agent_custom_api_url', '')
        settings.voice_agent_custom_auth_header = request.POST.get('voice_agent_custom_auth_header', 'Authorization')
        settings.voice_agent_custom_auth_prefix = request.POST.get('voice_agent_custom_auth_prefix', 'Bearer')

        settings.max_messages_per_session = request.POST.get('max_messages_per_session', 50)
        settings.rate_limit_per_minute = request.POST.get('rate_limit_per_minute', 10)

        settings.save()
        messages.success(request, _('تم حفظ إعدادات الشات بوت بنجاح'))
        return redirect('dashboard:chatbot_settings')


class ChatbotTestConnectionView(SuperuserRequiredMixin, View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        try:
            provider = get_provider(settings)
            success = provider.test_connection()
            if success:
                return JsonResponse({'success': True, 'message': 'Connection successful!'})
            else:
                return JsonResponse({'success': False, 'message': 'Connection failed. Check your API key and model.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class ChatbotTestVoiceAgentView(SuperuserRequiredMixin, View):
    def post(self, request):
        settings = ChatbotSettings.get_settings()
        try:
            from chatbot.voice_agent_providers.registry import get_voice_agent_provider
            provider = get_voice_agent_provider(settings)
            if not provider:
                return JsonResponse({'success': False, 'message': 'Voice agent provider not configured'})
            success = provider.test_connection()
            if success:
                return JsonResponse({'success': True, 'message': 'Voice agent connection successful!'})
            else:
                return JsonResponse({'success': False, 'message': 'Voice agent connection failed. Check your API key and Agent ID.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class ChatbotConversationListView(DashboardAccessMixin, View):
    template_name = 'dashboard/chatbot/conversations.html'

    def get(self, request):
        conversations = Conversation.objects.annotate(
            message_count=Count('messages')
        ).order_by('-updated_at')

        query = request.GET.get('q', '').strip()
        if query:
            conversations = conversations.filter(
                Q(messages__content__icontains=query) |
                Q(session_key__icontains=query)
            ).distinct()

        lang_filter = request.GET.get('language', '')
        if lang_filter:
            conversations = conversations.filter(language=lang_filter)

        # Simple pagination
        page = int(request.GET.get('page', 1))
        per_page = 20
        total = conversations.count()
        conversations = conversations[(page-1)*per_page:page*per_page]

        context = {
            'conversations': conversations,
            'query': query,
            'lang_filter': lang_filter,
            'page': page,
            'total_pages': (total + per_page - 1) // per_page,
            'total': total,
            'page_title': _('المحادثات'),
            'current_page': 'chatbot',
        }
        return render(request, self.template_name, context)


class ChatbotConversationDetailView(DashboardAccessMixin, View):
    template_name = 'dashboard/chatbot/conversation_detail.html'

    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        conv_messages = conversation.messages.all().order_by('created_at')
        context = {
            'conversation': conversation,
            'chat_messages': conv_messages,
            'page_title': f'{_("المحادثة")} #{conversation_id}',
            'current_page': 'chatbot',
        }
        return render(request, self.template_name, context)


class ChatbotConversationDeleteView(DashboardAccessMixin, View):
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        conversation.delete()
        messages.success(request, _('تم حذف المحادثة بنجاح'))
        return redirect('dashboard:chatbot_conversations')


class ChatbotCustomQAListView(DashboardAccessMixin, View):
    template_name = 'dashboard/chatbot/custom_qa.html'

    def get(self, request):
        qas = CustomQA.objects.all()
        suggested = SuggestedQuestion.objects.all()
        context = {
            'qas': qas,
            'suggested_questions': suggested,
            'page_title': _('الأسئلة المخصصة'),
            'current_page': 'chatbot',
        }
        return render(request, self.template_name, context)


class ChatbotCustomQACreateView(DashboardAccessMixin, View):
    def post(self, request):
        CustomQA.objects.create(
            question_ar=request.POST.get('question_ar', ''),
            question_en=request.POST.get('question_en', ''),
            answer_ar=request.POST.get('answer_ar', ''),
            answer_en=request.POST.get('answer_en', ''),
            keywords=request.POST.get('keywords', ''),
            priority=request.POST.get('priority', 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, _('تم إضافة السؤال والجواب بنجاح'))
        return redirect('dashboard:chatbot_custom_qa')


class ChatbotCustomQAEditView(DashboardAccessMixin, View):
    def post(self, request, qa_id):
        qa = get_object_or_404(CustomQA, pk=qa_id)
        qa.question_ar = request.POST.get('question_ar', '')
        qa.question_en = request.POST.get('question_en', '')
        qa.answer_ar = request.POST.get('answer_ar', '')
        qa.answer_en = request.POST.get('answer_en', '')
        qa.keywords = request.POST.get('keywords', '')
        qa.priority = request.POST.get('priority', 0)
        qa.is_active = request.POST.get('is_active') == 'on'
        qa.save()
        messages.success(request, _('تم تحديث السؤال والجواب بنجاح'))
        return redirect('dashboard:chatbot_custom_qa')


class ChatbotCustomQADeleteView(DashboardAccessMixin, View):
    def post(self, request, qa_id):
        qa = get_object_or_404(CustomQA, pk=qa_id)
        qa.delete()
        messages.success(request, _('تم حذف السؤال والجواب بنجاح'))
        return redirect('dashboard:chatbot_custom_qa')


class ChatbotSuggestedCreateView(DashboardAccessMixin, View):
    def post(self, request):
        SuggestedQuestion.objects.create(
            text_ar=request.POST.get('text_ar', ''),
            text_en=request.POST.get('text_en', ''),
            icon=request.POST.get('icon', 'fas fa-question-circle'),
            order=request.POST.get('order', 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, _('تم إضافة السؤال المقترح بنجاح'))
        return redirect('dashboard:chatbot_custom_qa')


class ChatbotSuggestedDeleteView(DashboardAccessMixin, View):
    def post(self, request, suggestion_id):
        s = get_object_or_404(SuggestedQuestion, pk=suggestion_id)
        s.delete()
        messages.success(request, _('تم حذف السؤال المقترح بنجاح'))
        return redirect('dashboard:chatbot_custom_qa')


class ChatbotAnalyticsView(DashboardAccessMixin, View):
    template_name = 'dashboard/chatbot/analytics.html'

    def get(self, request):
        now = timezone.now()
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        total_conversations = Conversation.objects.count()
        total_messages = Message.objects.count()
        conversations_7d = Conversation.objects.filter(started_at__gte=last_7d).count()
        messages_7d = Message.objects.filter(created_at__gte=last_7d).count()

        avg_response = Message.objects.filter(
            role='assistant', response_time_ms__gt=0
        ).aggregate(avg=Avg('response_time_ms'))['avg'] or 0

        total_tokens = Message.objects.filter(
            role='assistant'
        ).aggregate(total=Sum('tokens_used'))['total'] or 0

        top_models = Message.objects.filter(
            role='assistant', model_used__gt=''
        ).values('model_used').annotate(count=Count('id')).order_by('-count')[:5]

        context = {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'conversations_7d': conversations_7d,
            'messages_7d': messages_7d,
            'avg_response_ms': int(avg_response),
            'total_tokens': total_tokens,
            'top_models': top_models,
            'page_title': _('إحصائيات الشات بوت'),
            'current_page': 'chatbot',
        }
        return render(request, self.template_name, context)
