import urllib.parse
import requests
from .base import AbstractVoiceProvider


class FreeTTSProvider(AbstractVoiceProvider):
    """
    Free TTS using Google Translate's TTS endpoint (no API key needed).
    Supports Arabic, English, and many other languages.
    STT falls back to browser Web Speech API (client-side).
    """

    def transcribe(self, audio_data: bytes, content_type: str = 'audio/webm') -> str:
        raise NotImplementedError('Free provider uses browser STT (client-side)')

    def synthesize(self, text: str) -> tuple:
        lang = (self.language or 'ar-SA')[:2]

        chunks = self._split_text(text, 200)
        audio_parts = []
        for chunk in chunks:
            encoded = urllib.parse.quote(chunk)
            url = f'https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q={encoded}'
            response = requests.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://translate.google.com/',
                },
                timeout=10,
            )
            response.raise_for_status()
            audio_parts.append(response.content)

        return b''.join(audio_parts), 'audio/mpeg'

    def _split_text(self, text, max_len):
        if len(text) <= max_len:
            return [text]

        chunks = []
        separators = ['。', '．', '.', '،', ',', '؟', '?', '!', '！', '؛', ';', '\n']
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            split_pos = -1
            for sep in separators:
                pos = text.rfind(sep, 0, max_len)
                if pos > split_pos:
                    split_pos = pos
            if split_pos <= 0:
                space_pos = text.rfind(' ', 0, max_len)
                if space_pos > 0:
                    split_pos = space_pos
                else:
                    split_pos = max_len - 1
            chunks.append(text[:split_pos + 1].strip())
            text = text[split_pos + 1:].strip()
        return [c for c in chunks if c]

    def test_connection(self) -> bool:
        try:
            audio, _ = self.synthesize('test')
            return len(audio) > 0
        except Exception:
            return False

    @classmethod
    def get_available_voices(cls) -> list:
        return []
