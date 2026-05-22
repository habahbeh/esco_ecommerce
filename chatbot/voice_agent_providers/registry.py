from .base import AbstractVoiceAgentProvider
from .vapi_provider import VapiProvider
from .bland_provider import BlandProvider
from .retell_provider import RetellProvider
from .voiceflow_provider import VoiceflowProvider
from .livekit_provider import LiveKitProvider
from .custom_agent_provider import CustomAgentProvider


VOICE_AGENT_PROVIDER_MAP = {
    'vapi': VapiProvider,
    'bland': BlandProvider,
    'retell': RetellProvider,
    'voiceflow': VoiceflowProvider,
    'livekit': LiveKitProvider,
    'custom_agent': CustomAgentProvider,
}


def get_voice_agent_provider(settings) -> AbstractVoiceAgentProvider:
    provider_name = settings.voice_agent_provider
    cls = VOICE_AGENT_PROVIDER_MAP.get(provider_name)
    if not cls:
        return None

    kwargs = {
        'api_key': settings.voice_agent_api_key,
        'agent_id': settings.voice_agent_id,
        'phone_number': settings.voice_agent_phone_number,
        'extra_config': settings.voice_agent_extra_config or {},
    }

    if provider_name == 'custom_agent':
        kwargs['ws_url'] = settings.voice_agent_custom_ws_url
        kwargs['api_url'] = settings.voice_agent_custom_api_url
        kwargs['auth_header'] = settings.voice_agent_custom_auth_header or 'Authorization'
        kwargs['auth_prefix'] = settings.voice_agent_custom_auth_prefix or 'Bearer'
        kwargs['embed_code'] = settings.voice_agent_embed_code

    if provider_name == 'livekit':
        kwargs['ws_url'] = settings.voice_agent_custom_ws_url

    return cls(**kwargs)


def get_all_voice_agent_providers_info():
    result = {}
    for name, cls in VOICE_AGENT_PROVIDER_MAP.items():
        result[name] = cls.get_provider_info()
    return result
