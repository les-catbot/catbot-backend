"""Stub NLP processor para desenvolvimento local sem spaCy/NLTK."""

from catbot.domain.ports.nlp_processor import NLPProcessor, NLPResult


class StubNLPProcessor(NLPProcessor):
    async def process(self, texto: str) -> NLPResult:
        tokens = texto.lower().split()
        return NLPResult(
            texto_normalizado=texto.lower().strip(),
            tokens=tokens,
            intencao=None,
            entidades={},
        )
