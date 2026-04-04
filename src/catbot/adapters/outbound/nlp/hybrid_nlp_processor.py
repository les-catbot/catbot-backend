import json
import re
from catbot.domain.ports.nlp_processor import NLPProcessor, NLPResult
from catbot.domain.ports.llm_client import LLMClient
from catbot.adapters.outbound.nlp.spacy_processor import SpacyNLPProcessor

PROMPT_SISTEMA_INTENCAO = """Você é um classificador de intenções especializado na base normativa do IFES (Instituto Federal do Espírito Santo). Sua única função é analisar a pergunta do usuário e categorizá-la rigorosamente em uma das 4 categorias abaixo, extraindo entidades relevantes para busca em banco de dados vetorial.

Definição das Intenções:
DUVIDA_ROD: Perguntas sobre a vida acadêmica direta do aluno (Ensino Técnico ou Graduação). Caracteriza-se por temas como: processos de matrícula, trancamento, transferência, aproveitamento de estudos, critérios de avaliação (notas/faltas), colação de grau, regime de dependência, atendimento domiciliar e organização didática dos cursos.
DUVIDA_RESOLUCAO: Perguntas sobre normas gerais, políticas institucionais e funcionamento de conselhos/comitês superiores. Caracteriza-se por temas como: regulamentos de comitês (Ética no Uso de Animais, Colegiados, NDE, CEPE), políticas de internacionalização, diretrizes de extensão (curricularização), gestão de riscos e governança institucional.
DUVIDA_PORTARIA: Perguntas sobre atos administrativos específicos, temporários ou de gestão de pessoas. Caracteriza-se por temas como: designação de servidores para comissões (inventário, Neabi), substituições de chefia, autorização de oferta de cursos específicos em campi, licenças de servidores, retificação de gratificações e nomeações de membros.
SAUDACAO_OU_OUTROS: Entradas que contenham apenas cumprimentos (Oi, bom dia), agradecimentos ou perguntas fora do escopo normativo/administrativo do IFES.

Exemplos (Few-Shot):
Pergunta: "Qual o prazo para eu pedir aproveitamento de uma disciplina que já fiz?"
Saída: {"intencao": "DUVIDA_ROD", "entidades": {"assunto": "aproveitamento de estudos"}}

Pergunta: "O que o Núcleo Docente Estruturante (NDE) faz exatamente?"
Saída: {"intencao": "DUVIDA_RESOLUCAO", "entidades": {"orgao": "NDE", "assunto": "atribuições"}}

Pergunta: "Quem são os membros da comissão de inventário do Campus São Mateus?"
Saída: {"intencao": "DUVIDA_PORTARIA", "entidades": {"comissao": "inventário", "campus": "São Mateus"}}

Pergunta: "O professor André Romero foi autorizado a atuar em qual campus?"
Saída: {"intencao": "DUVIDA_PORTARIA", "entidades": {"servidor": "André Romero", "assunto": "mobilidade docente"}}

Pergunta: "Olá CatBot, tudo bem?"
Saída: {"intencao": "SAUDACAO_OU_OUTROS", "entidades": {}}

Regras de Saída (JSON Estrito):
- Retorne APENAS o objeto JSON.
- NUNCA inclua explicações, introduções ou conclusões.
- NUNCA use blocos de código Markdown.
- Use a seguinte estrutura: {"intencao": "NOME_DA_INTENCAO", "entidades": {"chave": "valor"}}
Se não houver entidades claras, o objeto "entidades" deve ser {}.
"""


class HybridNLPProcessor(NLPProcessor):
    def __init__(self, spacy_processor: SpacyNLPProcessor, llm_client: LLMClient):
        self._spacy = spacy_processor
        self._llm = llm_client

    async def process(self, texto: str) -> NLPResult:
        # 1. Processamento rápido pelo SpaCy (Tokenização e NER Genérico)
        spacy_result = await self._spacy.process(texto)

        # 2. Avaliação de Intenção pelo LLM
        prompt_final = f"{PROMPT_SISTEMA_INTENCAO}\n\nPergunta: \"{texto}\"\nSaída:"
        resposta_llm = await self._llm.generate(prompt=prompt_final)

        texto_resposta = resposta_llm.texto.strip()
        intencao = "SAUDACAO_OU_OUTROS"
        entidades_llm = {}

        try:
            # Proteção contra formatação markdown indesejada do LLM
            if texto_resposta.startswith("```"):
                texto_resposta = re.sub(r"```(json)?", "", texto_resposta).strip()

            dados_extraidos = json.loads(texto_resposta)
            intencao = dados_extraidos.get("intencao", intencao)
            entidades_llm = dados_extraidos.get("entidades", {})

        except json.JSONDecodeError:
            print(f"Erro ao parsear JSON retornado pelo LLM: {texto_resposta}")

        # 3. Mesclar as entidades (As do modelo SpaCy com as de negócio do LLM)
        entidades_combinadas = {**spacy_result.entidades, **entidades_llm}

        return NLPResult(
            texto_normalizado=spacy_result.texto_normalizado,
            tokens=spacy_result.tokens,
            intencao=intencao,
            entidades=entidades_combinadas
        )