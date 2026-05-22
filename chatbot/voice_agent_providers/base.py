from abc import ABC, abstractmethod


class AbstractVoiceAgentProvider(ABC):
    def __init__(self, api_key='', agent_id='', phone_number='', extra_config=None, **kwargs):
        self.api_key = api_key
        self.agent_id = agent_id
        self.phone_number = phone_number
        self.extra_config = extra_config or {}
        for k, v in kwargs.items():
            setattr(self, k, v)

    @abstractmethod
    def get_sdk_url(self) -> str:
        pass

    @abstractmethod
    def get_init_config(self) -> dict:
        pass

    def get_embed_script(self) -> str:
        return ''

    def test_connection(self) -> bool:
        return bool(self.api_key and self.agent_id)

    @classmethod
    def get_provider_info(cls) -> dict:
        return {
            'name': cls.__name__,
            'supports_arabic': False,
            'website': '',
        }
