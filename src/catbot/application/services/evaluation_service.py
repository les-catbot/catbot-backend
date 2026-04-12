"""Caso de uso: Avaliar Qualidade das Respostas."""

from uuid import UUID

from catbot.domain.entities.avaliacao import Avaliacao
from catbot.domain.ports.avaliacao_repository import AvaliacaoRepository


class EvaluationService:
    def __init__(self, avaliacao_repo: AvaliacaoRepository) -> None:
        self._repo = avaliacao_repo

    async def avaliar(
        self,
        mensagem_id: UUID,
        usuario_id: UUID,
        nota: int,
        comentario: str = "",
    ) -> Avaliacao:
        if not (1 <= nota <= 5):
            raise ValueError("Nota deve ser entre 1 e 5.")

        avaliacao = Avaliacao(
            mensagem_id=mensagem_id,
            usuario_id=usuario_id,
            nota=nota,
            comentario=comentario,
        )
        return await self._repo.save(avaliacao)

    async def buscar_por_mensagem(self, mensagem_id: UUID) -> list[Avaliacao]:
        return await self._repo.get_by_mensagem(mensagem_id)

    async def listar_avaliacoes(self) -> list[Avaliacao]:
        return await self._repo.list_all()
