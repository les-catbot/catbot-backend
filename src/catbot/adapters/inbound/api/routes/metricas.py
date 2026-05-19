"""Rotas administrativas de métricas de uso."""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Optional

# Crie a injeção em dependencies.py
from catbot.adapters.inbound.api.dependencies import get_metrics_service
from catbot.application.services.metrics_service import MetricsService

router = APIRouter(prefix="/admin/metricas", tags=["admin_metricas"])

@router.get(
    "/dashboard",
    summary="Obter Relatório de Desempenho do Chatbot"
)
async def obter_dashboard(
    inicio: Optional[datetime] = None,
    fim: Optional[datetime] = None,
    service: MetricsService = Depends(get_metrics_service)
):
    """
    Retorna métricas de uso: total de perguntas, taxa de sucesso e reformulação.
    Exclusivo para perfil ADMINISTRADOR.
    """
    return await service.gerar_relatorio_desempenho(inicio, fim)