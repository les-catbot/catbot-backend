from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from catbot.adapters.outbound.persistence.sqlalchemy.models import (
    ConversaModel,
    MensagemModel,
    RespostaModel,
    FonteRespostaModel
)
from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem, StatusValidacao, TipoRemetente
from catbot.domain.entities.resposta import Resposta, FonteResposta
from catbot.domain.ports.conversa_repository import ConversaRepository

class SQLAlchemyConversaRepository(ConversaRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_by_id(self, conversa_id: UUID) -> Conversa | None:
        async with self._sf() as session:
            row = await session.get(ConversaModel, conversa_id)
            return _to_entity(row) if row else None

    async def save(self, conversa: Conversa) -> Conversa:
        async with self._sf() as session:
            row = ConversaModel(id=conversa.id, usuario_id=conversa.usuario_id, status_sucesso=conversa.status_sucesso)
            await session.merge(row)
            await session.commit()
            return conversa

    async def list_by_usuario(self, usuario_id: UUID) -> list[Conversa]:
        async with self._sf() as session:
            result = await session.execute(select(ConversaModel).where(ConversaModel.usuario_id == usuario_id))
            return [_to_entity(r) for r in result.scalars().all()]

    async def add_mensagem(self, mensagem: Mensagem) -> Mensagem:
        async with self._sf() as session:
            row = MensagemModel(
                id=mensagem.id,
                conversa_id=mensagem.conversa_id,
                conteudo=mensagem.conteudo,
                tipo_remetente=mensagem.tipo_remetente.value,
                status_validacao=mensagem.status_validacao.value
            )
            session.add(row)
            await session.commit()
            return mensagem

    async def get_mensagens(self, conversa_id: UUID) -> list[Mensagem]:
        async with self._sf() as session:
            result = await session.execute(select(MensagemModel).where(MensagemModel.conversa_id == conversa_id).order_by(MensagemModel.criado_em))
            return [_msg_to_entity(r) for r in result.scalars().all()]

    async def save_resposta(self, resposta: Resposta) -> Resposta:
        async with self._sf() as session:
            row = RespostaModel(
                id=resposta.id,
                mensagem_id=resposta.mensagem_id,
                texto_resposta=resposta.texto_resposta,
                pontuacao_confianca=resposta.pontuacao_confianca
            )
            session.add(row)
            await session.commit()
            return resposta

    async def add_fonte_resposta(self, fonte: FonteResposta) -> FonteResposta:
        db_fonte = FonteRespostaModel(
            id=fonte.id,
            resposta_id=fonte.resposta_id,
            documento_id=fonte.documento_id,
            trecho=fonte.trecho
        )
        # CORREÇÃO AQUI: Abrindo a sessão corretamente
        async with self._sf() as session:
            session.add(db_fonte)
            await session.commit()
            return fonte

    async def get_fontes_por_mensagem(self, mensagem_id: UUID) -> list[FonteResposta]:
        # CORREÇÃO AQUI: Abrindo a sessão corretamente
        async with self._sf() as session:
            # Primeiro, acha a Resposta baseada na mensagem_id
            query_resp = select(RespostaModel).where(RespostaModel.mensagem_id == mensagem_id)
            result_resp = await session.execute(query_resp)
            resposta_db = result_resp.scalar_one_or_none()

            if not resposta_db:
                return []

            # Busca as fontes vinculadas à resposta_id
            query_fontes = select(FonteRespostaModel).where(FonteRespostaModel.resposta_id == resposta_db.id)
            result_fontes = await session.execute(query_fontes)
            fontes_db = result_fontes.scalars().all()

            return [
                FonteResposta(
                    id=f.id,
                    resposta_id=f.resposta_id,
                    documento_id=f.documento_id,
                    trecho=f.trecho
                ) for f in fontes_db
            ]

    async def list_all(self) -> list[Conversa]:
        # CORREÇÃO AQUI: Abrindo a sessão corretamente
        async with self._sf() as session:
            query = select(ConversaModel)
            result = await session.execute(query)
            conversas_db = result.scalars().all()
            return [
                Conversa(
                    id=c.id,
                    usuario_id=c.usuario_id,
                    status_sucesso=c.status_sucesso,
                    iniciado_em=c.iniciado_em,
                    encerrado_em=c.encerrado_em
                ) for c in conversas_db
            ]

def _to_entity(row: ConversaModel) -> Conversa:
    return Conversa(id=row.id, usuario_id=row.usuario_id, status_sucesso=row.status_sucesso, iniciado_em=row.iniciado_em)

def _msg_to_entity(row: MensagemModel) -> Mensagem:
    return Mensagem(id=row.id, conversa_id=row.conversa_id, conteudo=row.conteudo, tipo_remetente=TipoRemetente(row.tipo_remetente), status_validacao=StatusValidacao(row.status_validacao), criado_em=row.criado_em)