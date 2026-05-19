"""Caso de uso: Gerenciar Base de Conhecimento com indexação vetorial."""

import logging
from dataclasses import dataclass
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


@dataclass
class ReindexacaoDocumento:
    documento_id: UUID
    versao_id: UUID
    total_chunks: int


@dataclass
class ReindexacaoResultado:
    total_documentos: int
    total_chunks: int
    documentos: list[ReindexacaoDocumento]


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

        logger.info(
            "Documento %s atualizado para versão %d.",
            documento_id,
            nova_versao.numero_versao,
        )
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

    async def buscar_similar(
        self,
        query: str,
        categoria: str | None = None,
        top_k: int = 5,
    ) -> list[ChunkDocumento]:
        embeddings = await self._embedding.generate_embeddings([query])
        if not embeddings:
            raise ValueError("Nenhum embedding gerado para a busca.")
        self._validar_dimensoes(embeddings)
        # Repassa a variável categoria para o vector repository
        return await self._vector.search_similar(embeddings[0], categoria=categoria, top_k=top_k)

    async def reindexar_documentos(
        self,
        documento_id: UUID | None = None,
    ) -> ReindexacaoResultado:
        """Rebuild stored vectors from the latest document versions."""
        if documento_id is not None:
            doc = await self._repo.get_by_id(documento_id)
            if doc is None:
                raise ValueError("Documento não encontrado.")
            documentos = [doc]
        else:
            documentos = await self._repo.list_all()

        reindexados: list[ReindexacaoDocumento] = []
        total_chunks = 0

        for doc in documentos:
            versoes = await self._repo.get_versoes(doc.id)
            if not versoes:
                logger.warning("Documento %s sem versões; reindexação ignorada.", doc.id)
                continue

            versao = max(versoes, key=lambda item: item.numero_versao)
            chunks = await self._gerar_chunks_indexados(
                doc=doc,
                versao=versao,
                categoria=doc.categoria,
                fonte=doc.fonte,
            )
            await self._vector.delete_by_documento(doc.id)
            await self._vector.save_chunks(chunks)

            reindexados.append(
                ReindexacaoDocumento(
                    documento_id=doc.id,
                    versao_id=versao.id,
                    total_chunks=len(chunks),
                )
            )
            total_chunks += len(chunks)

        return ReindexacaoResultado(
            total_documentos=len(reindexados),
            total_chunks=total_chunks,
            documentos=reindexados,
        )

    async def _indexar_versao(
        self,
        doc: Documento,
        versao: VersaoDocumento,
        categoria: str,
        fonte: str,
    ) -> None:
        chunk_entities = await self._gerar_chunks_indexados(
            doc=doc,
            versao=versao,
            categoria=categoria,
            fonte=fonte,
        )

        await self._vector.save_chunks(chunk_entities)

    async def _gerar_chunks_indexados(
        self,
        doc: Documento,
        versao: VersaoDocumento,
        categoria: str,
        fonte: str,
    ) -> list[ChunkDocumento]:
        chunks_text = chunk_text(
            versao.conteudo,
            chunk_size=self._chunk_size,
            overlap=self._chunk_overlap,
        )
        if not chunks_text:
            raise ValueError("Nenhum chunk gerado a partir do conteúdo.")

        embeddings = await self._embedding.generate_embeddings(chunks_text)
        self._validar_dimensoes(embeddings)
        if len(embeddings) != len(chunks_text):
            raise ValueError(
                "Quantidade de embeddings diferente da quantidade de chunks gerados."
            )

        return [
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

    def _validar_dimensoes(self, embeddings: list[list[float]]) -> None:
        expected_dimension = self._embedding.dimension()
        invalid = [
            len(embedding)
            for embedding in embeddings
            if len(embedding) != expected_dimension
        ]
        if invalid:
            raise ValueError(
                "Dimensão de embedding inválida: "
                f"esperado {expected_dimension}, recebido {invalid[0]}."
            )

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
