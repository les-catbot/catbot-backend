"""Caso de uso: Geração de Métricas e Desempenho do Chatbot."""

from datetime import datetime, timezone
from catbot.domain.ports.conversa_repository import ConversaRepository

class MetricsService:
    def __init__(self, conversa_repo: ConversaRepository) -> None:
        self._repo = conversa_repo

    async def gerar_relatorio_desempenho(self, inicio: datetime = None, fim: datetime = None) -> dict:
        """Agrega dados do banco para gerar métricas de uso."""
        conversas = await self._repo.list_all()

        if inicio and fim:
            # Garante que as datas vindas da API (Swagger) tenham fuso horário (UTC)
            if inicio.tzinfo is None:
                inicio = inicio.replace(tzinfo=timezone.utc)
            if fim.tzinfo is None:
                fim = fim.replace(tzinfo=timezone.utc)

            conversas_filtradas = []
            for c in conversas:
                # Garante que a data do banco também tenha fuso horário para comparação segura
                data_conversa = c.iniciado_em
                if data_conversa.tzinfo is None:
                    data_conversa = data_conversa.replace(tzinfo=timezone.utc)

                if inicio <= data_conversa <= fim:
                    conversas_filtradas.append(c)
            conversas = conversas_filtradas

        total_conversas = len(conversas)
        sucessos = len([c for c in conversas if c.status_sucesso])

        taxa_sucesso = (sucessos / total_conversas * 100) if total_conversas > 0 else 0.0

        # Coletar todas as mensagens (O ideal em produção é usar consultas SQL de agregação COUNT)
        todas_mensagens = []
        for c in conversas:
            mensagens = await self._repo.get_mensagens(c.id)
            todas_mensagens.extend(mensagens)

        # Pega a string 'usuario' direto do Enum ou da string
        total_perguntas = len([
            m for m in todas_mensagens
            if (hasattr(m.tipo_remetente, 'value') and m.tipo_remetente.value == "usuario")
            or m.tipo_remetente == "usuario"
        ])

        taxa_reformulacao = self._calcular_taxa_reformulacao(todas_mensagens, total_perguntas)

        return {
            "periodo": {"inicio": inicio, "fim": fim},
            "metricas": {
                "total_conversas": total_conversas,
                "total_perguntas_realizadas": total_perguntas,
                "taxa_sucesso_conversas": round(taxa_sucesso, 2),
                "taxa_reformulacao_estimada": round(taxa_reformulacao, 2)
            }
        }

    def _calcular_taxa_reformulacao(self, mensagens: list, total_perguntas: int) -> float:
        """Calcula taxa de reformulação identificando perguntas sequenciais do usuário."""
        if total_perguntas == 0: return 0.0

        reformulacoes = 0
        mensagens.sort(key=lambda m: m.criado_em)

        for i in range(1, len(mensagens)):
            remetente_atual = mensagens[i].tipo_remetente.value if hasattr(mensagens[i].tipo_remetente, 'value') else mensagens[i].tipo_remetente
            remetente_ant = mensagens[i-1].tipo_remetente.value if hasattr(mensagens[i-1].tipo_remetente, 'value') else mensagens[i-1].tipo_remetente

            if remetente_atual == "usuario" and remetente_ant == "usuario":
                # Se o usuário mandou duas msgs seguidas na mesma conversa, consideramos reformulação
                if mensagens[i].conversa_id == mensagens[i-1].conversa_id:
                    reformulacoes += 1

        return (reformulacoes / total_perguntas) * 100