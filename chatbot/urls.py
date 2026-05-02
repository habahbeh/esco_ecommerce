from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('config/', views.ChatbotConfigView.as_view(), name='config'),
    path('message/', views.ChatbotMessageView.as_view(), name='message'),
    path('stream/', views.ChatbotStreamView.as_view(), name='stream'),
    path('compare/', views.ChatbotCompareView.as_view(), name='compare'),
    path('new/', views.ChatbotNewConversationView.as_view(), name='new_conversation'),
    path('lead-request/', views.ChatbotLeadRequestView.as_view(), name='lead_request'),
    path('voice/transcribe/', views.ChatbotVoiceTranscribeView.as_view(), name='voice_transcribe'),
    path('voice/synthesize/', views.ChatbotVoiceSynthesizeView.as_view(), name='voice_synthesize'),
]
