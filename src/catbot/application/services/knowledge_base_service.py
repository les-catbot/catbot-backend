"""Caso de uso: Gerenciar Base de Conhecimento com indexação vetorial."""

import logging
from uuid import UUID

from catbot.application.text_processing import chunk_text, extract_text
from catbot.domain.entities.chunk_documento import ChunkDocumento
from catbot.domain.entities.documento import Documento, VersaoDocumento
from catbot.domain.ports.documento_repository import DocumentoRepository
from catbot.domain.ports.embedding_service import EmbeddingService
from catbot.domain.ports.vector_repository import VectorRepository

logger = logging.getLogger(__name__)


class IndexingError(Exception):
    """Raised when the indexing pipeline fails and the operation is rolled back."""


class KnowledgeBaseService:
    def __init__(
        self,
        documento_repo: DocumentoRepository,
        embedding_service: EmbeddingService,
        vector_repo: VectorRepository,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> None:
        self._repo = documento_repo
        self._embedding = embedding_service
        self._vector = vector_repo
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def cadastrar_documento(
        self,
        titulo: str,
        categoria: str,
        fonte: str,
        conteudo: str | None = None,
        arquivo_bytes: bytes | None = None,
        arquivo_nome: str | None = None,
    ) -> Documento:
        """Register a new document, index its content and store embeddings.

        If any step fails, all persisted data for this operation is rolled back
        so no orphan records remain.
        """
        text = extract_text(arquivo_bytes, arquivo_nome, conteudo)
        if not text.strip():
            raise ValueError("O conteúdo extraído está vazio.")

        doc = Documento(titulo=titulo, categoria=categoria, fonte=fonte)
        doc = await self._repo.save(doc)

        versao = VersaoDocumento(
            documento_id=doc.id,
            numero_versao=1,
            conteudo=text,
        )
        versao = await self._repo.add_versao(versao)

        try:
            await self._indexar_versao(doc, versao, categoria, fonte)
        except Exception as exc:
            logger.error("Falha na indexação do documento %s: %s", doc.id, exc)
            await self._rollback_documento(doc.id)
            raise IndexingError(
                f"Falha ao indexar documento '{titulo}': {exc}"
            ) from exc

        logger.info(
            "Documento '%s' (id=%s) cadastrado e indexado com sucesso.", titulo, doc.id
        )
        return doc

    async def atualizar_documento(
        self,
        documento_id: UUID,
        conteudo: str | None = None,
        arquivo_bytes: bytes | None = None,
        arquivo_nome: str | None = None,
    ) -> VersaoDocumento:
        """Create a new version of an existing document and re-index it."""
        doc = await self._repo.get_by_id(documento_id)
        if doc is None:
            raise ValueError("Documento não encontrado.")

        text = extract_text(arquivo_bytes, arquivo_nome, conteudo)
        if not text.strip():
            raise ValueError("O conteúdo extraído está vazio.")

        versoes = await self._repo.get_versoes(documento_id)
        nova_versao = VersaoDocumento(
            documento_id=documento_id,
            numero_versao=len(versoes) + 1,
            conteudo=text,
        )
        nova_versao = await self._repo.add_versao(nova_versao)

        try:
            await self._vector.delete_by_documento(documento_id)
            await self._indexar_versao(doc, nova_versao, doc.categoria, doc.fonte)
        except Exception as exc:
            logger.error(
                "Falha na re-indexação do documento %s: %s", documento_id, exc
            )
            await self._vector.delete_by_versao(nova_versao.id)
            raise IndexingError(
                f"Falha ao re-indexar documento {documento_id}: {exc}"
            ) from exc

        logger.info("Documento %s atualizado para versão %d.", documento_id, nova_versao.numero_versao)
        return nova_versao

    async def listar_documentos(self) -> list[Documento]:
        return await self._repo.list_all()

    async def obter_documento(self, documento_id: UUID) -> Documento | None:
        return await self._repo.get_by_id(documento_id)

    async def deletar_documento(self, documento_id: UUID) -> None:
        """Delete a document and all its associated chunks."""
        await self._vector.delete_by_documento(documento_id)
        await self._repo.delete(documento_id)
        logger.info("Documento %s removido.", documento_id)

    async def buscar_similar(self, query: str, categoria: str | None = None, top_k: int = 5) -> list[ChunkDocumento]:
        embeddings = await self._embedding.generate_embeddings([query])
        # Repassa a variável categoria para o vector repository
        return await self._vector.search_similar(embeddings[0], categoria=categoria, top_k=top_k)

    async def _indexar_versao(
        self,
        doc: Documento,
        versao: VersaoDocumento,
        categoria: str,
        fonte: str,
    ) -> None:
        chunks_text = chunk_text(
            versao.conteudo,
            chunk_size=self._chunk_size,
            overlap=self._chunk_overlap,
        )
        if not chunks_text:
            raise ValueError("Nenhum chunk gerado a partir do conteúdo.")

        embeddings = await self._embedding.generate_embeddings(chunks_text)

        chunk_entities = [
            ChunkDocumento(
                documento_id=doc.id,
                versao_id=versao.id,
                conteudo=text,
                indice_chunk=idx,
                embedding=emb,
                categoria=categoria,
                fonte=fonte,
            )
            for idx, (text, emb) in enumerate(zip(chunks_text, embeddings))
        ]

        await self._vector.save_chunks(chunk_entities)

    async def _rollback_documento(self, documento_id: UUID) -> None:
        """Best-effort cleanup: remove the document and any partial vectors."""
        try:
            await self._vector.delete_by_documento(documento_id)
        except Exception:
            logger.warning("Rollback de vetores falhou para doc %s", documento_id)
        try:
            await self._repo.delete(documento_id)
        except Exception:
            logger.warning("Rollback de documento falhou para doc %s", documento_id)
