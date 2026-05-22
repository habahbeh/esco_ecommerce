import requests
from .base import AbstractVoiceAgentProvider


class VoiceflowProvider(AbstractVoiceAgentProvider):

    def get_sdk_url(self) -> str:
        return 'https://cdn.voiceflow.com/widget/bundle.mjs'

    def get_init_config(self) -> dict:
        config = {
            'provider': 'voiceflow',
            'projectId': self.agent_id,
            'apiKey': self.api_key,
        }
        if self.extra_config:
            config.update(self.extra_config)
        return config

    def get_embed_script(self) -> str:
        return ''

    def test_connection(self) -> bool:
        if not self.api_key or not self.agent_id:
            return False
        try:
            r = requests.get(
                f'https://general-runtime.voiceflow.com/state/{self.agent_id}/user/test',
                headers={'Authorization': self.api_key},
                timeout=10,
            )
            return r.status_code in (200, 404)
        except Exception:
            return False

    @classmethod
    def get_provider_info(cls) -> dict:
        return {
            'name': 'Voiceflow',
            'supports_arabic': True,
            'website': 'https://voiceflow.com',
            'description': 'Visual conversation design platform with voice and chat',
        }
