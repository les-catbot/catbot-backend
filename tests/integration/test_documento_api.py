"""Testes de integração para os endpoints de documento."""

import pytest
from httpx import AsyncClient


class TestDocumentoEndpoints:
    async def test_cadastrar_documento_texto(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/documentos/",
            data={
                "titulo": "Manual do Gato",
                "categoria": "Saúde",
                "fonte": "veterinario.com",
                "conteudo": "Os gatos precisam de cuidados especiais com alimentação. " * 15,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["mensagem"] == "Documento cadastrado e indexado com sucesso."
        assert body["total_chunks"] > 0
        assert body["documento"]["titulo"] == "Manual do Gato"

    async def test_cadastrar_documento_arquivo_txt(self, client: AsyncClient):
        content = ("Texto do arquivo sobre felinos. " * 20).encode("utf-8")
        response = await client.post(
            "/api/v1/documentos/",
            data={
                "titulo": "Upload TXT",
                "categoria": "Educação",
                "fonte": "escola.com",
            },
            files={"arquivo": ("documento.txt", content, "text/plain")},
        )
        assert response.status_code == 201
        assert response.json()["total_chunks"] > 0

    async def test_cadastrar_sem_conteudo_falha(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/documentos/",
            data={
                "titulo": "Vazio",
                "categoria": "Teste",
                "fonte": "teste",
            },
        )
        assert response.status_code == 400

    async def test_listar_documentos(self, client: AsyncClient):
        await client.post(
            "/api/v1/documentos/",
            data={
                "titulo": "Doc 1",
                "categoria": "A",
                "fonte": "f",
                "conteudo": "Conteúdo suficiente para gerar pelo menos um chunk de texto. " * 10,
            },
        )
        response = await client.get("/api/v1/documentos/")
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) >= 1

    async def test_obter_documento(self, client: AsyncClient):
        create = await client.post(
            "/api/v1/documentos/",
            data={
                "titulo": "Detalhe",
                "categoria": "B",
                "fonte": "g",
                "conteudo": "Documento para consulta de detalhe com conteúdo extenso. " * 10,
            },
        )
        doc_id = create.json()["documento"]["id"]

        response = await client.get(f"/api/v1/documentos/{doc_id}")
        assert response.status_code == 200
        assert response.json()["total_chunks"] > 0

    async def test_deletar_documento(self, client: AsyncClient):
        create = await client.post(
            "/api/v1/documentos/",
            data={
                "titulo": "Para Deletar",
                "categoria": "C",
                "fonte": "h",
                "conteudo": "Documento temporário que será removido do sistema. " * 10,
            },
        )
        doc_id = create.json()["documento"]["id"]

        response = await client.delete(f"/api/v1/documentos/{doc_id}")
        assert response.status_code == 204

        response = await client.get(f"/api/v1/documentos/{doc_id}")
        assert response.status_code == 404

    async def test_busca_semantica(self, client: AsyncClient):
        await client.post(
            "/api/v1/documentos/",
            data={
                "titulo": "Vacinação",
                "categoria": "Saúde",
                "fonte": "vet.com",
                "conteudo": "Gatos devem ser vacinados anualmente contra raiva e outras doenças. " * 10,
            },
        )
        response = await client.post(
            "/api/v1/documentos/busca",
            json={"query": "vacina gato", "top_k": 3},
        )
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        assert "conteudo" in results[0]

    async def test_atualizar_documento(self, client: AsyncClient):
        create = await client.post(
            "/api/v1/documentos/",
            data={
                "titulo": "Para Atualizar",
                "categoria": "D",
                "fonte": "i",
                "conteudo": "Versão original do documento com informações iniciais. " * 10,
            },
        )
        doc_id = create.json()["documento"]["id"]

        response = await client.put(
            f"/api/v1/documentos/{doc_id}",
            data={
                "conteudo": "Versão atualizada com novas informações sobre o assunto. " * 10,
            },
        )
        assert response.status_code == 200
        assert "versão 2" in response.json()["mensagem"]
