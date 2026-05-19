"""Stub LLM client para desenvolvimento local sem modelo real."""

from catbot.domain.ports.llm_client import LLMClient, LLMResponse


class StubLLMClient(LLMClient):
    async def generate(
        self,
        prompt: str,
        context: str = "",
        system_prompt_override: str | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            texto=f"[STUB] Resposta simulada para: {prompt[:80]}",
            confianca=0.5,
        )
