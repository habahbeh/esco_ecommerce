import json as _json
import logging
import requests
from typing import List, Dict, Generator
from .base import AbstractProvider, ChatResponse

logger = logging.getLogger(__name__)


FREE_MODELS = [
    {'id': 'openrouter/free', 'name': 'Auto (Best Free Model)'},
    {'id': 'nvidia/nemotron-3-super-120b-a12b:free', 'name': 'NVIDIA Nemotron 3 Super 120B (Free)'},
    {'id': 'google/gemma-4-31b-it:free', 'name': 'Google Gemma 4 31B (Free)'},
    {'id': 'google/gemma-4-26b-a4b-it:free', 'name': 'Google Gemma 4 26B (Free)'},
    {'id': 'minimax/minimax-m2.5:free', 'name': 'MiniMax M2.5 (Free)'},
]

PAID_MODELS = [
    {'id': 'openai/gpt-4o-mini', 'name': 'GPT-4o Mini'},
    {'id': 'openai/gpt-4o', 'name': 'GPT-4o'},
    {'id': 'anthropic/claude-sonnet-4-6', 'name': 'Claude Sonnet 4.6'},
    {'id': 'google/gemini-2.5-flash', 'name': 'Gemini 2.5 Flash'},
]


class OpenRouterProvider(AbstractProvider):
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://esco.jo",
            "X-Title": "ESCO Chatbot",
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
        except requests.exceptions.Timeout:
            return ChatResponse(content='عذراً، استغرقت الاستجابة وقتاً طويلاً. حاول مرة أخرى.')
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                return ChatResponse(content='عذراً، عدد الطلبات كثير. انتظر قليلاً وحاول مرة أخرى.')
            return ChatResponse(content='عذراً، حدث خطأ في الاتصال بالذكاء الاصطناعي.')
        except Exception:
            return ChatResponse(content='عذراً، حدث خطأ غير متوقع.')

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
        except Exception as e:
            logger.error('OpenRouter stream error: %s', e, exc_info=True)
            yield 'عذراً، حدث خطأ غير متوقع.'

    def test_connection(self) -> bool:
        try:
            resp = self.chat([{"role": "user", "content": "Hi"}])
            return bool(resp.content and 'عذراً' not in resp.content)
        except Exception:
            return False

    @classmethod
    def get_available_models(cls) -> List[Dict[str, str]]:
        return FREE_MODELS + PAID_MODELS
