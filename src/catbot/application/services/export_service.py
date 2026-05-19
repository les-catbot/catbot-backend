"""Caso de uso: Exportar respostas e histórico de conversas."""

import html
from dataclasses import dataclass, field
from io import BytesIO, StringIO
from uuid import UUID

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from catbot.application.services.history_service import HistoryService
from catbot.domain.entities.mensagem import Mensagem, TipoRemetente
from catbot.domain.ports.conversa_repository import ConversaRepository
from catbot.domain.ports.documento_repository import DocumentoRepository


@dataclass
class FonteExportacao:
    titulo_documento: str | None
    trecho: str


@dataclass
class BlocoExportacao:
    pergunta: Mensagem | None = None
    resposta: Mensagem | None = None
    fontes: list[FonteExportacao] = field(default_factory=list)


class ExportService:
    def __init__(
        self,
        history_service: HistoryService,
        conversa_repo: ConversaRepository,
        documento_repo: DocumentoRepository | None = None,
    ) -> None:
        self._history_service = history_service
        self._conversa_repo = conversa_repo
        self._documento_repo = documento_repo

    async def exportar_conversa_texto(self, conversa_id: UUID) -> str:
        """Gera um relatório em texto simples (.txt)."""
        dados = await self._history_service.detalhar_conversa(conversa_id)
        blocos = await self._montar_blocos_exportacao(dados.mensagens)

        output = StringIO()
        output.write("=== RELATÓRIO DE CONVERSA ===\n")
        output.write(
            "Data de Início: "
            f"{dados.conversa.iniciado_em.strftime('%d/%m/%Y %H:%M:%S')}\n"
        )
        output.write("=" * 30 + "\n\n")

        for indice, bloco in enumerate(blocos, start=1):
            output.write(f"Atendimento {indice}\n")
            output.write("-" * 30 + "\n")

            if bloco.pergunta is not None:
                output.write("Pergunta:\n")
                output.write(f"{bloco.pergunta.conteudo}\n\n")

            if bloco.resposta is not None:
                output.write("Resposta:\n")
                output.write(f"{bloco.resposta.conteudo}\n")

            if bloco.fontes:
                output.write("\nFontes da resposta:\n")
                for fonte in bloco.fontes:
                    if fonte.titulo_documento:
                        output.write(f"- Documento: {fonte.titulo_documento}\n")
                    output.write(f"  Trecho: {_resumir_trecho(fonte.trecho, 220)}\n")

            output.write("\n")

        return output.getvalue()

    async def exportar_conversa_pdf(self, conversa_id: UUID) -> bytes:
        """Gera um relatório profissional em PDF contendo as justificativas e origens."""
        dados = await self._history_service.detalhar_conversa(conversa_id)
        blocos = await self._montar_blocos_exportacao(dados.mensagens)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=18,
        )
        styles = getSampleStyleSheet()
        story = []

        # Estilos customizados
        title_style = styles["Title"]
        normal_style = styles["Normal"]
        bold_style = ParagraphStyle(
            "Bold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
        )
        italic_style = ParagraphStyle(
            "Italic",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            textColor="#555555",
        )

        # Cabeçalho do Relatório
        story.append(Paragraph("Relatório de Atendimento - CatBot", title_style))
        story.append(Spacer(1, 12))
        story.append(
            Paragraph(
                "<b>Iniciado em:</b> "
                f"{dados.conversa.iniciado_em.strftime('%d/%m/%Y %H:%M:%S')}",
                normal_style,
            )
        )
        story.append(Spacer(1, 20))

        for indice, bloco in enumerate(blocos, start=1):
            story.append(Paragraph(f"<b>Atendimento {indice}</b>", bold_style))
            story.append(Spacer(1, 8))

            if bloco.pergunta is not None:
                pergunta = html.escape(bloco.pergunta.conteudo).replace("\n", "<br/>")
                story.append(Paragraph("<b>Pergunta</b>", bold_style))
                story.append(Paragraph(pergunta, normal_style))
                story.append(Spacer(1, 8))

            if bloco.resposta is not None:
                resposta = html.escape(bloco.resposta.conteudo).replace("\n", "<br/>")
                story.append(Paragraph("<b>Resposta</b>", bold_style))
                story.append(Paragraph(resposta, normal_style))

            if bloco.fontes:
                story.append(Spacer(1, 8))
                story.append(Paragraph("<b>Fontes da resposta</b>", italic_style))
                for fonte in bloco.fontes:
                    if fonte.titulo_documento:
                        titulo = html.escape(fonte.titulo_documento)
                        story.append(Paragraph(f"<b>Documento:</b> {titulo}", italic_style))
                    trecho = html.escape(_resumir_trecho(fonte.trecho, 280)).replace(
                        "\n", " "
                    )
                    story.append(Paragraph(f"<b>Trecho:</b> {trecho}", italic_style))

            story.append(Spacer(1, 15))

        # Construindo o PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    async def _montar_blocos_exportacao(
        self,
        mensagens: list[Mensagem],
    ) -> list[BlocoExportacao]:
        blocos: list[BlocoExportacao] = []
        bloco_atual: BlocoExportacao | None = None
        cache_documentos: dict[UUID, str | None] = {}

        for msg in mensagens:
            if _tipo_remetente(msg) == TipoRemetente.USUARIO.value:
                if bloco_atual is not None:
                    blocos.append(bloco_atual)
                bloco_atual = BlocoExportacao(pergunta=msg)
                continue

            if bloco_atual is None:
                bloco_atual = BlocoExportacao()

            bloco_atual.resposta = msg
            bloco_atual.fontes = await self._carregar_fontes(msg.id, cache_documentos)
            blocos.append(bloco_atual)
            bloco_atual = None

        if bloco_atual is not None:
            blocos.append(bloco_atual)

        return blocos

    async def _carregar_fontes(
        self,
        mensagem_id: UUID,
        cache_documentos: dict[UUID, str | None],
    ) -> list[FonteExportacao]:
        if not hasattr(self._conversa_repo, "get_fontes_por_mensagem"):
            return []

        fontes = await self._conversa_repo.get_fontes_por_mensagem(mensagem_id)
        return [
            FonteExportacao(
                titulo_documento=await self._obter_titulo_documento(
                    fonte.documento_id,
                    cache_documentos,
                ),
                trecho=fonte.trecho,
            )
            for fonte in fontes
        ]

    async def _obter_titulo_documento(
        self,
        documento_id: UUID,
        cache_documentos: dict[UUID, str | None],
    ) -> str | None:
        if documento_id in cache_documentos:
            return cache_documentos[documento_id]

        if self._documento_repo is None:
            cache_documentos[documento_id] = None
            return None

        documento = await self._documento_repo.get_by_id(documento_id)
        titulo = documento.titulo if documento is not None else None
        cache_documentos[documento_id] = titulo
        return titulo


def _tipo_remetente(msg) -> str:
    return getattr(msg.tipo_remetente, "value", msg.tipo_remetente)


def _resumir_trecho(trecho: str, limite: int) -> str:
    trecho_limpo = " ".join(trecho.split())
    if len(trecho_limpo) <= limite:
        return trecho_limpo
    return trecho_limpo[: limite - 3].rstrip() + "..."
