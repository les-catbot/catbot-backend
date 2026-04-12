"""Rotas de histórico de conversas."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from catbot.adapters.inbound.api.dependencies import get_history_service
from catbot.adapters.inbound.api.schemas.historico import (
    ConversaDetalheResponse,
    ConversaResponse,
    FiltroPeridoRequest,
    MensagemResponse,
)
from catbot.application.services.history_service import HistoryService

router = APIRouter(prefix="/historico", tags=["historico"])


@router.get(
    "/usuarios/{usuario_id}/conversas",
    response_model=list[ConversaResponse],
    summary="Listar conversas de um usuário",
    description="""
Retorna todas as conversas de um usuário, ordenadas da mais recente para a mais antiga.

### Como usar

1. Passe o `usuario_id` (UUID) na URL
2. A resposta é uma lista de conversas com `id`, `iniciado_em` e `status_sucesso`

### Fluxo típico

```
POST /chat/iniciar          → cria conversa (conversa_id)
POST /chat/perguntar        → envia perguntas (mensagens ficam salvas)
GET  /historico/usuarios/{id}/conversas  → lista todas as conversas depois
```

### Exemplo de resposta

```json
[
  {
    "id": "a1b2c3d4-...",
    "usuario_id": "u1u2u3u4-...",
    "status_sucesso": false,
    "iniciado_em": "2026-03-23T15:30:00Z",
    "encerrado_em": null
  }
]
```
""",
)
async def listar_conversas(
    usuario_id: UUID,
    service: HistoryService = Depends(get_history_service),
):
    conversas = await service.listar_conversas(usuario_id)
    conversas.sort(key=lambda c: c.iniciado_em, reverse=True)
    return conversas


@router.get(
    "/conversas/{conversa_id}",
    response_model=ConversaDetalheResponse,
    summary="Detalhar conversa com mensagens",
    description="""
Retorna uma conversa específica com **todas as suas mensagens** em ordem cronológica.

Cada mensagem inclui:
- `tipo_remetente`: `"usuario"` ou `"bot"`
- `conteudo`: texto da mensagem
- `criado_em`: timestamp

### Exemplo de resposta

```json
{
  "conversa": {
    "id": "a1b2c3d4-...",
    "usuario_id": "u1u2u3u4-...",
    "status_sucesso": false,
    "iniciado_em": "2026-03-23T15:30:00Z",
    "encerrado_em": null
  },
  "mensagens": [
    {
      "id": "m1m2m3m4-...",
      "conversa_id": "a1b2c3d4-...",
      "conteudo": "Qual o prazo para trancamento de matrícula?",
      "tipo_remetente": "usuario",
      "status_validacao": "valida",
      "criado_em": "2026-03-23T15:30:05Z"
    },
    {
      "id": "m5m6m7m8-...",
      "conversa_id": "a1b2c3d4-...",
      "conteudo": "De acordo com o ROD, o prazo para trancamento...",
      "tipo_remetente": "bot",
      "status_validacao": "valida",
      "criado_em": "2026-03-23T15:30:08Z"
    }
  ]
}
```
""",
)
async def detalhar_conversa(
    conversa_id: UUID,
    service: HistoryService = Depends(get_history_service),
):
    try:
        result = await service.detalhar_conversa(conversa_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return ConversaDetalheResponse(
        conversa=ConversaResponse(
            id=result.conversa.id,
            usuario_id=result.conversa.usuario_id,
            status_sucesso=result.conversa.status_sucesso,
            iniciado_em=result.conversa.iniciado_em,
            encerrado_em=result.conversa.encerrado_em,
        ),
        mensagens=[
            MensagemResponse(
                id=m.id,
                conversa_id=m.conversa_id,
                conteudo=m.conteudo,
                tipo_remetente=m.tipo_remetente,
                status_validacao=m.status_validacao,
                criado_em=m.criado_em,
            )
            for m in result.mensagens
        ],
    )


@router.post(
    "/usuarios/{usuario_id}/conversas/filtrar",
    response_model=list[ConversaResponse],
    summary="Filtrar conversas por período",
    description="""
Filtra conversas de um usuário dentro de um intervalo de datas.

### Body (JSON)

```json
{
  "inicio": "2026-03-01T00:00:00Z",
  "fim": "2026-03-31T23:59:59Z"
}
```

Retorna apenas as conversas cujo `iniciado_em` está entre `inicio` e `fim`.
Útil para relatórios e dashboards do administrador.
""",
)
async def filtrar_por_periodo(
    usuario_id: UUID,
    body: FiltroPeridoRequest,
    service: HistoryService = Depends(get_history_service),
):
    conversas = await service.filtrar_por_periodo(
        usuario_id=usuario_id,
        inicio=body.inicio,
        fim=body.fim,
    )
    conversas.sort(key=lambda c: c.iniciado_em, reverse=True)
    return conversas
