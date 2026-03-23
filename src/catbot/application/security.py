import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from catbot.config import get_settings


def verificar_senha(senha_clara: str, senha_hash: str) -> bool:
    """Compara a senha em texto com o hash salvo no banco."""
    return bcrypt.checkpw(senha_clara.encode('utf-8'), senha_hash.encode('utf-8'))


def criar_token_acesso(dados: dict) -> str:
    """Gera um JWT assinado com a chave secreta da aplicação."""
    settings = get_settings()
    para_codificar = dados.copy()

    agora = datetime.now(timezone.utc)
    expiracao = agora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    para_codificar.update({"exp": expiracao, "iat": agora})

    token_codificado = jwt.encode(para_codificar, settings.SECRET_KEY, algorithm="HS256")
    return token_codificado