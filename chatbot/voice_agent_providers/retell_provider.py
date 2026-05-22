import requests
from .base import AbstractVoiceAgentProvider


class RetellProvider(AbstractVoiceAgentProvider):

    def get_sdk_url(self) -> str:
        return 'https://cdn.retellai.com/retell-web-sdk/latest/retell-web-sdk.umd.js'

    def get_init_config(self) -> dict:
        config = {
            'provider': 'retell',
            'apiKey': self.api_key,
            'agentId': self.agent_id,
        }
        if self.extra_config:
            config.update(self.extra_config)
        return config

    def get_embed_script(self) -> str:
        return ''

    def test_connection(self) -> bool:
        if not self.api_key:
            return False
        try:
            r = requests.get(
                'https://api.retellai.com/v2/agent',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=10,
            )
            return r.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_provider_info(cls) -> dict:
        return {
            'name': 'Retell.ai',
            'supports_arabic': True,
            'website': 'https://retellai.com',
            'description': 'Conversational voice AI with low latency and Arabic support',
        }
