import json as _json
import requests
from typing import List, Dict, Generator
from .base import AbstractProvider, ChatResponse


class OpenAIProvider(AbstractProvider):
    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, messages, stream=False):
        p = {
            "model": self.model,
            "messages": messages,
            "temperature": float(self.temperature),
            "max_tokens": self.max_tokens,
        }
        if stream:
            p["stream"] = True
        return p

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> ChatResponse:
        try:
            resp = requests.post(self.BASE_URL, json=self._payload(messages), headers=self._headers(), timeout=60)
            resp.raise_for_status()
            data = resp.json()
            choice = data.get('choices', [{}])[0]
            message = choice.get('message', {})
            usage = data.get('usage', {})
            return ChatResponse(
                content=message.get('content', ''),
                tokens_used=usage.get('total_tokens', 0),
                model=data.get('model', self.model),
                finish_reason=choice.get('finish_reason', ''),
            )
        except Exception:
            return ChatResponse(content='عذراً، حدث خطأ في الاتصال بالذكاء الاصطناعي.')

    def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        try:
            resp = requests.post(
                self.BASE_URL,
                json=self._payload(messages, stream=True),
                headers=self._headers(),
                timeout=60,
                stream=True,
            )
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode('utf-8', errors='replace')
                if not line.startswith('data: '):
                    continue
                payload = line[6:]
                if payload.strip() == '[DONE]':
                    break
                try:
                    chunk = _json.loads(payload)
                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                    token = delta.get('content', '')
                    if token:
                        yield token
                except (_json.JSONDecodeError, IndexError, KeyError):
                    continue
        except Exception:
            yield 'عذراً، حدث خطأ في الاتصال بالذكاء الاصطناعي.'

    def test_connection(self) -> bool:
        try:
            resp = self.chat([{"role": "user", "content": "Hi"}])
            return bool(resp.content and 'عذراً' not in resp.content)
        except Exception:
            return False

    @classmethod
    def get_available_models(cls) -> List[Dict[str, str]]:
        return [
            {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini'},
            {'id': 'gpt-4o', 'name': 'GPT-4o'},
            {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo'},
        ]
