import logging

import httpx

from catbot.domain.ports.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)


class OllamaLLMClient(LLMClient):
    """Adaptador real para geração de texto usando o Ollama local."""

    def __init__(self, base_url: str, model: str = "llama3") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str, context: str = "") -> LLMResponse:
        # Engenhara de Prompt Básica (System Prompt)
        system_prompt = (
            "És o CatBot, um assistente virtual especialista do IFES Campus Colatina.\n"
            "Responde sempre em português do Brasil de forma clara e objetiva.\n"
        )

        if context:
            system_prompt += (
                "Usa APENAS a informação do seguinte contexto para responder à pergunta.\n"
                "Se a resposta não estiver no contexto, diz que não tens informação suficiente.\n\n"
                f"CONTEXTO:\n{context}\n"
            )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return LLMResponse(
                    texto=data.get("response", "").strip(),
                    confianca=0.85
                )
        except Exception as e:
            logger.exception("Erro detalhado ao contactar o Ollama (LLM):")
            return LLMResponse(
                texto="Desculpa, ocorreu um erro interno e não consegui gerar a resposta.",
                confianca=0.0
            )