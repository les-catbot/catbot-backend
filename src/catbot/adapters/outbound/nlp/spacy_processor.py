import spacy
from catbot.domain.ports.nlp_processor import NLPProcessor, NLPResult


class SpacyNLPProcessor(NLPProcessor):
    def __init__(self, model_name: str = "pt_core_news_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)

    async def process(self, texto: str) -> NLPResult:
        doc = self.nlp(texto)

        # 1. Normalização e Tokenização (ignorando pontuação e stopwords)
        tokens = [token.text.lower() for token in doc if not token.is_punct and not token.is_stop]
        texto_normalizado = " ".join(tokens)

        # 2. Reconhecimento de Entidades Nomeadas (NER) genéricas
        entidades = {ent.text: ent.label_ for ent in doc.ents}

        # Retorna o resultado preliminar (Sem a intenção, pois o Híbrido vai preencher)
        return NLPResult(
            texto_normalizado=texto_normalizado,
            tokens=tokens,
            intencao=None,
            entidades=entidades
        )