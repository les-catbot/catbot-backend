"""Rotas de gerenciamento de documentos da base de conhecimento."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from catbot.adapters.inbound.api.dependencies import get_knowledge_base_service
from catbot.adapters.inbound.api.schemas.documento import (
    BuscaSemanticaRequest,
    ChunkResponse,
    DocumentoDetalheResponse,
    DocumentoResponse,
    IndexacaoResponse,
    VersaoDocumentoResponse,
)
from catbot.application.services.knowledge_base_service import (
    IndexingError,
    KnowledgeBaseService,
)

router = APIRouter(prefix="/documentos", tags=["documentos"])


@router.post("/", response_model=IndexacaoResponse, status_code=status.HTTP_201_CREATED)
async def cadastrar_documento(
    titulo: str = Form(...),
    categoria: str = Form(...),
    fonte: str = Form(...),
    conteudo: str | None = Form(None),
    arquivo: UploadFile | None = File(None),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    """Upload a document (file or raw text) for indexing."""
    if not conteudo and not arquivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça 'conteudo' (texto) ou 'arquivo' (upload).",
        )

    arquivo_bytes: bytes | None = None
    arquivo_nome: str | None = None
    if arquivo:
        arquivo_bytes = await arquivo.read()
        arquivo_nome = arquivo.filename

    try:
        doc = await service.cadastrar_documento(
            titulo=titulo,
            categoria=categoria,
            fonte=fonte,
            conteudo=conteudo,
            arquivo_bytes=arquivo_bytes,
            arquivo_nome=arquivo_nome,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IndexingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        )

    chunks = await service._vector.get_by_documento(doc.id)

    return IndexacaoResponse(
        mensagem="Documento cadastrado e indexado com sucesso.",
        documento=DocumentoResponse(
            id=doc.id,
            titulo=doc.titulo,
            categoria=doc.categoria,
            fonte=doc.fonte,
            criado_em=doc.criado_em,
        ),
        total_chunks=len(chunks),
    )


@router.get("/", response_model=list[DocumentoResponse])
async def listar_documentos(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    return await service.listar_documentos()


@router.get("/{documento_id}", response_model=DocumentoDetalheResponse)
async def obter_documento(
    documento_id: UUID,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    doc = await service.obter_documento(documento_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")
    chunks = await service._vector.get_by_documento(documento_id)
    return DocumentoDetalheResponse(
        id=doc.id,
        titulo=doc.titulo,
        categoria=doc.categoria,
        fonte=doc.fonte,
        criado_em=doc.criado_em,
        total_chunks=len(chunks),
    )


@router.put("/{documento_id}", response_model=IndexacaoResponse)
async def atualizar_documento(
    documento_id: UUID,
    conteudo: str | None = Form(None),
    arquivo: UploadFile | None = File(None),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    """Update document content and re-index."""
    if not conteudo and not arquivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça 'conteudo' (texto) ou 'arquivo' (upload).",
        )

    arquivo_bytes: bytes | None = None
    arquivo_nome: str | None = None
    if arquivo:
        arquivo_bytes = await arquivo.read()
        arquivo_nome = arquivo.filename

    try:
        versao = await service.atualizar_documento(
            documento_id=documento_id,
            conteudo=conteudo,
            arquivo_bytes=arquivo_bytes,
            arquivo_nome=arquivo_nome,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IndexingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        )

    doc = await service.obter_documento(documento_id)
    chunks = await service._vector.get_by_documento(documento_id)

    return IndexacaoResponse(
        mensagem=f"Documento atualizado para versão {versao.numero_versao} e re-indexado.",
        documento=DocumentoResponse(
            id=doc.id,
            titulo=doc.titulo,
            categoria=doc.categoria,
            fonte=doc.fonte,
            criado_em=doc.criado_em,
        ),
        total_chunks=len(chunks),
    )


@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_documento(
    documento_id: UUID,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    doc = await service.obter_documento(documento_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")
    await service.deletar_documento(documento_id)


@router.post("/busca", response_model=list[ChunkResponse])
async def busca_semantica(
    body: BuscaSemanticaRequest,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
):
    """Semantic search across the knowledge base."""
    try:
        chunks = await service.buscar_similar(body.query, top_k=body.top_k)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha na busca semântica: {exc}",
        )

    return [
        ChunkResponse(
            id=c.id,
            documento_id=c.documento_id,
            conteudo=c.conteudo,
            indice_chunk=c.indice_chunk,
            categoria=c.categoria,
            fonte=c.fonte,
        )
        for c in chunks
    ]
