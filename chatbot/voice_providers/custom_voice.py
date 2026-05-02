import json
import requests
from .base import AbstractVoiceProvider


class CustomVoiceProvider(AbstractVoiceProvider):
    """
    Generic voice provider that works with any platform (Lahajati, PlayHT, Murf, etc.)
    via configurable API URLs, auth headers, and request/response patterns.
    """

    def __init__(self, api_key: str, language: str = 'ar-SA', voice_id: str = '', **kwargs):
        super().__init__(api_key, language, voice_id, **kwargs)
        self.tts_url = kwargs.get('tts_url', '')
        self.stt_url = kwargs.get('stt_url', '')
        self.auth_header = kwargs.get('auth_header', 'Authorization')
        self.auth_prefix = kwargs.get('auth_prefix', 'Bearer')
        self.tts_body_template = kwargs.get('tts_body_template', '')
        self.stt_field = kwargs.get('stt_field', 'file')
        self.response_path = kwargs.get('response_path', 'text')

    def _build_auth_headers(self):
        headers = {}
        if self.api_key:
            if self.auth_prefix:
                headers[self.auth_header] = f'{self.auth_prefix} {self.api_key}'
            else:
                headers[self.auth_header] = self.api_key
        return headers

    def _extract_nested(self, data, path):
        parts = path.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, '')
            else:
                return ''
        return current if isinstance(current, str) else str(current) if current else ''

    def transcribe(self, audio_data: bytes, content_type: str = 'audio/webm') -> str:
        if not self.stt_url:
            raise ValueError('STT URL not configured')

        ext = 'webm'
        if 'mp3' in content_type:
            ext = 'mp3'
        elif 'wav' in content_type:
            ext = 'wav'
        elif 'mp4' in content_type:
            ext = 'mp4'

        headers = self._build_auth_headers()

        files = {self.stt_field: (f'audio.{ext}', audio_data, content_type)}
        data = {}
        if self.language:
            data['language'] = self.language
        if self.voice_id:
            data['voice_id'] = self.voice_id

        response = requests.post(
            self.stt_url,
            headers=headers,
            files=files,
            data=data if data else None,
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        return self._extract_nested(result, self.response_path)

    def synthesize(self, text: str) -> tuple:
        if not self.tts_url:
            raise ValueError('TTS URL not configured')

        headers = self._build_auth_headers()
        headers['Content-Type'] = 'application/json'

        if self.tts_body_template:
            body_str = self.tts_body_template.replace('{text}', text)
            body_str = body_str.replace('{voice_id}', self.voice_id or '')
            body_str = body_str.replace('{language}', self.language or '')
            try:
                body = json.loads(body_str)
            except json.JSONDecodeError:
                body = {'text': text, 'voice_id': self.voice_id, 'language': self.language}
        else:
            body = {'text': text}
            if self.voice_id:
                body['voice_id'] = self.voice_id
            if self.language:
                body['language'] = self.language

        response = requests.post(
            self.tts_url,
            headers=headers,
            json=body,
            timeout=30,
        )
        response.raise_for_status()

        response_ct = response.headers.get('Content-Type', 'audio/mpeg')
        if 'json' in response_ct:
            data = response.json()
            audio_url = self._extract_nested(data, 'audio_url') or self._extract_nested(data, 'url')
            if audio_url:
                audio_response = requests.get(audio_url, timeout=30)
                audio_response.raise_for_status()
                return audio_response.content, audio_response.headers.get('Content-Type', 'audio/mpeg')
            raise ValueError('No audio URL in response')

        return response.content, response_ct

    def test_connection(self) -> bool:
        try:
            headers = self._build_auth_headers()
            if self.tts_url:
                response = requests.options(self.tts_url, headers=headers, timeout=10)
                return response.status_code < 500
            if self.stt_url:
                response = requests.options(self.stt_url, headers=headers, timeout=10)
                return response.status_code < 500
            return False
        except Exception:
            return False

    @classmethod
    def get_available_voices(cls) -> list:
        return []
