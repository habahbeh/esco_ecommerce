from .base import AbstractVoiceAgentProvider


class LiveKitProvider(AbstractVoiceAgentProvider):

    def get_sdk_url(self) -> str:
        return 'https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.umd.min.js'

    def get_init_config(self) -> dict:
        config = {
            'provider': 'livekit',
            'apiKey': self.api_key,
            'agentId': self.agent_id,
            'wsUrl': getattr(self, 'ws_url', ''),
        }
        if self.extra_config:
            config.update(self.extra_config)
        return config

    def get_embed_script(self) -> str:
        return ''

    def test_connection(self) -> bool:
        return bool(self.api_key and self.agent_id)

    @classmethod
    def get_provider_info(cls) -> dict:
        return {
            'name': 'LiveKit',
            'supports_arabic': True,
            'website': 'https://livekit.io',
            'description': 'Open-source real-time communication with AI voice agents',
        }
