import requests
from .base import AbstractVoiceProvider


class OpenAIVoiceProvider(AbstractVoiceProvider):
    BASE_URL = 'https://api.openai.com/v1'

    def transcribe(self, audio_data: bytes, content_type: str = 'audio/webm') -> str:
        ext = 'webm'
        if 'mp3' in content_type:
            ext = 'mp3'
        elif 'wav' in content_type:
            ext = 'wav'
        elif 'mp4' in content_type or 'mpeg' in content_type:
            ext = 'mp4'

        response = requests.post(
            f'{self.BASE_URL}/audio/transcriptions',
            headers={'Authorization': f'Bearer {self.api_key}'},
            files={'file': (f'audio.{ext}', audio_data, content_type)},
            data={'model': 'whisper-1', 'language': self.language[:2]},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get('text', '')

    def synthesize(self, text: str) -> tuple:
        voice = self.voice_id or 'alloy'
        response = requests.post(
            f'{self.BASE_URL}/audio/speech',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'tts-1',
                'input': text,
                'voice': voice,
                'response_format': 'mp3',
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.content, 'audio/mpeg'

    def test_connection(self) -> bool:
        try:
            response = requests.get(
                f'{self.BASE_URL}/models',
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_available_voices(cls) -> list:
        return [
            {'id': 'alloy', 'name': 'Alloy'},
            {'id': 'echo', 'name': 'Echo'},
            {'id': 'fable', 'name': 'Fable'},
            {'id': 'onyx', 'name': 'Onyx'},
            {'id': 'nova', 'name': 'Nova'},
            {'id': 'shimmer', 'name': 'Shimmer'},
        ]
