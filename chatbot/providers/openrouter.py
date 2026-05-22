import json as _json
import logging
import requests
from typing import List, Dict, Generator
from .base import AbstractProvider, ChatResponse

logger = logging.getLogger(__name__)


FALLBACK_MODELS = [
    'liquid/lfm-2.5-1.2b-instruct:free',
    'nvidia/nemotron-nano-9b-v2:free',
]

FREE_MODELS = [
    {'id': 'nvidia/nemotron-3-nano-30b-a3b:free', 'name': 'NVIDIA Nemotron 3 Nano 30B (Free)'},
    {'id': 'google/gemma-4-31b-it:free', 'name': 'Google Gemma 4 31B (Free)'},
    {'id': 'deepseek/deepseek-v4-flash:free', 'name': 'DeepSeek V4 Flash (Free)'},
    {'id': 'liquid/lfm-2.5-1.2b-instruct:free', 'name': 'Liquid LFM 1.2B (Free, Fast)'},
    {'id': 'nvidia/nemotron-nano-9b-v2:free', 'name': 'NVIDIA Nemotron Nano 9B v2 (Free)'},
    {'id': 'openrouter/free', 'name': 'Auto (Best Free Model)'},
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

    def _try_chat(self, messages, model_override=None, timeout=30):
        payload = self._payload(messages)
        if model_override:
            payload['model'] = model_override
        resp = requests.post(self.BASE_URL, json=payload, headers=self._headers(), timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if 'error' in data:
            raise ValueError(data['error'].get('message', str(data['error'])) if isinstance(data['error'], dict) else str(data['error']))
        choice = data.get('choices', [{}])[0]
        message = choice.get('message', {})
        content = message.get('content', '')
        if not content:
            raise ValueError('Empty response from model')
        usage = data.get('usage', {})
        return ChatResponse(
            content=content,
            tokens_used=usage.get('total_tokens', 0),
            model=data.get('model', model_override or self.model),
            finish_reason=choice.get('finish_reason', ''),
        )

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> ChatResponse:
        try:
            return self._try_chat(messages)
        except Exception as primary_err:
            logger.warning('Primary model %s failed: %s', self.model, primary_err)
            for fallback in FALLBACK_MODELS:
                if fallback == self.model:
                    continue
                try:
                    logger.info('Trying fallback model: %s', fallback)
                    return self._try_chat(messages, model_override=fallback)
                except Exception as fb_err:
                    logger.warning('Fallback %s failed: %s', fallback, fb_err)
            if isinstance(primary_err, requests.exceptions.Timeout):
                return ChatResponse(content='عذراً، استغرقت الاستجابة وقتاً طويلاً. حاول مرة أخرى.')
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
