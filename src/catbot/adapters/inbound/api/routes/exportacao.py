"""Rotas para exportação de dados e relatórios."""

from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response

from catbot.adapters.inbound.api.dependencies import get_export_service
from catbot.application.services.export_service import ExportService

router = APIRouter(prefix="/exportacao", tags=["exportacao"])

@router.get(
    "/conversa/{conversa_id}/txt",
    response_class=PlainTextResponse,
    summary="Exportar Histórico em TXT"
)
async def exportar_conversa_txt(
    conversa_id: UUID,
    service: ExportService = Depends(get_export_service)
):
    """Retorna um arquivo .txt contendo a conversa completa e origens dos dados."""
    texto = await service.exportar_conversa_texto(conversa_id)
    return PlainTextResponse(
        content=texto,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=relatorio_conversa_{conversa_id}.txt"}
    )

@router.get(
    "/conversa/{conversa_id}/pdf",
    summary="Exportar Histórico em Relatório PDF"
)
async def exportar_conversa_pdf(
    conversa_id: UUID,
    service: ExportService = Depends(get_export_service)
):
    """Retorna um arquivo PDF formatado contendo as perguntas, respostas e justificativas."""
    pdf_bytes = await service.exportar_conversa_pdf(conversa_id)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_conversa_{conversa_id}.pdf"}
    )