"""Adaptador LLM usando a API oficial da OpenAI."""

import logging

from openai import AsyncOpenAI

from catbot.domain.ports.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)


class OpenAILLMClient(LLMClient):
    """Adaptador para geração de texto usando a API da OpenAI."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate(
        self,
        prompt: str,
        context: str = "",
        system_prompt_override: str | None = None,
    ) -> LLMResponse:
        # 1. Define o system prompt
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = (
                "Você é o CatBot, o assistente virtual institucional do IFES Campus Colatina.\n"
                "Sua comunicação deve ser clara, direta, prestativa e em português do Brasil."
            )

        # 2. Monta o user prompt com contexto RAG (quando existir)
        user_prompt = prompt
        if context and not system_prompt_override:
            user_prompt = (
                f"{context}\n\n"
                f"=== PERGUNTA DO USUÁRIO ===\n"
                f"{prompt}\n\n"
                "INSTRUÇÃO OBRIGATÓRIA: Responda à pergunta acima baseando-se APENAS nos "
                "documentos da [BASE DE CONHECIMENTO]. Se a resposta não estiver descrita "
                "nos documentos acima, responda EXATAMENTE: "
                "'Desculpe, não encontrei essa informação na minha base de conhecimento "
                "institucional.'"
            )

        # 3. Força resposta JSON quando o sistema pede (usado pelo NLP Processor)
        kwargs = {}
        if system_prompt_override and "JSON" in system_prompt_override:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.0,  # Essencial manter 0 para RAG
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **kwargs,
            )
            texto = response.choices[0].message.content or ""
            return LLMResponse(texto=texto.strip(), confianca=0.85)

        except Exception:
            logger.exception("Erro ao contactar a API da OpenAI (LLM):")
            return LLMResponse(
                texto="Desculpa, ocorreu um erro interno e não consegui gerar a resposta.",
                confianca=0.0,
            )
