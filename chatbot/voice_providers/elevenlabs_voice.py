import requests
from .base import AbstractVoiceProvider


class ElevenLabsVoiceProvider(AbstractVoiceProvider):
    BASE_URL = 'https://api.elevenlabs.io/v1'

    def transcribe(self, audio_data: bytes, content_type: str = 'audio/webm') -> str:
        ext = 'webm'
        if 'mp3' in content_type:
            ext = 'mp3'
        elif 'wav' in content_type:
            ext = 'wav'

        response = requests.post(
            f'{self.BASE_URL}/speech-to-text',
            headers={'xi-api-key': self.api_key},
            files={'file': (f'audio.{ext}', audio_data, content_type)},
            data={'model_id': 'scribe_v1', 'language_code': self.language[:2]},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get('text', '')

    def synthesize(self, text: str) -> tuple:
        voice_id = self.voice_id or 'pNInz6obpgDQGcFmaJgB'
        response = requests.post(
            f'{self.BASE_URL}/text-to-speech/{voice_id}',
            headers={
                'xi-api-key': self.api_key,
                'Content-Type': 'application/json',
            },
            json={
                'text': text,
                'model_id': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.75,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.content, 'audio/mpeg'

    def test_connection(self) -> bool:
        try:
            response = requests.get(
                f'{self.BASE_URL}/user',
                headers={'xi-api-key': self.api_key},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_available_voices(cls) -> list:
        return [
            {'id': 'pNInz6obpgDQGcFmaJgB', 'name': 'Adam (Male)'},
            {'id': '21m00Tcm4TlvDq8ikWAM', 'name': 'Rachel (Female)'},
            {'id': 'EXAVITQu4vr4xnSDxMaL', 'name': 'Bella (Female)'},
            {'id': 'ErXwobaYiN019PkySvjV', 'name': 'Antoni (Male)'},
        ]
