from django.contrib import admin
from .models import ChatbotSettings, Conversation, Message, CustomQA, SuggestedQuestion


@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_enabled', 'provider', 'model_name']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_key', 'user', 'language', 'started_at', 'is_active']
    list_filter = ['language', 'is_active', 'started_at']
    search_fields = ['session_key']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'role', 'created_at', 'tokens_used']
    list_filter = ['role', 'provider_used']


@admin.register(CustomQA)
class CustomQAAdmin(admin.ModelAdmin):
    list_display = ['question_ar', 'is_active', 'priority']
    list_filter = ['is_active']


@admin.register(SuggestedQuestion)
class SuggestedQuestionAdmin(admin.ModelAdmin):
    list_display = ['text_ar', 'order', 'is_active']
    list_filter = ['is_active']
