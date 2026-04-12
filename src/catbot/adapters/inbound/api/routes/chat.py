from fastapi import APIRouter, Depends, HTTPException

from catbot.adapters.inbound.api.dependencies import get_chat_service
from catbot.adapters.inbound.api.schemas.chat import (
    PerguntaRequest,
    PerguntaResponse,
    NovaConversaRequest, # Nova importação
    NovaConversaResponse # Nova importação
)
from catbot.application.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

# NOVA ROTA PARA CRIAR O ID DA CONVERSA
@router.post("/iniciar", response_model=NovaConversaResponse)
async def iniciar_conversa(
    body: NovaConversaRequest,
    service: ChatService = Depends(get_chat_service),
) -> NovaConversaResponse:
    conversa = await service.iniciar_conversa(usuario_id=body.usuario_id)
    return NovaConversaResponse(conversa_id=conversa.id)


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
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return PerguntaResponse(
        resposta=result.resposta,
        confianca=result.confianca,
        mensagem_id=result.mensagem_id,
    )