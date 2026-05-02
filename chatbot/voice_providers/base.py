from abc import ABC, abstractmethod


class AbstractVoiceProvider(ABC):
    def __init__(self, api_key: str, language: str = 'ar-SA', voice_id: str = '', **kwargs):
        self.api_key = api_key
        self.language = language
        self.voice_id = voice_id

    @abstractmethod
    def transcribe(self, audio_data: bytes, content_type: str = 'audio/webm') -> str:
        pass

    @abstractmethod
    def synthesize(self, text: str) -> tuple:
        """Returns (audio_bytes, content_type)"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        pass

    @classmethod
    def get_available_voices(cls) -> list:
        return []
