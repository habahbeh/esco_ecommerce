import requests
from typing import List, Dict
from .base import AbstractProvider, ChatResponse


class GoogleProvider(AbstractProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> ChatResponse:
        system_instruction = ''
        contents = []
        for m in messages:
            if m['role'] == 'system':
                system_instruction = m['content']
            else:
                role = 'user' if m['role'] == 'user' else 'model'
                contents.append({"role": role, "parts": [{"text": m['content']}]})

        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": float(self.temperature),
                "maxOutputTokens": self.max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get('candidates', [{}])
            content = ''
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                content = ''.join(p.get('text', '') for p in parts)
            usage = data.get('usageMetadata', {})
            return ChatResponse(
                content=content,
                tokens_used=usage.get('totalTokenCount', 0),
                model=self.model,
                finish_reason=candidates[0].get('finishReason', '') if candidates else '',
            )
        except Exception:
            return ChatResponse(content='عذراً، حدث خطأ في الاتصال بالذكاء الاصطناعي.')

    def test_connection(self) -> bool:
        try:
            resp = self.chat([{"role": "user", "content": "Hi"}])
            return bool(resp.content and 'عذراً' not in resp.content)
        except Exception:
            return False

    @classmethod
    def get_available_models(cls) -> List[Dict[str, str]]:
        return [
            {'id': 'gemini-2.5-flash', 'name': 'Gemini 2.5 Flash'},
            {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro'},
        ]
