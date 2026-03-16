from uuid import UUID

from catbot.domain.entities.documento import Documento, VersaoDocumento
from catbot.domain.ports.documento_repository import DocumentoRepository


class InMemoryDocumentoRepository(DocumentoRepository):
    def __init__(self) -> None:
        self._documentos: dict[UUID, Documento] = {}
        self._versoes: dict[UUID, list[VersaoDocumento]] = {}

    async def get_by_id(self, documento_id: UUID) -> Documento | None:
        return self._documentos.get(documento_id)

    async def save(self, documento: Documento) -> Documento:
        self._documentos[documento.id] = documento
        if documento.id not in self._versoes:
            self._versoes[documento.id] = []
        return documento

    async def list_all(self) -> list[Documento]:
        return list(self._documentos.values())

    async def delete(self, documento_id: UUID) -> None:
        self._documentos.pop(documento_id, None)
        self._versoes.pop(documento_id, None)

    async def add_versao(self, versao: VersaoDocumento) -> VersaoDocumento:
        if versao.documento_id not in self._versoes:
            self._versoes[versao.documento_id] = []
        self._versoes[versao.documento_id].append(versao)
        return versao

    async def get_versoes(self, documento_id: UUID) -> list[VersaoDocumento]:
        return list(self._versoes.get(documento_id, []))
