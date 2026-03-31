import spacy
from catbot.domain.ports.nlp_processor import NLPProcessor, NLPResult


class SpacyNLPProcessor(NLPProcessor):
    def __init__(self, model_name: str = "pt_core_news_sm"):
        # Carrega o modelo em português do spaCy
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)

    async def process(self, texto: str) -> NLPResult:
        doc = self.nlp(texto)

        # 1. Normalização e Tokenização (ignorando pontuação e stopwords)
        tokens = [token.text.lower() for token in doc if not token.is_punct]
        texto_normalizado = " ".join(tokens)

        # 2. Reconhecimento de Entidades Nomeadas (NER)
        entidades = {ent.text: ent.label_ for ent in doc.ents}

        # 3. Classificação de Intenção (Exemplo simples baseado em regras/palavras-chave)
        # Em um cenário avançado, você pode chamar o LLM aqui para classificar a intenção.
        intencao = self._classificar_intencao(texto_normalizado)

        return NLPResult(
            texto_normalizado=texto_normalizado,
            tokens=tokens,
            intencao=intencao,
            entidades=entidades
        )

    def _classificar_intencao(self, texto: str) -> str | None:
        if "relatório" in texto or "resumo" in texto:
            return "gerar_relatorio"
        elif "buscar" in texto or "documento" in texto:
            return "busca_documento"
        return "pergunta_geral"