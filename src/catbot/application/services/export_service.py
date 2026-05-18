"""Caso de uso: Exportar respostas e histórico de conversas."""

import html
from io import BytesIO, StringIO
from uuid import UUID

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from catbot.application.services.history_service import HistoryService
from catbot.domain.ports.conversa_repository import ConversaRepository


class ExportService:
    def __init__(self, history_service: HistoryService, conversa_repo: ConversaRepository) -> None:
        self._history_service = history_service
        self._conversa_repo = conversa_repo

    async def exportar_conversa_texto(self, conversa_id: UUID) -> str:
        """Gera um relatório em texto simples (.txt)."""
        dados = await self._history_service.detalhar_conversa(conversa_id)

        output = StringIO()
        output.write(f"=== RELATÓRIO DE CONVERSA ===\n")
        output.write(f"ID Conversa: {dados.conversa.id}\n")
        output.write(f"Data de Início: {dados.conversa.iniciado_em.strftime('%d/%m/%Y %H:%M:%S')}\n")
        output.write("="*30 + "\n\n")

        for msg in dados.mensagens:
            remetente = "USUÁRIO" if msg.tipo_remetente == "usuario" else "CATBOT"
            output.write(f"[{msg.criado_em.strftime('%H:%M:%S')}] {remetente}:\n{msg.conteudo}\n")

            if msg.tipo_remetente == "bot" and hasattr(self._conversa_repo, 'get_fontes_por_mensagem'):
                fontes = await self._conversa_repo.get_fontes_por_mensagem(msg.id)
                if fontes:
                    output.write("\n  >> Fontes Utilizadas:\n")
                    for f in fontes:
                        output.write(f"  - Documento ID: {f.documento_id}\n")
                        output.write(f"  - Trecho: {f.trecho[:150]}...\n")
            output.write("\n" + "-"*30 + "\n")

        return output.getvalue()

    async def exportar_conversa_pdf(self, conversa_id: UUID) -> bytes:
        """Gera um relatório profissional em PDF contendo as justificativas e origens."""
        dados = await self._history_service.detalhar_conversa(conversa_id)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=18)
        styles = getSampleStyleSheet()
        story = []

        # Estilos customizados
        title_style = styles['Title']
        normal_style = styles['Normal']
        bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold')
        italic_style = ParagraphStyle('Italic', parent=styles['Normal'], fontName='Helvetica-Oblique', textColor="#555555")

        # Cabeçalho do Relatório
        story.append(Paragraph("Relatório de Atendimento - CatBot", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>ID da Conversa:</b> {dados.conversa.id}", normal_style))
        story.append(Paragraph(f"<b>Iniciado em:</b> {dados.conversa.iniciado_em.strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 20))

        # Iterando sobre as mensagens
        for msg in dados.mensagens:
            remetente = "USUÁRIO" if msg.tipo_remetente == "usuario" else "CATBOT (IA)"
            hora = msg.criado_em.strftime('%H:%M:%S')

            # Nome do remetente
            story.append(Paragraph(f"<b>[{hora}] {remetente}:</b>", bold_style))

            # Conteúdo da mensagem (escapando HTML para não quebrar o gerador do reportlab)
            conteudo_escaped = html.escape(msg.conteudo).replace('\n', '<br/>')
            story.append(Paragraph(conteudo_escaped, normal_style))

            # Adicionando as fontes (Rastreabilidade) para as mensagens do bot
            if msg.tipo_remetente == "bot" and hasattr(self._conversa_repo, 'get_fontes_por_mensagem'):
                fontes = await self._conversa_repo.get_fontes_por_mensagem(msg.id)
                if fontes:
                    story.append(Spacer(1, 6))
                    story.append(Paragraph("<i>  >> Origem da Informação (Base de Conhecimento):</i>", italic_style))
                    for f in fontes:
                        trecho_limpo = html.escape(f.trecho[:200]).replace('\n', ' ') + "..."
                        story.append(Paragraph(f"  - <b>Doc ID:</b> {f.documento_id}", italic_style))
                        story.append(Paragraph(f"  - <b>Trecho:</b> {trecho_limpo}", italic_style))

            story.append(Spacer(1, 15))

        # Construindo o PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes