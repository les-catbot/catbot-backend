import pytest
from uuid import uuid4

from catbot.adapters.outbound.persistence.in_memory import (
    InMemoryUsuarioRepository,
    InMemoryDocumentoRepository,
)
from catbot.domain.entities.usuario import Usuario
from catbot.domain.entities.documento import Documento, VersaoDocumento


@pytest.mark.asyncio
async def test_usuario_save_and_get():
    repo = InMemoryUsuarioRepository()
    user = Usuario(nome="Test", email="test@example.com", senha_hash="hash")
    await repo.save(user)

    found = await repo.get_by_id(user.id)
    assert found is not None
    assert found.email == "test@example.com"


@pytest.mark.asyncio
async def test_usuario_get_by_email():
    repo = InMemoryUsuarioRepository()
    user = Usuario(nome="Test", email="test@example.com", senha_hash="hash")
    await repo.save(user)

    found = await repo.get_by_email("test@example.com")
    assert found is not None
    assert found.id == user.id


@pytest.mark.asyncio
async def test_usuario_delete():
    repo = InMemoryUsuarioRepository()
    user = Usuario(nome="Test", email="test@example.com", senha_hash="hash")
    await repo.save(user)
    await repo.delete(user.id)

    assert await repo.get_by_id(user.id) is None


@pytest.mark.asyncio
async def test_documento_versoes():
    repo = InMemoryDocumentoRepository()
    doc = Documento(titulo="Regulamento", categoria="normas", fonte="site")
    await repo.save(doc)

    v1 = VersaoDocumento(documento_id=doc.id, numero_versao=1, conteudo="versão 1")
    v2 = VersaoDocumento(documento_id=doc.id, numero_versao=2, conteudo="versão 2")
    await repo.add_versao(v1)
    await repo.add_versao(v2)

    versoes = await repo.get_versoes(doc.id)
    assert len(versoes) == 2
    assert versoes[0].numero_versao == 1
    assert versoes[1].numero_versao == 2
