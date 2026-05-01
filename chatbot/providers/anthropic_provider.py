import requests
from typing import List, Dict
from .base import AbstractProvider, ChatResponse


class AnthropicProvider(AbstractProvider):
    BASE_URL = "https://api.anthropic.com/v1/messages"

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> ChatResponse:
        system_msg = ''
        chat_messages = []
        for m in messages:
            if m['role'] == 'system':
                system_msg = m['content']
            else:
                chat_messages.append(m)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": chat_messages,
        }
        if system_msg:
            payload["system"] = system_msg

        try:
            resp = requests.post(self.BASE_URL, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            content = ''
            for block in data.get('content', []):
                if block.get('type') == 'text':
                    content += block.get('text', '')
            usage = data.get('usage', {})
            return ChatResponse(
                content=content,
                tokens_used=usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
                model=data.get('model', self.model),
                finish_reason=data.get('stop_reason', ''),
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
            {'id': 'claude-sonnet-4-6-20250514', 'name': 'Claude Sonnet 4.6'},
            {'id': 'claude-haiku-4-5-20251001', 'name': 'Claude Haiku 4.5'},
        ]
