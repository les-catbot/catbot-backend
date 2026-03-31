# CatBot Backend

Backend do chatbot CatBot — arquitetura hexagonal (Ports & Adapters).

## Forma recomendada: Docker Compose

O Docker Compose sobe a aplicação junto com o PostgreSQL/pgvector e o Ollama.

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` conforme o modo desejado (veja a seção [Variáveis de ambiente](#variáveis-de-ambiente) abaixo).

### 2. Subir o stack

```bash
docker compose up --build
```

Na primeira execução o `ollama-pull` irá baixar os modelos `nomic-embed-text` e `llama3` automaticamente — isso pode demorar dependendo da sua conexão.

A API ficará disponível em `http://localhost:8000`. Documentação interativa (Swagger): `http://localhost:8000/docs`.

### 3. Rodar as migrações do banco de dados

As migrações **não rodam automaticamente** no startup. Após os containers estarem no ar, execute:

```bash
docker compose exec app alembic upgrade head
```

Isso cria todas as tabelas e insere os perfis padrão (`Administrador` e `Usuário Padrão`). **Este passo é obrigatório quando `REPOSITORY_TYPE=sqlalchemy`.**

Para gerar uma nova migration após alterar os models:

```bash
docker compose exec app alembic revision --autogenerate -m "Descrição"
```

---

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores. As principais variáveis que alteram o comportamento do sistema são:

### Modo de repositório (`REPOSITORY_TYPE`)

| Valor | Comportamento |
|---|---|
| `memory` (padrão) | Dados em memória, sem banco. Ideal para desenvolvimento rápido. Dados perdidos ao reiniciar. |
| `sqlalchemy` | PostgreSQL via pgvector. Requer banco no ar e migrations aplicadas. |

### Modo de embeddings e LLM (`EMBEDDING_TYPE`)

| Valor | Comportamento |
|---|---|
| `stub` (padrão) | Embeddings zerados, LLM retorna resposta fixa. Não requer Ollama. |
| `ollama` | Usa `nomic-embed-text` para embeddings e `llama3` para geração de texto via Ollama. |

### Configurações completas

| Variável | Descrição | Default |
|---|---|---|
| `REPOSITORY_TYPE` | `memory` ou `sqlalchemy` | `memory` |
| `DATABASE_URL` | Connection string PostgreSQL | `postgresql+asyncpg://catbot:catbot@localhost:5432/catbot` |
| `EMBEDDING_TYPE` | `stub` ou `ollama` | `stub` |
| `EMBEDDING_MODEL` | Modelo de embeddings do Ollama | `nomic-embed-text` |
| `LLM_BASE_URL` | URL do servidor Ollama | `http://ollama:11434` |
| `LLM_MODEL` | Modelo LLM do Ollama | `llama3` |
| `CHUNK_SIZE` | Tamanho dos chunks de texto (caracteres) | `500` |
| `CHUNK_OVERLAP` | Sobreposição entre chunks (caracteres) | `100` |
| `RAG_TOP_K` | Quantidade de chunks recuperados por busca semântica | `5` |
| `SECRET_KEY` | Chave para assinar JWT | `teste` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do token JWT (minutos) | `60` |

### Combinações típicas

**Desenvolvimento sem banco (padrão):**
```env
REPOSITORY_TYPE=memory
EMBEDDING_TYPE=stub
```

**Stack completo com Ollama:**
```env
REPOSITORY_TYPE=sqlalchemy
EMBEDDING_TYPE=ollama
DATABASE_URL=postgresql+asyncpg://catbot:catbot@db:5432/catbot
LLM_BASE_URL=http://ollama:11434
```

---

## Rodar sem Docker (não recomendado)

> **Aviso:** rodar fora do Docker requer que PostgreSQL e Ollama estejam instalados e configurados manualmente na sua máquina. Recomendamos o Docker Compose para evitar incompatibilidades de ambiente.

```bash
# Criar e ativar venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install -e ".[dev]"

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env apontando DATABASE_URL e LLM_BASE_URL para instâncias locais

# Aplicar migrations (se REPOSITORY_TYPE=sqlalchemy)
alembic upgrade head

# Rodar a API
uvicorn catbot.main:app --reload
```

---

## Testes

```bash
pytest                                      # todos os testes
pytest --cov=catbot                         # com cobertura
pytest tests/unit/test_chat_service.py      # arquivo específico
pytest -v                                   # verbose
```

Os testes usam `asyncio_mode = "auto"` — não é necessário o decorator `@pytest.mark.asyncio`.

## Linting e formatação

```bash
ruff check src/ tests/
ruff format src/ tests/
```
