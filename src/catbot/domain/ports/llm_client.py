from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    texto: str
    confianca: float


class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, context: str = "", system_prompt_override: str | None = None) -> LLMResponse:
        pass