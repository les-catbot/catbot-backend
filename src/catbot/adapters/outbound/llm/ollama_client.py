import logging
import httpx
from catbot.domain.ports.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

class OllamaLLMClient(LLMClient):
    """Adaptador real para geração de texto usando o Ollama local."""

    def __init__(self, base_url: str, model: str = "llama3") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str, context: str = "", system_prompt_override: str | None = None) -> LLMResponse:
        # 1. System Prompt ultra simples (Apenas para definir a Persona)
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = (
                "Você é o CatBot, o assistente virtual institucional do IFES Campus Colatina.\n"
                "Sua comunicação deve ser clara, direta, prestativa e em português do Brasil."
            )

        # 2. Reestruturação do User Prompt: Contexto -> Pergunta -> Instrução
        user_prompt = prompt
        if context and not system_prompt_override:
            user_prompt = f"""{context}

=== PERGUNTA DO USUÁRIO ===
{prompt}

INSTRUÇÃO OBRIGATÓRIA: Responda à pergunta acima baseando-se APENAS nos documentos da [BASE DE CONHECIMENTO]. Se a resposta não estiver descrita nos documentos acima, responda EXATAMENTE: 'Desculpe, não encontrei essa informação na minha base de conhecimento institucional.'"""

        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0 # Essencial manter a 0 para RAG
            }
        }

        # 3. Modo JSON para o NLP Processor
        if system_prompt_override and "JSON" in system_prompt_override:
            payload["format"] = "json"

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