"""Testes para o serviço de base de conhecimento com pipeline de indexação."""

import pytest

from catbot.adapters.outbound.embedding.stub_embedding import StubEmbeddingService
from catbot.adapters.outbound.persistence.in_memory import (
    InMemoryDocumentoRepository,
    InMemoryVectorRepository,
)
from catbot.application.services.knowledge_base_service import (
    IndexingError,
    KnowledgeBaseService,
)
from catbot.domain.ports.embedding_service import EmbeddingService


@pytest.fixture
def doc_repo():
    return InMemoryDocumentoRepository()


@pytest.fixture
def embedding_service():
    return StubEmbeddingService()


@pytest.fixture
def vector_repo():
    return InMemoryVectorRepository()


@pytest.fixture
def service(doc_repo, embedding_service, vector_repo):
    return KnowledgeBaseService(
        documento_repo=doc_repo,
        embedding_service=embedding_service,
        vector_repo=vector_repo,
        chunk_size=100,
        chunk_overlap=20,
    )


class TestCadastrarDocumento:
    async def test_sucesso_com_texto(self, service, vector_repo):
        doc = await service.cadastrar_documento(
            titulo="Manual do Gato",
            categoria="Saúde",
            fonte="veterinario.com",
            conteudo="Os gatos precisam de cuidados especiais. " * 20,
        )
        assert doc.titulo == "Manual do Gato"
        assert doc.categoria == "Saúde"

        chunks = await vector_repo.get_by_documento(doc.id)
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.documento_id == doc.id
            assert chunk.categoria == "Saúde"
            assert chunk.fonte == "veterinario.com"
            assert len(chunk.embedding) > 0

    async def test_sucesso_com_arquivo_txt(self, service, vector_repo):
        content = ("Conteúdo do arquivo texto sobre gatos. " * 15).encode("utf-8")
        doc = await service.cadastrar_documento(
            titulo="Arquivo TXT",
            categoria="Educação",
            fonte="escola.com",
            arquivo_bytes=content,
            arquivo_nome="aula.txt",
        )
        chunks = await vector_repo.get_by_documento(doc.id)
        assert len(chunks) > 0

    async def test_conteudo_vazio_falha(self, service):
        with pytest.raises(ValueError, match="vazio"):
            await service.cadastrar_documento(
                titulo="Vazio",
                categoria="Teste",
                fonte="teste",
                conteudo="   ",
            )

    async def test_formato_nao_suportado(self, service):
        with pytest.raises(ValueError, match="não suportado"):
            await service.cadastrar_documento(
                titulo="Imagem",
                categoria="Teste",
                fonte="teste",
                arquivo_bytes=b"fake",
                arquivo_nome="foto.png",
            )


class TestAtualizarDocumento:
    async def test_atualizar_re_indexa(self, service, vector_repo):
        doc = await service.cadastrar_documento(
            titulo="Doc v1",
            categoria="Cat",
            fonte="fonte",
            conteudo="Versão um do documento com conteúdo suficiente para gerar chunks. " * 10,
        )
        chunks_v1 = await vector_repo.get_by_documento(doc.id)

        await service.atualizar_documento(
            documento_id=doc.id,
            conteudo="Versão dois completamente diferente com novo conteúdo para indexação. " * 10,
        )
        chunks_v2 = await vector_repo.get_by_documento(doc.id)

        assert len(chunks_v2) > 0
        v1_texts = {c.conteudo for c in chunks_v1}
        v2_texts = {c.conteudo for c in chunks_v2}
        assert v1_texts != v2_texts

    async def test_atualizar_documento_inexistente(self, service):
        from uuid import uuid4

        with pytest.raises(ValueError, match="não encontrado"):
            await service.atualizar_documento(
                documento_id=uuid4(), conteudo="algo"
            )


class TestDeletarDocumento:
    async def test_deleta_documento_e_chunks(self, service, doc_repo, vector_repo):
        doc = await service.cadastrar_documento(
            titulo="Para Deletar",
            categoria="Temp",
            fonte="temp",
            conteudo="Texto temporário que será removido junto com seus chunks. " * 10,
        )
        assert await vector_repo.get_by_documento(doc.id)

        await service.deletar_documento(doc.id)

        assert await doc_repo.get_by_id(doc.id) is None
        assert await vector_repo.get_by_documento(doc.id) == []


class TestBuscaSimilar:
    async def test_busca_retorna_resultados(self, service):
        await service.cadastrar_documento(
            titulo="Guia Felino",
            categoria="Saúde",
            fonte="vet.com",
            conteudo="Gatos precisam de vacinação anual e cuidados com a alimentação. " * 10,
        )
        results = await service.buscar_similar("vacinação de gatos", top_k=3)
        assert len(results) > 0


class TestReindexacao:
    async def test_reindexar_reconstroi_chunks_sem_apagar_documento(
        self,
        service,
        doc_repo,
        vector_repo,
    ):
        doc = await service.cadastrar_documento(
            titulo="Norma",
            categoria="ROD",
            fonte="ifes.edu.br",
            conteudo="Texto normativo com conteúdo suficiente para gerar chunks. " * 10,
        )
        await vector_repo.delete_by_documento(doc.id)

        resultado = await service.reindexar_documentos()
        chunks = await vector_repo.get_by_documento(doc.id)

        assert resultado.total_documentos == 1
        assert resultado.total_chunks == len(chunks)
        assert chunks
        assert await doc_repo.get_by_id(doc.id) is not None

    async def test_reindexar_documento_inexistente_falha(self, service):
        from uuid import uuid4

        with pytest.raises(ValueError, match="não encontrado"):
            await service.reindexar_documentos(documento_id=uuid4())


class TestRollbackOnFailure:
    async def test_rollback_quando_embedding_falha(self, doc_repo, vector_repo):
        class FailingEmbedding(EmbeddingService):
            async def generate_embeddings(self, texts):
                raise ConnectionError("API offline")

            def dimension(self):
                return 384

        service = KnowledgeBaseService(
            documento_repo=doc_repo,
            embedding_service=FailingEmbedding(),
            vector_repo=vector_repo,
        )

        with pytest.raises(IndexingError, match="Falha ao indexar"):
            await service.cadastrar_documento(
                titulo="Vai Falhar",
                categoria="Erro",
                fonte="teste",
                conteudo="Conteúdo que falhará na geração de embeddings. " * 10,
            )

        docs = await doc_repo.list_all()
        assert len(docs) == 0, "Documento deveria ter sido removido no rollback"
        assert await vector_repo.get_by_documento(docs[0].id) == [] if docs else True
