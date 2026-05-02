import requests
from .base import AbstractVoiceProvider


class AzureVoiceProvider(AbstractVoiceProvider):
    def __init__(self, api_key: str, language: str = 'ar-SA', voice_id: str = '', **kwargs):
        super().__init__(api_key, language, voice_id, **kwargs)
        self.region = kwargs.get('region', 'eastus')

    def _get_token(self):
        response = requests.post(
            f'https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken',
            headers={
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Length': '0',
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.text

    def transcribe(self, audio_data: bytes, content_type: str = 'audio/webm') -> str:
        ct = 'audio/webm; codecs=opus'
        if 'wav' in content_type:
            ct = 'audio/wav'
        elif 'mp3' in content_type or 'mpeg' in content_type:
            ct = 'audio/mpeg'

        token = self._get_token()
        response = requests.post(
            f'https://{self.region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1'
            f'?language={self.language}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': ct,
            },
            data=audio_data,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        return result.get('DisplayText', '')

    def synthesize(self, text: str) -> tuple:
        voice_name = self.voice_id or 'ar-SA-HamedNeural'
        token = self._get_token()

        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{self.language}">'
            f'<voice name="{voice_name}">{text}</voice>'
            f'</speak>'
        )
        response = requests.post(
            f'https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
            },
            data=ssml.encode('utf-8'),
            timeout=30,
        )
        response.raise_for_status()
        return response.content, 'audio/mpeg'

    def test_connection(self) -> bool:
        try:
            self._get_token()
            return True
        except Exception:
            return False

    @classmethod
    def get_available_voices(cls) -> list:
        return [
            {'id': 'ar-SA-HamedNeural', 'name': 'Hamed (Male, Saudi)'},
            {'id': 'ar-SA-ZariyahNeural', 'name': 'Zariyah (Female, Saudi)'},
            {'id': 'ar-JO-TaimNeural', 'name': 'Taim (Male, Jordan)'},
            {'id': 'ar-JO-SanaNeural', 'name': 'Sana (Female, Jordan)'},
            {'id': 'ar-EG-ShakirNeural', 'name': 'Shakir (Male, Egypt)'},
            {'id': 'ar-EG-SalmaNeural', 'name': 'Salma (Female, Egypt)'},
            {'id': 'en-US-GuyNeural', 'name': 'Guy (Male, US)'},
            {'id': 'en-US-JennyNeural', 'name': 'Jenny (Female, US)'},
        ]
