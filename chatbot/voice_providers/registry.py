from .base import AbstractVoiceProvider
from .openai_voice import OpenAIVoiceProvider
from .elevenlabs_voice import ElevenLabsVoiceProvider
from .google_voice import GoogleVoiceProvider
from .azure_voice import AzureVoiceProvider


VOICE_PROVIDER_MAP = {
    'openai': OpenAIVoiceProvider,
    'elevenlabs': ElevenLabsVoiceProvider,
    'google': GoogleVoiceProvider,
    'azure': AzureVoiceProvider,
}


def get_voice_provider(settings) -> AbstractVoiceProvider:
    provider_name = settings.voice_provider
    if provider_name == 'browser' or provider_name not in VOICE_PROVIDER_MAP:
        return None
    cls = VOICE_PROVIDER_MAP[provider_name]
    return cls(
        api_key=settings.voice_api_key,
        language=settings.voice_language,
        voice_id=settings.voice_id,
    )


def get_all_voice_providers_voices():
    result = {}
    for name, cls in VOICE_PROVIDER_MAP.items():
        result[name] = cls.get_available_voices()
    return result
