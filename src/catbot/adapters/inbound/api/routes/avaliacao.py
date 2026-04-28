from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from catbot.adapters.inbound.api.dependencies import get_evaluation_service
from catbot.adapters.inbound.api.schemas.avaliacao import (
    AvaliacaoListResponse,
    AvaliacaoRequest,
    AvaliacaoResponse,
)
from catbot.application.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])


@router.post("", response_model=AvaliacaoResponse, status_code=201)
async def criar_avaliacao(
    body: AvaliacaoRequest,
    service: EvaluationService = Depends(get_evaluation_service),
) -> AvaliacaoResponse:
    try:
        avaliacao = await service.avaliar(
            mensagem_id=body.mensagem_id,
            usuario_id=body.usuario_id,
            nota=body.nota,
            comentario=body.comentario,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return AvaliacaoResponse(
        id=avaliacao.id,
        mensagem_id=avaliacao.mensagem_id,
        usuario_id=avaliacao.usuario_id,
        nota=avaliacao.nota,
        comentario=avaliacao.comentario,
        criado_em=avaliacao.criado_em,
    )


@router.get("/mensagem/{mensagem_id}", response_model=AvaliacaoListResponse)
async def listar_avaliacoes_por_mensagem(
    mensagem_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service),
) -> AvaliacaoListResponse:
    avaliacoes = await service.buscar_por_mensagem(mensagem_id)
    return AvaliacaoListResponse(
        avaliacoes=[
            AvaliacaoResponse(
                id=a.id,
                mensagem_id=a.mensagem_id,
                usuario_id=a.usuario_id,
                nota=a.nota,
                comentario=a.comentario,
                criado_em=a.criado_em,
            )
            for a in avaliacoes
        ],
        total=len(avaliacoes),
    )


@router.get("", response_model=AvaliacaoListResponse)
async def listar_avaliacoes(
    service: EvaluationService = Depends(get_evaluation_service),
) -> AvaliacaoListResponse:
    avaliacoes = await service.listar_avaliacoes()
    return AvaliacaoListResponse(
        avaliacoes=[
            AvaliacaoResponse(
                id=a.id,
                mensagem_id=a.mensagem_id,
                usuario_id=a.usuario_id,
                nota=a.nota,
                comentario=a.comentario,
                criado_em=a.criado_em,
            )
            for a in avaliacoes
        ],
        total=len(avaliacoes),
    )
