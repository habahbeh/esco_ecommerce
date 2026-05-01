from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Generator


@dataclass
class ChatResponse:
    content: str = ''
    tokens_used: int = 0
    model: str = ''
    finish_reason: str = ''


class AbstractProvider(ABC):
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 1024)

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> ChatResponse:
        pass

    def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        response = self.chat(messages, **kwargs)
        yield response.content

    @abstractmethod
    def test_connection(self) -> bool:
        pass

    @classmethod
    def get_available_models(cls) -> List[Dict[str, str]]:
        return []
