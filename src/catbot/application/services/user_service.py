import bcrypt
from uuid import UUID
from catbot.domain.entities.usuario import Usuario
from catbot.domain.ports.usuario_repository import UsuarioRepository


# Você também precisará importar a porta do repositório de perfis, caso crie uma.

class UserService:
    def __init__(self, usuario_repo: UsuarioRepository, perfil_repo=None) -> None:
        self._repo = usuario_repo
        self._perfil_repo = perfil_repo

    def _gerar_hash(self, senha: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

    async def criar(self, dados: dict) -> Usuario:
        # Validação 1: E-mail único
        existente = await self._repo.get_by_email(dados['email'])
        if existente:
            raise ValueError("E-mail já cadastrado.")

        # Validação 2: Verificar se Perfil existe e guardá-lo numa variável
        perfil_encontrado = None
        if self._perfil_repo:
            perfil_encontrado = await self._perfil_repo.get_by_id(dados['perfil_id'])
            if not perfil_encontrado:
                raise ValueError("Perfil não encontrado.")

        senha_hash = self._gerar_hash(dados['senha'])

        novo_usuario = Usuario(
            nome=dados['nome'],
            email=dados['email'],
            senha_hash=senha_hash,
            perfil_id=dados['perfil_id'],
            perfil=perfil_encontrado  # <-- Injetamos o objeto completo aqui!
        )
        return await self._repo.save(novo_usuario)

    async def listar(self) -> list[Usuario]:
        return await self._repo.list_all()

    async def obter(self, usuario_id: UUID) -> Usuario:
        usuario = await self._repo.get_by_id(usuario_id)
        if not usuario:
            raise ValueError("Usuário não encontrado.")
        return usuario

    async def eliminar(self, usuario_id: UUID) -> None:
        await self._repo.delete(usuario_id)

    async def editar(self, usuario_id: UUID, dados: dict) -> Usuario:
        usuario = await self.obter(usuario_id)

        if 'email' in dados and dados['email'] != usuario.email:
            existente = await self._repo.get_by_email(dados['email'])
            if existente:
                raise ValueError("E-mail já cadastrado para outro usuário.")
            usuario.email = dados['email']

        if 'nome' in dados:
            usuario.nome = dados['nome']

        if 'perfil_id' in dados:
            # Validar existência do perfil_id caso necessário
            usuario.perfil_id = dados['perfil_id']

        if 'senha' in dados and dados['senha']:
            usuario.senha_hash = self._gerar_hash(dados['senha'])

        return await self._repo.save(usuario)