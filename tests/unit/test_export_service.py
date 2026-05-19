from uuid import uuid4

import pytest

from catbot.adapters.outbound.persistence.in_memory import (
    InMemoryConversaRepository,
    InMemoryDocumentoRepository,
)
from catbot.application.services.export_service import ExportService
from catbot.application.services.history_service import HistoryService
from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.documento import Documento
from catbot.domain.entities.mensagem import Mensagem, StatusValidacao, TipoRemetente
from catbot.domain.entities.resposta import FonteResposta, Resposta


@pytest.mark.asyncio
async def test_exportacao_texto_mostra_pergunta_resposta_e_fonte_sem_ids() -> None:
    repo = InMemoryConversaRepository()
    documento_repo = InMemoryDocumentoRepository()
    history_service = HistoryService(conversa_repo=repo)
    export_service = ExportService(
        history_service=history_service,
        conversa_repo=repo,
        documento_repo=documento_repo,
    )

    conversa = await repo.save(Conversa(usuario_id=uuid4()))
    documento = await documento_repo.save(
        Documento(
            titulo="Regulamento de Matrícula",
            categoria="portaria",
            fonte="Base institucional",
        )
    )
    await repo.add_mensagem(
        Mensagem(
            conversa_id=conversa.id,
            conteudo="Qual o prazo?",
            tipo_remetente=TipoRemetente.USUARIO,
            status_validacao=StatusValidacao.VALIDA,
        )
    )
    resposta_msg = await repo.add_mensagem(
        Mensagem(
            conversa_id=conversa.id,
            conteudo="O prazo e de 30 dias.",
            tipo_remetente=TipoRemetente.BOT,
            status_validacao=StatusValidacao.VALIDA,
        )
    )
    resposta = await repo.save_resposta(
        Resposta(
            mensagem_id=resposta_msg.id,
            texto_resposta=resposta_msg.conteudo,
            pontuacao_confianca=0.9,
        )
    )
    await repo.add_fonte_resposta(
        FonteResposta(
            resposta_id=resposta.id,
            documento_id=documento.id,
            trecho="Trecho do documento que embasa a resposta.",
        )
    )

    texto = await export_service.exportar_conversa_texto(conversa.id)

    assert "Pergunta:" in texto
    assert "Resposta:" in texto
    assert "Fontes da resposta:" in texto
    assert "Regulamento de Matrícula" in texto
    assert "Trecho do documento" in texto
    assert str(conversa.id) not in texto
    assert str(documento.id) not in texto
    assert "Documento ID" not in texto


@pytest.mark.asyncio
async def test_exportacao_pdf_nao_expoe_ids_tecnicos() -> None:
    repo = InMemoryConversaRepository()
    documento_repo = InMemoryDocumentoRepository()
    history_service = HistoryService(conversa_repo=repo)
    export_service = ExportService(
        history_service=history_service,
        conversa_repo=repo,
        documento_repo=documento_repo,
    )

    conversa = await repo.save(Conversa(usuario_id=uuid4()))
    documento = await documento_repo.save(
        Documento(
            titulo="Portaria Acadêmica",
            categoria="portaria",
            fonte="Base institucional",
        )
    )
    await repo.add_mensagem(
        Mensagem(
            conversa_id=conversa.id,
            conteudo="Quais documentos preciso enviar?",
            tipo_remetente=TipoRemetente.USUARIO,
            status_validacao=StatusValidacao.VALIDA,
        )
    )
    resposta_msg = await repo.add_mensagem(
        Mensagem(
            conversa_id=conversa.id,
            conteudo="Você precisa enviar requerimento e comprovante.",
            tipo_remetente=TipoRemetente.BOT,
            status_validacao=StatusValidacao.VALIDA,
        )
    )
    resposta = await repo.save_resposta(
        Resposta(
            mensagem_id=resposta_msg.id,
            texto_resposta=resposta_msg.conteudo,
            pontuacao_confianca=0.9,
        )
    )
    await repo.add_fonte_resposta(
        FonteResposta(
            resposta_id=resposta.id,
            documento_id=documento.id,
            trecho="Trecho da portaria com a lista de documentos exigidos.",
        )
    )

    pdf = await export_service.exportar_conversa_pdf(conversa.id)

    assert pdf.startswith(b"%PDF")
    assert b"ID da Conversa" not in pdf
    assert b"Doc ID" not in pdf
