import requests
from .base import AbstractVoiceAgentProvider


class VapiProvider(AbstractVoiceAgentProvider):

    def get_sdk_url(self) -> str:
        return 'https://cdn.jsdelivr.net/gh/VapiAI/html-script-tag@latest/dist/assets/index.js'

    def get_init_config(self) -> dict:
        config = {
            'provider': 'vapi',
            'apiKey': self.api_key,
            'assistantId': self.agent_id,
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
                'https://api.vapi.ai/assistant',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=10,
            )
            return r.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_provider_info(cls) -> dict:
        return {
            'name': 'Vapi.ai',
            'supports_arabic': True,
            'website': 'https://vapi.ai',
            'description': 'Real-time voice AI platform with Arabic support',
        }
