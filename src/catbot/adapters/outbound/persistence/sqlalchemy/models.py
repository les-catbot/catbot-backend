"""SQLAlchemy ORM models -- mapeamento do esquema do banco.

Estes modelos são separados das entidades de domínio propositalmente.
A conversão entre ORM model <-> domain entity será feita nos repositórios.
"""

import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UsuarioModel(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column(unique=True)
    senha_hash: Mapped[str] = mapped_column()
    perfil_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("perfil.id"), nullable=True)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PerfilModel(Base):
    __tablename__ = "perfil"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column()
    descricao: Mapped[str] = mapped_column(Text, default="")


class ConversaModel(Base):
    __tablename__ = "conversa"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    status_sucesso: Mapped[bool] = mapped_column(Boolean, default=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    iniciado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    encerrado_em: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MensagemModel(Base):
    __tablename__ = "mensagem"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversa_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversa.id"))
    status_validacao: Mapped[str] = mapped_column(default="pendente")
    tipo_remetente: Mapped[str] = mapped_column()
    conteudo: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessamentoPerguntaModel(Base):
    __tablename__ = "processamento_pergunta"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    mensagem_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("mensagem.id"))
    texto_normalizado: Mapped[str] = mapped_column(Text)
    tokens: Mapped[str] = mapped_column(Text)
    intencao_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("intencao.id"), nullable=True
    )
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IntencaoModel(Base):
    __tablename__ = "intencao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column()
    descricao: Mapped[str] = mapped_column(Text, default="")


class EntidadeExtraidaModel(Base):
    __tablename__ = "entidade_extraida"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    processamento_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("processamento_pergunta.id")
    )
    nome_entidade: Mapped[str] = mapped_column()
    valor_entidade: Mapped[str] = mapped_column()


class RespostaModel(Base):
    __tablename__ = "resposta"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    mensagem_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("mensagem.id"))
    texto_resposta: Mapped[str] = mapped_column(Text)
    pontuacao_confianca: Mapped[float] = mapped_column(Float, default=0.0)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentoModel(Base):
    __tablename__ = "documento"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    titulo: Mapped[str] = mapped_column()
    categoria: Mapped[str] = mapped_column()
    fonte: Mapped[str] = mapped_column()
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VersaoDocumentoModel(Base):
    __tablename__ = "versao_documento"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    documento_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("documento.id"))
    numero_versao: Mapped[int] = mapped_column(Integer)
    conteudo: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FonteRespostaModel(Base):
    __tablename__ = "fonte_resposta"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resposta_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("resposta.id"))
    documento_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("documento.id"))
    trecho: Mapped[str] = mapped_column(Text)


class AvaliacaoModel(Base):
    __tablename__ = "avaliacao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    mensagem_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("mensagem.id"))
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    nota: Mapped[int] = mapped_column(Integer)
    comentario: Mapped[str] = mapped_column(Text, default="")
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LogAdminModel(Base):
    __tablename__ = "log_admin"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id"))
    acao: Mapped[str] = mapped_column()
    descricao: Mapped[str] = mapped_column(Text, default="")
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
