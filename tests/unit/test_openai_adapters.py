from types import SimpleNamespace

import pytest

from catbot.adapters.outbound.embedding.openai_embedding import OpenAIEmbeddingService
from catbot.adapters.outbound.llm.openai_client import OpenAILLMClient


class FakeCompletions:
    def __init__(self) -> None:
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content='{"intencao":"DUVIDA_ROD"}')
                )
            ]
        )


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[
                SimpleNamespace(embedding=[0.1] * 1536),
                SimpleNamespace(embedding=[0.2] * 1536),
            ]
        )


@pytest.mark.asyncio
async def test_openai_llm_forca_json_quando_prompt_de_sistema_pede_json():
    completions = FakeCompletions()
    client = OpenAILLMClient(api_key="test-key")
    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )

    response = await client.generate(
        prompt='Pergunta: "Qual o prazo?"',
        system_prompt_override="Retorne apenas JSON.",
    )

    assert response.texto == '{"intencao":"DUVIDA_ROD"}'
    assert completions.calls[0]["response_format"] == {"type": "json_object"}
    assert completions.calls[0]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_openai_llm_monta_prompt_rag_com_contexto():
    completions = FakeCompletions()
    client = OpenAILLMClient(api_key="test-key")
    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )

    await client.generate(
        prompt="Qual o prazo?",
        context="=== [BASE DE CONHECIMENTO] ===\nPrazo de 30 dias.",
    )

    user_message = completions.calls[0]["messages"][1]["content"]
    assert "=== PERGUNTA DO USUÁRIO ===" in user_message
    assert "baseando-se APENAS" in user_message


@pytest.mark.asyncio
async def test_openai_embedding_envia_lote_e_preserva_dimensao():
    embeddings = FakeEmbeddings()
    service = OpenAIEmbeddingService(api_key="test-key")
    service._client = SimpleNamespace(embeddings=embeddings)

    result = await service.generate_embeddings(["texto 1", "texto 2"])

    assert len(result) == 2
    assert len(result[0]) == 1536
    assert service.dimension() == 1536
    assert embeddings.calls[0]["model"] == "text-embedding-3-small"
    assert embeddings.calls[0]["input"] == ["texto 1", "texto 2"]
