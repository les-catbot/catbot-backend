"""NLP processor deterministic for tests."""

from catbot.domain.ports.nlp_processor import NLPProcessor, NLPResult


class StubNLPProcessor(NLPProcessor):
    def __init__(self, intencao: str = "DUVIDA_ROD") -> None:
        self._intencao = intencao

    async def process(self, texto: str) -> NLPResult:
        tokens = [token.lower() for token in texto.split()]
        return NLPResult(
            texto_normalizado=" ".join(tokens),
            tokens=tokens,
            intencao=self._intencao,
            entidades={},
        )
