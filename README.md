# CatBot Backend

Backend do CatBot com arquitetura hexagonal, FastAPI, PostgreSQL/pgvector e OpenAI.

## Execução Recomendada

O fluxo real do RAG usa PostgreSQL com pgvector. O Docker Compose sobe apenas o banco;
a API roda localmente para usar sua `OPENAI_API_KEY` no `.env`.

```bash
cp .env.example .env
docker compose up -d db
.venv\Scripts\activate
pip install -e ".[dev,nlp]"
alembic upgrade head
uvicorn catbot.main:app --reload
```

A API fica em `http://localhost:8000` e a documentação em
`http://localhost:8000/docs`.

## Variáveis de Ambiente

```env
REPOSITORY_TYPE=sqlalchemy
DATABASE_URL=postgresql+asyncpg://catbot:catbot@localhost:5433/catbot

LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sua-chave
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

Ollama permanece como adapter legado. Para usá-lo manualmente, configure
`LLM_PROVIDER=ollama`, `EMBEDDING_PROVIDER=ollama`, `LLM_BASE_URL` e os modelos
compatíveis.

## RAG e Documentos

Documentos são processados pelo `KnowledgeBaseService`:

1. extrai texto de `conteudo` bruto, TXT/MD/CSV ou PDF;
2. divide o texto em chunks com `CHUNK_SIZE` e `CHUNK_OVERLAP`;
3. gera embeddings com OpenAI;
4. salva os chunks em `chunk_documento.embedding` para busca via pgvector;
5. consulta chunks similares e filtra por categoria no fluxo do chat.

Embeddings antigos do Ollama não devem ser misturados com embeddings OpenAI. Após
migrar uma base existente, reindexe os documentos já cadastrados:

```bash
curl -X POST http://localhost:8000/api/v1/documentos/reindexar
```

Para reindexar um documento específico:

```bash
curl -X POST "http://localhost:8000/api/v1/documentos/reindexar?documento_id=<uuid>"
```

Esse processo apaga apenas chunks antigos e os reconstrói a partir das versões em
`versao_documento`; os registros de `documento` são preservados.

## Migrações

```bash
alembic upgrade head
alembic revision --autogenerate -m "descricao"
```

## Testes

```bash
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m compileall -q src tests
.venv\Scripts\python.exe -m ruff check src tests
```
