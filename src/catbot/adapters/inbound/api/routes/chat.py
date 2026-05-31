"""Rotas do chat."""

from fastapi import APIRouter, Depends, HTTPException, status

from catbot.adapters.inbound.api.dependencies import get_chat_service
from catbot.adapters.inbound.api.schemas.chat import (
    EncerrarConversaRequest,
    EncerrarConversaResponse,
    FonteResponse,
    NovaConversaRequest,
    NovaConversaResponse,
    PerguntaRequest,
    PerguntaResponse,
)
from catbot.application.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/iniciar", response_model=NovaConversaResponse, status_code=status.HTTP_201_CREATED)
async def iniciar_conversa(
    body: NovaConversaRequest,
    service: ChatService = Depends(get_chat_service),
) -> NovaConversaResponse:
    conversa = await service.iniciar_conversa(usuario_id=body.usuario_id)
    return NovaConversaResponse(conversa_id=conversa.id)


@router.post(
    "/encerrar",
    response_model=EncerrarConversaResponse,
    summary="Encerrar uma conversa",
    description=(
        "Encerra manualmente uma conversa, registrando o `encerrado_em`. "
        "A operação é idempotente: encerrar uma conversa já encerrada devolve "
        "o timestamp original sem alterá-lo."
    ),
)
async def encerrar_conversa(
    body: EncerrarConversaRequest,
    service: ChatService = Depends(get_chat_service),
) -> EncerrarConversaResponse:
    try:
        conversa = await service.encerrar_conversa(conversa_id=body.conversa_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return EncerrarConversaResponse(
        conversa_id=conversa.id,
        encerrado_em=conversa.encerrado_em,
    )


@router.post("/perguntar", response_model=PerguntaResponse)
async def perguntar(
    body: PerguntaRequest,
    service: ChatService = Depends(get_chat_service),
) -> PerguntaResponse:
    try:
        result = await service.processar_pergunta(
            conversa_id=body.conversa_id,
            texto_usuario=body.texto,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )

    # Convertendo as entidades de domínio (FonteResposta) para schemas da API (FonteResponse)
    fontes_formatadas = [
        FonteResponse(documento_id=f.documento_id, trecho=f.trecho)
        for f in result.fontes
    ]

    return PerguntaResponse(
        resposta=result.resposta,
        confianca=result.confianca,
        mensagem_id=result.mensagem_id,
        fontes=fontes_formatadas
    )
