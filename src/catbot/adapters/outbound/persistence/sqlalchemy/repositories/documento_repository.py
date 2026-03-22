from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from catbot.adapters.outbound.persistence.sqlalchemy.models import (
    DocumentoModel,
    VersaoDocumentoModel,
)
from catbot.domain.entities.documento import Documento, VersaoDocumento
from catbot.domain.ports.documento_repository import DocumentoRepository


class SQLAlchemyDocumentoRepository(DocumentoRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_by_id(self, documento_id: UUID) -> Documento | None:
        async with self._sf() as session:
            row = await session.get(DocumentoModel, documento_id)
            return _to_entity(row) if row else None

    async def save(self, documento: Documento) -> Documento:
        async with self._sf() as session:
            row = DocumentoModel(
                id=documento.id,
                titulo=documento.titulo,
                categoria=documento.categoria,
                fonte=documento.fonte,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_entity(row)

    async def list_all(self) -> list[Documento]:
        async with self._sf() as session:
            result = await session.execute(select(DocumentoModel))
            return [_to_entity(r) for r in result.scalars().all()]

    async def delete(self, documento_id: UUID) -> None:
        async with self._sf() as session:
            await session.execute(
                delete(VersaoDocumentoModel).where(
                    VersaoDocumentoModel.documento_id == documento_id
                )
            )
            await session.execute(
                delete(DocumentoModel).where(DocumentoModel.id == documento_id)
            )
            await session.commit()

    async def add_versao(self, versao: VersaoDocumento) -> VersaoDocumento:
        async with self._sf() as session:
            row = VersaoDocumentoModel(
                id=versao.id,
                documento_id=versao.documento_id,
                numero_versao=versao.numero_versao,
                conteudo=versao.conteudo,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _versao_to_entity(row)

    async def get_versoes(self, documento_id: UUID) -> list[VersaoDocumento]:
        async with self._sf() as session:
            result = await session.execute(
                select(VersaoDocumentoModel)
                .where(VersaoDocumentoModel.documento_id == documento_id)
                .order_by(VersaoDocumentoModel.numero_versao)
            )
            return [_versao_to_entity(r) for r in result.scalars().all()]


def _to_entity(row: DocumentoModel) -> Documento:
    return Documento(
        id=row.id,
        titulo=row.titulo,
        categoria=row.categoria,
        fonte=row.fonte,
        criado_em=row.criado_em,
    )


def _versao_to_entity(row: VersaoDocumentoModel) -> VersaoDocumento:
    return VersaoDocumento(
        id=row.id,
        documento_id=row.documento_id,
        numero_versao=row.numero_versao,
        conteudo=row.conteudo,
        criado_em=row.criado_em,
    )
