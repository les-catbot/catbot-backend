"""Serviço de embeddings usando a API oficial da OpenAI."""

import logging

from openai import AsyncOpenAI

from catbot.domain.ports.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# text-embedding-3-small: 1536 dimensões, rápido e barato
# text-embedding-3-large: 3072 dimensões, mais preciso
_MODEL_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class OpenAIEmbeddingService(EmbeddingService):
    """Gera embeddings via API da OpenAI."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Envia os textos em lote para a OpenAI e devolve os vetores."""
        if not texts:
            return []

        # A API da OpenAI aceita listas inteiras — sem necessidade de loop
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        # A resposta vem ordenada pelo índice, preservando a ordem do input
        return [item.embedding for item in response.data]

    def dimension(self) -> int:
        return _MODEL_DIMENSIONS.get(self._model, 1536)
