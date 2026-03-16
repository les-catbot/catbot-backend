from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class NLPResult:
    texto_normalizado: str
    tokens: list[str]
    intencao: str | None = None
    entidades: dict[str, str] = field(default_factory=dict)


class NLPProcessor(ABC):
    @abstractmethod
    async def process(self, texto: str) -> NLPResult: ...
