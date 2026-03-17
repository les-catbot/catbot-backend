from uuid import UUID
from catbot.domain.entities.usuario import Usuario
from catbot.domain.ports.usuario_repository import UsuarioRepository


class UserService:
    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._repo = usuario_repo

    async def criar(self, nome: str, email: str, senha_hash: str) -> Usuario:
        # Verifica se o email já existe
        existente = await self._repo.get_by_email(email)
        if existente:
            raise ValueError("Email já cadastrado.")

        novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
        return await self._repo.save(novo_usuario)

    async def listar(self) -> list[Usuario]:
        return await self._repo.list_all()

    async def obter(self, usuario_id: UUID) -> Usuario:
        usuario = await self._repo.get_by_id(usuario_id)
        if not usuario:
            raise ValueError("Utilizador não encontrado.")
        return usuario

    async def eliminar(self, usuario_id: UUID) -> None:
        await self._repo.delete(usuario_id)

    async def editar(self, usuario_id: UUID, nome: str = None, email: str = None) -> Usuario:
        usuario = await self.obter(usuario_id)
        if nome:
            usuario.nome = nome
        if email:
            usuario.email = email
        return await self._repo.save(usuario)