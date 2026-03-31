from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from catbot.adapters.outbound.persistence.sqlalchemy.models import ConversaModel, MensagemModel, RespostaModel
from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem, StatusValidacao, TipoRemetente
from catbot.domain.entities.resposta import Resposta
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

def _to_entity(row: ConversaModel) -> Conversa:
    return Conversa(id=row.id, usuario_id=row.usuario_id, status_sucesso=row.status_sucesso, iniciado_em=row.iniciado_em)

def _msg_to_entity(row: MensagemModel) -> Mensagem:
    return Mensagem(id=row.id, conversa_id=row.conversa_id, conteudo=row.conteudo, tipo_remetente=TipoRemetente(row.tipo_remetente), status_validacao=StatusValidacao(row.status_validacao), criado_em=row.criado_em)