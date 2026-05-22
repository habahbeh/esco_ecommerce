import requests
from .base import AbstractVoiceAgentProvider


class BlandProvider(AbstractVoiceAgentProvider):

    def get_sdk_url(self) -> str:
        return 'https://cdn.bland.ai/embed/widget.js'

    def get_init_config(self) -> dict:
        config = {
            'provider': 'bland',
            'apiKey': self.api_key,
            'agentId': self.agent_id,
        }
        if self.phone_number:
            config['phoneNumber'] = self.phone_number
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
                'https://api.bland.ai/v1/agents',
                headers={'Authorization': self.api_key},
                timeout=10,
            )
            return r.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_provider_info(cls) -> dict:
        return {
            'name': 'Bland.ai',
            'supports_arabic': True,
            'website': 'https://bland.ai',
            'description': 'Enterprise AI phone agents with multilingual support',
        }
