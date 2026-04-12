"""Initial schema — baseline de todas as tabelas existentes.

Revision ID: 001
Revises: None
Create Date: 2026-03-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "perfil",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("descricao", sa.Text(), server_default=""),
    )

    op.create_table(
        "usuario",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("senha_hash", sa.String(), nullable=False),
        sa.Column("perfil_id", sa.Uuid(), sa.ForeignKey("perfil.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "intencao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("descricao", sa.Text(), server_default=""),
    )

    op.create_table(
        "conversa",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("status_sucesso", sa.Boolean(), server_default="false"),
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("encerrado_em", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "mensagem",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conversa_id", sa.Uuid(), sa.ForeignKey("conversa.id"), nullable=False),
        sa.Column("status_validacao", sa.String(), server_default="pendente"),
        sa.Column("tipo_remetente", sa.String(), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "processamento_pergunta",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("mensagem_id", sa.Uuid(), sa.ForeignKey("mensagem.id"), nullable=False),
        sa.Column("texto_normalizado", sa.Text(), nullable=False),
        sa.Column("tokens", sa.Text(), nullable=False),
        sa.Column("intencao_id", sa.Uuid(), sa.ForeignKey("intencao.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "entidade_extraida",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "processamento_id",
            sa.Uuid(),
            sa.ForeignKey("processamento_pergunta.id"),
            nullable=False,
        ),
        sa.Column("nome_entidade", sa.String(), nullable=False),
        sa.Column("valor_entidade", sa.String(), nullable=False),
    )

    op.create_table(
        "resposta",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("mensagem_id", sa.Uuid(), sa.ForeignKey("mensagem.id"), nullable=False),
        sa.Column("texto_resposta", sa.Text(), nullable=False),
        sa.Column("pontuacao_confianca", sa.Float(), server_default="0.0"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "documento",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("categoria", sa.String(), nullable=False),
        sa.Column("fonte", sa.String(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "versao_documento",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("documento_id", sa.Uuid(), sa.ForeignKey("documento.id"), nullable=False),
        sa.Column("numero_versao", sa.Integer(), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "fonte_resposta",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("resposta_id", sa.Uuid(), sa.ForeignKey("resposta.id"), nullable=False),
        sa.Column("documento_id", sa.Uuid(), sa.ForeignKey("documento.id"), nullable=False),
        sa.Column("trecho", sa.Text(), nullable=False),
    )

    op.create_table(
        "avaliacao",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("mensagem_id", sa.Uuid(), sa.ForeignKey("mensagem.id"), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("nota", sa.Integer(), nullable=False),
        sa.Column("comentario", sa.Text(), server_default=""),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "log_admin",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("usuario_id", sa.Uuid(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("acao", sa.String(), nullable=False),
        sa.Column("descricao", sa.Text(), server_default=""),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chunk_documento",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("documento_id", sa.Uuid(), sa.ForeignKey("documento.id"), nullable=False),
        sa.Column("versao_id", sa.Uuid(), sa.ForeignKey("versao_documento.id"), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("indice_chunk", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector()),
        sa.Column("categoria", sa.String(), server_default=""),
        sa.Column("fonte", sa.String(), server_default=""),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.execute("""
        INSERT INTO perfil (id, nome, descricao) VALUES
        ('00000000-0000-0000-0000-000000000001', 'Administrador', 'Acesso total ao sistema'),
        ('00000000-0000-0000-0000-000000000002', 'Usuário Padrão', 'Acesso comum')
    """)


def downgrade() -> None:
    op.drop_table("chunk_documento")
    op.drop_table("log_admin")
    op.drop_table("avaliacao")
    op.drop_table("fonte_resposta")
    op.drop_table("versao_documento")
    op.drop_table("documento")
    op.drop_table("resposta")
    op.drop_table("entidade_extraida")
    op.drop_table("processamento_pergunta")
    op.drop_table("mensagem")
    op.drop_table("conversa")
    op.drop_table("intencao")
    op.drop_table("usuario")
    op.drop_table("perfil")
