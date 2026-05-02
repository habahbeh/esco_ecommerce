import json
import base64
import requests
from .base import AbstractVoiceProvider


class GoogleVoiceProvider(AbstractVoiceProvider):
    STT_URL = 'https://speech.googleapis.com/v1/speech:recognize'
    TTS_URL = 'https://texttospeech.googleapis.com/v1/text:synthesize'

    def transcribe(self, audio_data: bytes, content_type: str = 'audio/webm') -> str:
        encoding = 'WEBM_OPUS'
        if 'wav' in content_type:
            encoding = 'LINEAR16'
        elif 'mp3' in content_type or 'mpeg' in content_type:
            encoding = 'MP3'

        payload = {
            'config': {
                'encoding': encoding,
                'languageCode': self.language,
                'enableAutomaticPunctuation': True,
            },
            'audio': {
                'content': base64.b64encode(audio_data).decode('utf-8'),
            },
        }
        response = requests.post(
            f'{self.STT_URL}?key={self.api_key}',
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        results = response.json().get('results', [])
        if results:
            return results[0].get('alternatives', [{}])[0].get('transcript', '')
        return ''

    def synthesize(self, text: str) -> tuple:
        voice_name = self.voice_id or f'{self.language}-Wavenet-A'
        payload = {
            'input': {'text': text},
            'voice': {
                'languageCode': self.language,
                'name': voice_name,
            },
            'audioConfig': {
                'audioEncoding': 'MP3',
            },
        }
        response = requests.post(
            f'{self.TTS_URL}?key={self.api_key}',
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        audio_content = response.json().get('audioContent', '')
        return base64.b64decode(audio_content), 'audio/mpeg'

    def test_connection(self) -> bool:
        try:
            response = requests.post(
                f'{self.TTS_URL}?key={self.api_key}',
                json={
                    'input': {'text': 'test'},
                    'voice': {'languageCode': 'en-US', 'name': 'en-US-Wavenet-A'},
                    'audioConfig': {'audioEncoding': 'MP3'},
                },
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_available_voices(cls) -> list:
        return [
            {'id': 'ar-XA-Wavenet-A', 'name': 'Arabic Wavenet A (Female)'},
            {'id': 'ar-XA-Wavenet-B', 'name': 'Arabic Wavenet B (Male)'},
            {'id': 'ar-XA-Wavenet-C', 'name': 'Arabic Wavenet C (Male)'},
            {'id': 'en-US-Wavenet-D', 'name': 'English Wavenet D (Male)'},
            {'id': 'en-US-Wavenet-F', 'name': 'English Wavenet F (Female)'},
        ]
