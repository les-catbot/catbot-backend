"""Caso de uso: Gerenciar Base de Conhecimento."""

from uuid import UUID

from catbot.domain.entities.documento import Documento, VersaoDocumento
from catbot.domain.ports.documento_repository import DocumentoRepository


class KnowledgeBaseService:
    def __init__(self, documento_repo: DocumentoRepository) -> None:
        self._repo = documento_repo

    async def cadastrar_documento(
        self,
        titulo: str,
        categoria: str,
        fonte: str,
        conteudo: str,
    ) -> Documento:
        doc = Documento(titulo=titulo, categoria=categoria, fonte=fonte)
        doc = await self._repo.save(doc)

        versao = VersaoDocumento(
            documento_id=doc.id,
            numero_versao=1,
            conteudo=conteudo,
        )
        await self._repo.add_versao(versao)
        return doc

    async def atualizar_documento(
        self,
        documento_id: UUID,
        conteudo: str,
    ) -> VersaoDocumento:
        doc = await self._repo.get_by_id(documento_id)
        if doc is None:
            raise ValueError("Documento não encontrado.")

        versoes = await self._repo.get_versoes(documento_id)
        nova_versao = VersaoDocumento(
            documento_id=documento_id,
            numero_versao=len(versoes) + 1,
            conteudo=conteudo,
        )
        return await self._repo.add_versao(nova_versao)

    async def listar_documentos(self) -> list[Documento]:
        return await self._repo.list_all()
