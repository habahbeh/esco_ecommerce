from .base import AbstractVoiceProvider
from .openai_voice import OpenAIVoiceProvider
from .elevenlabs_voice import ElevenLabsVoiceProvider
from .google_voice import GoogleVoiceProvider
from .azure_voice import AzureVoiceProvider
from .custom_voice import CustomVoiceProvider


VOICE_PROVIDER_MAP = {
    'openai': OpenAIVoiceProvider,
    'elevenlabs': ElevenLabsVoiceProvider,
    'google': GoogleVoiceProvider,
    'azure': AzureVoiceProvider,
    'custom': CustomVoiceProvider,
}


def get_voice_provider(settings) -> AbstractVoiceProvider:
    provider_name = settings.voice_provider
    if provider_name == 'browser':
        return None

    if provider_name == 'custom':
        return CustomVoiceProvider(
            api_key=settings.voice_api_key,
            language=settings.voice_language,
            voice_id=settings.voice_id,
            tts_url=settings.custom_voice_tts_url,
            stt_url=settings.custom_voice_stt_url,
            auth_header=settings.custom_voice_auth_header or 'Authorization',
            auth_prefix=settings.custom_voice_auth_prefix or 'Bearer',
            tts_body_template=settings.custom_voice_tts_body,
            stt_field=settings.custom_voice_stt_field or 'file',
            response_path=settings.custom_voice_response_path or 'text',
        )

    cls = VOICE_PROVIDER_MAP.get(provider_name)
    if not cls:
        return None
    return cls(
        api_key=settings.voice_api_key,
        language=settings.voice_language,
        voice_id=settings.voice_id,
    )


def get_all_voice_providers_voices():
    result = {}
    for name, cls in VOICE_PROVIDER_MAP.items():
        if name == 'custom':
            continue
        result[name] = cls.get_available_voices()
    return result
