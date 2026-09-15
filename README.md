# CatBot Backend

Backend de um chatbot com RAG (Retrieval-Augmented Generation) construído em
**arquitetura hexagonal** (Ports & Adapters), permitindo trocar de provedor de
LLM/embeddings ou de banco de dados sem tocar na lógica de negócio.

## O problema que resolve
Responder perguntas com base numa base de documentos própria (não no
conhecimento genérico do modelo), sempre citando a fonte da resposta e um
grau de confiança — em vez de um chatbot que só "conversa" sem embasamento.

## Como funciona (fluxo de RAG)
1. Documentos (TXT/MD/CSV/PDF) são enviados e divididos em *chunks* configuráveis
   (`CHUNK_SIZE`, `CHUNK_OVERLAP`).
2. Cada chunk vira um embedding (OpenAI ou Ollama) e é salvo no PostgreSQL via
   **pgvector**.
3. Ao perguntar, o sistema busca os `RAG_TOP_K` chunks mais relevantes,
   filtra por categoria e monta o contexto para o LLM.
4. A resposta volta com as fontes utilizadas (`documento_id` + trecho) e uma
   pontuação de confiança — não é uma caixa-preta.
5. Documentos podem ser reindexados (individualmente ou em lote) sem apagar o
   histórico de versões.

## Arquitetura
```
adapters/inbound/api      → rotas FastAPI (chat, documentos, auth, avaliação,
                             histórico, exportação, métricas, health)
application/services      → regras de negócio (ChatService, KnowledgeBaseService,
                             AuthService, EvaluationService, ExportService...)
domain/ports               → interfaces (contratos) que a aplicação depende
domain/entities             → modelos de domínio puros, sem dependência de framework
adapters/outbound/*        → implementações reais das portas:
                             persistence (SQLAlchemy+pgvector, ou in-memory p/ testes)
                             llm (OpenAI, Ollama, ou stub p/ testes)
                             embedding (OpenAI, Ollama, ou stub p/ testes)
                             nlp (spaCy + heurísticas híbridas)
```
A regra de negócio nunca importa FastAPI, SQLAlchemy ou a SDK da OpenAI
diretamente — só as *ports* (interfaces) do domínio. Isso é o que permite
rodar os testes unitários inteiros com repositórios em memória e um LLM
"stub", sem precisar de banco nem de chave de API.

## Tecnologias
Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, PostgreSQL + pgvector,
Alembic, JWT (python-jose + PyJWT), spaCy, OpenAI SDK, Ollama (adapter legado),
Docker Compose, pytest + pytest-asyncio, ruff.

## Como rodar
```bash
cp .env.example .env          # preencha sua OPENAI_API_KEY
docker compose up -d db       # sobe só o Postgres/pgvector
pip install -e ".[dev,nlp]"
alembic upgrade head
uvicorn catbot.main:app --reload
```
API em `http://localhost:8000`, documentação interativa em `/docs`.

## Principais endpoints (`/api/v1`)
`POST /chat/iniciar` · `POST /chat/perguntar` · `POST /documentos` (upload) ·
`POST /documentos/reindexar` · `POST /avaliacoes` (feedback da resposta) ·
`GET /historico` · `GET /exportacao` (PDF da conversa) · `GET /metricas` ·
`POST /auth/login` · `GET /health`

## Decisões técnicas
- **Arquitetura hexagonal**: trocar OpenAI por Ollama, ou Postgres por
  repositórios em memória nos testes, é questão de configuração, não de
  reescrever código de negócio.
- **Stub adapters para LLM/embedding/NLP**: os testes unitários rodam em
  milissegundos, sem chamar API externa nem precisar de banco.
- **Reindexação sem perda de versão**: trocar de provedor de embedding não
  mistura vetores incompatíveis, e o histórico de versões do documento é
  preservado.

## Testes
42 funções de teste (unitários + integração), cobrindo services, adapters e
as rotas principais da API:
```bash
pytest -q
```

## Autoria
Projeto em equipe, desenvolvido por **Daniel Donateli** e **Victor Cordeiro**.
Minha atuação: autenticação (JWT), integração com a OpenAI, fluxo de
pergunta/resposta do chat e parte dos testes de integração.

## Próximos passos
CI no GitHub Actions rodando os testes automaticamente, cobertura de testes
publicada, e um cliente MCP para expor o chat como ferramenta de IA.
