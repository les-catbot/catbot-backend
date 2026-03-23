from catbot.domain.ports.usuario_repository import UsuarioRepository
from catbot.application.security import verificar_senha, criar_token_acesso


class AuthService:
    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    async def autenticar(self, email: str, senha: str) -> str | None:
        # 1. Busca o usuário pelo e-mail
        usuario = await self._usuario_repo.get_by_email(email)
        if not usuario:
            return None  # Usuário não existe

        # 2. Verifica se a senha bate com o hash
        if not verificar_senha(senha, usuario.senha_hash):
            return None  # Senha incorreta

        # 3. Gera o token de acesso com dados úteis do usuário (Payload)
        token_data = {
            "sub": str(usuario.id),  # Subject (quem é o dono do token)
            "email": usuario.email,
            "perfil_id": str(usuario.perfil_id)
        }

        return criar_token_acesso(token_data)