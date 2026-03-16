"""Stub LLM client para desenvolvimento local sem modelo real."""

from catbot.domain.ports.llm_client import LLMClient, LLMResponse


class StubLLMClient(LLMClient):
    async def generate(self, prompt: str, context: str = "") -> LLMResponse:
        return LLMResponse(
            texto=f"[STUB] Resposta simulada para: {prompt[:80]}",
            confianca=0.5,
        )
