from abc import ABC, abstractmethod
from uuid import UUID

from catbot.domain.entities.documento import Documento, VersaoDocumento


class DocumentoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, documento_id: UUID) -> Documento | None: ...

    @abstractmethod
    async def save(self, documento: Documento) -> Documento: ...

    @abstractmethod
    async def list_all(self) -> list[Documento]: ...

    @abstractmethod
    async def delete(self, documento_id: UUID) -> None: ...

    @abstractmethod
    async def add_versao(self, versao: VersaoDocumento) -> VersaoDocumento: ...

    @abstractmethod
    async def get_versoes(self, documento_id: UUID) -> list[VersaoDocumento]: ...
