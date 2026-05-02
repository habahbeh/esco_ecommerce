import requests
from .base import AbstractVoiceAgentProvider


class CustomAgentProvider(AbstractVoiceAgentProvider):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ws_url = kwargs.get('ws_url', '')
        self.api_url = kwargs.get('api_url', '')
        self.auth_header = kwargs.get('auth_header', 'Authorization')
        self.auth_prefix = kwargs.get('auth_prefix', 'Bearer')
        self.embed_code = kwargs.get('embed_code', '')

    def get_sdk_url(self) -> str:
        return ''

    def get_init_config(self) -> dict:
        config = {
            'provider': 'custom_agent',
            'apiKey': self.api_key,
            'agentId': self.agent_id,
            'wsUrl': self.ws_url,
            'apiUrl': self.api_url,
            'authHeader': self.auth_header,
            'authPrefix': self.auth_prefix,
        }
        if self.extra_config:
            config.update(self.extra_config)
        return config

    def get_embed_script(self) -> str:
        return self.embed_code

    def test_connection(self) -> bool:
        if self.embed_code:
            return True
        if not self.api_key or not (self.ws_url or self.api_url):
            return False
        try:
            url = self.api_url or self.ws_url.replace('wss://', 'https://').replace('ws://', 'http://')
            auth_value = f'{self.auth_prefix} {self.api_key}'.strip() if self.auth_prefix else self.api_key
            r = requests.get(
                url,
                headers={self.auth_header: auth_value},
                timeout=10,
            )
            return r.status_code < 500
        except Exception:
            return False

    @classmethod
    def get_provider_info(cls) -> dict:
        return {
            'name': 'Custom Voice Agent',
            'supports_arabic': True,
            'website': '',
            'description': 'Connect any voice agent platform via embed code or WebSocket',
        }
