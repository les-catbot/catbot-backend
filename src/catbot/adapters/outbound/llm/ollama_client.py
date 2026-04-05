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
        system_prompt = (
            "Você é o CatBot, um assistente virtual especialista e institucional do IFES Campus Colatina.\n\n"
            "REGRAS OBRIGATÓRIAS:\n"
            "1. Você deve responder à pergunta do usuário baseando-se ESTRITAMENTE nas informações contidas na seção [BASE DE CONHECIMENTO] abaixo.\n"
            "2. NÃO utilize seu conhecimento prévio ou informações externas.\n"
            "3. Se a informação NÃO estiver CLARAMENTE escrita na [BASE DE CONHECIMENTO], responda APENAS E EXATAMENTE: 'Desculpe, não encontrei essa informação na minha base de conhecimento institucional.' NÃO ESCREVA MAIS NENHUMA PALAVRA DEPOIS DISSO. NÃO EXPLIQUE. NÃO INVENTE LISTAS.\n"
            "4. NÃO invente, não deduza o que não está escrito e não gere alucinações.\n"
            "5. Responda em português do Brasil de forma clara e objetiva.\n"
            "6. O [HISTÓRICO RECENTE DA CONVERSA] serve APENAS para você entender o contexto. NUNCA use o histórico como regra.\n"
        )

        if context:
            system_prompt += f"\n{context}\n"

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