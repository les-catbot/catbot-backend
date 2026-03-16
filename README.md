# CatBot Backend

Backend do chatbot CatBot.

## Setup local

```bash
# Criar e ativar venv
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac

# Instalar dependências
pip install -e ".[dev]"

# Copiar variáveis de ambiente
cp .env.example .env

# Rodar a API (usa repositório in-memory por padrão)
uvicorn catbot.main:app --reload

# Rodar testes
pytest
```

## Docker

```bash
docker compose up --build
```

## Variáveis de ambiente

| Variável | Descrição | Default |
|---|---|---|
| `REPOSITORY_TYPE` | `memory` ou `sqlalchemy` | `memory` |
| `DATABASE_URL` | Connection string PostgreSQL | `postgresql+asyncpg://catbot:catbot@localhost:5432/catbot` |
| `LLM_BASE_URL` | URL do servidor LLM | `http://localhost:11434` |
| `LLM_MODEL` | Modelo LLM | `llama3` |
